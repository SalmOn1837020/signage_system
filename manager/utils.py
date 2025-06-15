# manager/utils.py
from django.utils import timezone
from datetime import timedelta, datetime, time as dt_time # Renamed to avoid conflict
from .models import Attraction # Relative import for utils.py in manager app

def get_theatrical_status(attraction: Attraction, current_dt: datetime = None):
    if not attraction.is_theater:
        return None

    if current_dt is None:
        current_dt = timezone.now()

    # Ensure current_dt is offset-aware, matching Django's DateTimeFields
    if timezone.is_naive(current_dt):
        # Fallback to default timezone if current_dt is naive
        current_dt = timezone.make_aware(current_dt, timezone.get_default_timezone())

    # Get all showtimes, ordered by start time
    all_showtimes = attraction.showtimes.all().order_by('start_datetime')

    if not all_showtimes.exists():
        return {'status_key': 'no_show_info', 'display_text': '公演情報なし'}

    # --- Check for active states (上演中, 開演間近) across all showtimes ---
    # These states take precedence
    for show in all_showtimes:
        start_dt = show.start_datetime
        end_dt = show.end_datetime

        # Ensure show times are aware for comparison (they should be from DB)
        # If current_dt has a timezone, and DB times are naive, make DB times aware.
        # If DB times are aware, use them directly. Django DateTimeFields are aware by default if USE_TZ=True.
        if timezone.is_naive(start_dt) and timezone.is_aware(current_dt):
             start_dt = timezone.make_aware(start_dt, current_dt.tzinfo)
        if timezone.is_naive(end_dt) and timezone.is_aware(current_dt):
             end_dt = timezone.make_aware(end_dt, current_dt.tzinfo)

        # 1. 上演中 (Showing)
        if start_dt <= current_dt <= end_dt:
            return {'status_key': 'showing', 'display_text': '上演中'}

        # 2. 開演間近 (Starting Soon) - for shows that haven't started yet
        if current_dt < start_dt and (start_dt - current_dt) <= timedelta(minutes=10):
            minutes_left = int((start_dt - current_dt).total_seconds() // 60)
            return {
                'status_key': 'starting_soon',
                'display_text': f'開演まであと{minutes_left}分',
                'minutes_to_show': minutes_left
            }

    # --- If no show is currently '上演中' or '開演間近', determine other states ---
    # Convert current_dt to local timezone for day-based comparisons
    current_local_dt = timezone.localtime(current_dt)
    today_date = current_local_dt.date()

    todays_shows_local = []
    for show in all_showtimes:
        if timezone.localtime(show.start_datetime).date() == today_date:
            todays_shows_local.append(show)

    # 3. 準備中 (Preparing)
    # "公演日の0:00から開演時間の10分より前の状態"
    # This applies to the *next upcoming show today* if it's >10 mins away.
    if todays_shows_local: # Only if there are shows scheduled for today
        for show in todays_shows_local: # Already ordered by start_datetime from all_showtimes
            start_dt = show.start_datetime # Aware datetime

            # Make sure start_dt is correctly compared with current_dt
            if timezone.is_naive(start_dt) and timezone.is_aware(current_dt):
                 start_dt = timezone.make_aware(start_dt, current_dt.tzinfo)

            if current_dt < start_dt and (start_dt - current_dt) > timedelta(minutes=10):
                # This show is later today and more than 10 mins away.
                # Check if current_dt is on the same calendar day as the show's start_datetime,
                # and after 00:00 of that day.
                show_day_start_local = timezone.make_aware(
                    datetime.combine(timezone.localtime(start_dt).date(), dt_time.min),
                    current_local_dt.tzinfo # Use local timezone for comparison
                )
                if current_local_dt >= show_day_start_local:
                    return {'status_key': 'preparing', 'display_text': '準備中'}
                # If not, this show is not the one defining "preparing" status now.
                # Continue to check other shows today or fall through.


    # 4. 終演 (Ended Today - all of today's shows are done)
    # "終演時間から、終演時間が設定されている日の23:59までの状態。"
    # This implies all shows scheduled for today have finished.
    if todays_shows_local: # If there were any shows today
        all_over_for_today = True
        latest_end_time_today = None
        for show in todays_shows_local:
            end_dt = show.end_datetime
            if timezone.is_naive(end_dt) and timezone.is_aware(current_dt):
                 end_dt = timezone.make_aware(end_dt, current_dt.tzinfo)

            if current_dt < end_dt: # This show is not over yet
                all_over_for_today = False
                break
            if latest_end_time_today is None or end_dt > latest_end_time_today:
                latest_end_time_today = end_dt

        if all_over_for_today:
            # Ensure current_dt is still within the same calendar day as the last show's end time (local).
            if latest_end_time_today and timezone.localtime(latest_end_time_today).date() == today_date:
                 # And current_dt is before 23:59:59 of that day
                end_of_today_local = timezone.make_aware(
                    datetime.combine(today_date, dt_time.max),
                    current_local_dt.tzinfo
                )
                if current_local_dt <= end_of_today_local : # current_dt is after last show end, but still today
                    return {'status_key': 'ended_today', 'display_text': '本日の公演は全て終了しました'}

    # --- Fallback states if no specific state for today is found (e.g., no shows today, or all shows far in future/past) ---

    # 5. 近日公演予定 (Upcoming) - if there are future shows (not today, not fitting above)
    # Check all showtimes again for any show that starts after current_dt
    future_shows_exist = False
    next_overall_show_start_dt = None
    for show in all_showtimes: # Already ordered
        start_dt = show.start_datetime
        if timezone.is_naive(start_dt) and timezone.is_aware(current_dt):
             start_dt = timezone.make_aware(start_dt, current_dt.tzinfo)

        if start_dt > current_dt:
            future_shows_exist = True
            next_overall_show_start_dt = start_dt
            break # Found the soonest future show

    if future_shows_exist:
        # If there were shows today but they didn't match any "preparing" or "ended_today" state,
        # and we are past them, but there's a show on a *future day*.
        # Or, if there were no shows today at all, but there are future shows.
        if not todays_shows_local or all_over_for_today: # (all_over_for_today implies todays_shows_local existed)
             return {
                'status_key': 'upcoming',
                'display_text': f"{timezone.localtime(next_overall_show_start_dt).strftime('%m月%d日 %H:%M')} 公演予定"
            }


    # 6. 全公演終了 (All shows ever scheduled are in the past and none of above matched)
    # This implies no future shows exist, and today's states didn't match.
    # It's safe to assume all shows are done if we reach here and future_shows_exist is False.
    if not future_shows_exist:
        return {'status_key': 'all_shows_ended', 'display_text': '全公演終了'}

    # Default fallback if somehow a state wasn't determined (should be rare)
    return {'status_key': 'unknown', 'display_text': '状態不明'}
