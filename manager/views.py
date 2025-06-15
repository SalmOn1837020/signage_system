# manager/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, Http404, JsonResponse
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.contrib.auth import login, logout, authenticate
from .forms import CustomUserCreationForm, CustomAuthenticationForm
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.contrib import messages
from django.core.paginator import Paginator
from django.conf import settings
from django.http import JsonResponse
import os
from django.db.models import F

from .models import Attraction, SystemLog, UserActivity, GachaTicket, Like, User, Tag
from .forms import CustomUserCreationForm

# --- 定数 ---
ABNORMAL_EXIT_LOG_DETAIL_TEMPLATE = "ユーザー'{username}'が'{current_attraction_name}'に入室したため、'{previous_attraction_name}'から強制退室させました。"

# --- 状態更新ロジック ---
def update_attraction_status(attraction):
    """出し物の人数に基づいて状態を更新する関数"""
    if attraction.is_theater or attraction.status == 'closed':
        # 演劇または閉店中の場合は、人数に応じたステータス変更は行わない
        return

    # 収容率を計算
    ratio = attraction.current_visitors / attraction.capacity if attraction.capacity > 0 else 0

    if ratio < 0.8:
        attraction.status = 'available' # 空き
    elif 0.8 <= ratio <= 1.1:
        attraction.status = 'normal' # 普通
    else:
        attraction.status = 'crowded' # 混雑
    
    attraction.save()


# --- QRコード一覧表示 ---
@login_required
def qr_code_list(request):
    # 管理者(staff)か出し物職員(staff)のみアクセス可能
    if not (request.user.is_staff or request.user.role == 'staff'):
        raise Http404 
    
    if request.user.is_staff:
        # 管理者の場合は、全ての出し物を取得
        attractions = Attraction.objects.all().order_by('attraction_name')
        page_title = "【管理者用】全出し物 QRコード一覧"
    else:
        # 出し物職員の場合は、自分が担当する出し物のみを取得
        attractions = request.user.managed_attractions.all().order_by('attraction_name')
        page_title = "【職員用】担当出し物 QRコード一覧"

    base_url = request.build_absolute_uri('/')
    context = {
        'attractions': attractions,
        'base_url': base_url,
        'page_title': page_title,
    }
    return render(request, 'manager/qr_code_list.html', context)



# --- 入室処理 ---
@login_required
@transaction.atomic
def process_entry(request, qr_id):
    # QRコードIDに対応する出し物を探す
    attraction = get_object_or_404(Attraction, entry_qr_id=qr_id)
    user = request.user

    # 閉店・上演中の場合は処理を中断
    if attraction.status in ['closed', 'showing']:
        messages.error(request, f"「{attraction.attraction_name}」は現在入室できません。")
        return redirect('manager:attraction_list')

    # 仕様: 別の出し物に入室中の場合の処理
    last_entry_attraction_id = request.session.get('last_entry_attraction_id')
    if last_entry_attraction_id and last_entry_attraction_id != attraction.id:
        try:
            # 前の出し物の人数を1人減らす
            last_attraction = Attraction.objects.get(id=last_entry_attraction_id)
            if last_attraction.current_visitors > 0:
                last_attraction.current_visitors -= 1
                update_attraction_status(last_attraction) # 状態も更新
                # ログを記録
                SystemLog.objects.create(
                    user=user, 
                    action="異常退室処理", 
                    details=ABNORMAL_EXIT_LOG_DETAIL_TEMPLATE.format(
                        username=user.username,
                        current_attraction_name=attraction.attraction_name,
                        previous_attraction_name=last_attraction.attraction_name
                    )
                )
        except Attraction.DoesNotExist:
            pass # 既に削除されたアトラクションの場合は何もしない

    # 現在の出し物の人数を1人増やし、累計来場者数も増やす
    attraction.current_visitors += 1
    attraction.total_visitors += 1
    update_attraction_status(attraction) # 状態を更新
    
    # ログを記録
    SystemLog.objects.create(
        user=user, 
        action="入室", 
        details=f"ユーザー'{user.username}'が'{attraction.attraction_name}'に入室しました。"
    )

    # 次の退室処理のために、どの出し物に入室したかをセッションに保存
    request.session['last_entry_attraction_id'] = attraction.id
    # ガチャ判定のため、異常処理でないことをマーク
    request.session['is_normal_entry'] = True 

    # ユーザー行動履歴を作成（入室時間を記録）
    UserActivity.objects.create(user=user, attraction=attraction)

    messages.success(request, f"「{attraction.attraction_name}」に入室しました。")
    return redirect('manager:attraction_list')

# --- 退室処理 ---
@login_required
@transaction.atomic
def process_exit(request, qr_id):
    attraction = get_object_or_404(Attraction, exit_qr_id=qr_id)
    user = request.user

    last_entry_attraction_id = request.session.get('last_entry_attraction_id')
    if last_entry_attraction_id != attraction.id:
        messages.error(request, "この出し物の入室記録がありません。")
        return redirect('manager:attraction_list')
    
    if attraction.current_visitors > 0:
        attraction.current_visitors -= 1
        update_attraction_status(attraction)

    SystemLog.objects.create(
        user=user, 
        action="退室", 
        details=f"ユーザー'{user.username}'が'{attraction.attraction_name}'から退室しました。"
    )

    # 最新の未退室の行動履歴を探す
    activity = UserActivity.objects.filter(
        user=user,
        attraction=attraction,
        exit_time__isnull=True
    ).order_by('-entry_time').first()

    if not activity:
        messages.error(request, "この出し物の有効な入室記録が見つかりません。")
        # Clear session variables that might lead to incorrect state
        request.session['last_entry_attraction_id'] = None
        request.session['is_normal_entry'] = False
        return redirect('manager:attraction_list')

    # 退室時間を記録し保存（duration_secondsはモデルのsave()で計算）
    activity.exit_time = timezone.now()
    activity.save()

    if request.session.get('is_normal_entry', False): # 'is_normal_entry'は入室時に設定される
        SystemLog.objects.create(
            user=user,
            action="アトラクション巡回完了",
            details=f"ユーザー'{user.username}'が'{attraction.attraction_name}'の巡回を完了しました。"
        )
            
        # チケット発行ロジック (ユニークな体験済み出し物数をカウント)
        completed_attraction_count = UserActivity.objects.filter(
            user=user,
            exit_time__isnull=False
        ).values('attraction').distinct().count()
            
        if completed_attraction_count > 0 and completed_attraction_count % 5 == 0:
            # TODO: Consider more robust logic to prevent re-issuing tickets for the same milestone if already issued.
            # For now, this matches the original spirit if completed_attraction_count is a new multiple of 5.
            new_ticket = GachaTicket.objects.create(user=user)
            SystemLog.objects.create(
                user=user,
                action="ガチャチケット獲得",
                details=f"ユーザー'{user.username}'が{completed_attraction_count}個のユニークな出し物を巡り、チケットを獲得しました。(Ticket ID: {new_ticket.id})"
            )
            messages.success(request, '🎉 ガチャチケットを1枚獲得しました！「マイチケット」から確認できます。')

    request.session['last_entry_attraction_id'] = None
    request.session['is_normal_entry'] = False
    
    messages.success(request, f"「{attraction.attraction_name}」から退室しました。")
    return redirect('manager:attraction_list')


# --- トップページ（混雑状況一覧） ---
def attraction_list(request):
    # GETパラメータから選択されたタグIDを取得
    selected_tag_id = request.GET.get('tag')
    
    attractions = Attraction.objects.all().order_by('attraction_name')
    
# ログインしている場合、体験済みのアトラクションIDのリストを取得
    if request.user.is_authenticated:
        visited_attraction_ids = UserActivity.objects.filter(user=request.user).values_list('attraction_id', flat=True)
    else:
        visited_attraction_ids = []

    # もしタグIDがURLパラメータにあれば、それで絞り込みを行う
    if selected_tag_id and selected_tag_id.isdigit():
        attractions = attractions.filter(tags__id=selected_tag_id)

    # データベースから全てのタグを取得する
    tags = Tag.objects.all()
    
    # context辞書に、attractionsと"tags"の両方を入れる
    context = {
        'attractions': attractions,
        'tags': tags, # テンプレートでタグ情報を使用するため、コンテキストに含めます。
        'selected_tag_id': int(selected_tag_id) if selected_tag_id and selected_tag_id.isdigit() else None,
        'visited_attraction_ids': visited_attraction_ids,
    }
    return render(request, 'manager/attraction_list.html', context)

# --- 出し物詳細ページ ---
def attraction_detail(request, attraction_id):
    attraction = get_object_or_404(Attraction, id=attraction_id)
    
    is_liked = False
    can_like = False
    hls_url = None # HLS動画のURL。存在しない場合はNoneのまま。

    # HLSプレイリストパスが設定されていれば、完全なURLを構築します。
    if attraction.hls_playlist:
        # os.path.joinを使い、OSに依存しない安全なパス結合を行う
        # MEDIA_URLと結合し、バックスラッシュをスラッシュに置換
        hls_url = os.path.join(settings.MEDIA_URL, attraction.hls_playlist).replace('\\', '/')

    if request.user.is_authenticated:
        is_liked = Like.objects.filter(user=request.user, attraction=attraction).exists()
        can_like = UserActivity.objects.filter(user=request.user, attraction=attraction, exit_time__isnull=False).exists()

    context = {
        'attraction': attraction,
        'is_liked': is_liked,
        'can_like': can_like,
        'hls_url': hls_url, # HLS URLをテンプレートに渡します。
    }
    return render(request, 'manager/attraction_detail.html', context)

# --- 高評価（いいね）処理 ---
@login_required
@require_POST
def like_attraction(request, attraction_id):
    attraction = get_object_or_404(Attraction, id=attraction_id)
    user = request.user
    
    # Ajaxリクエストかどうかを判定
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if not UserActivity.objects.filter(user=user, attraction=attraction, exit_time__isnull=False).exists():
        if is_ajax:
            return JsonResponse({'status': 'error', 'message': 'Not allowed. User must have visited and exited the attraction.'}, status=400)
        messages.error(request, "いいねするには、出し物を体験し退室した後に再度お試しください。")
        return redirect('manager:attraction_detail', attraction_id=attraction.id)

    like, created = Like.objects.get_or_create(user=user, attraction=attraction)

    if created:
        attraction.likes_count = F('likes_count') + 1
    else:
        like.delete()
        attraction.likes_count = F('likes_count') - 1
    
    attraction.save()
    attraction.refresh_from_db() # F()オブジェクトを使った後はDBから最新の値を取得

    # ログ記録
    action = "高評価" if created else "高評価取消"
    SystemLog.objects.create(user=user, action=action, details=f"'{user.username}'が'{attraction.attraction_name}'を操作しました。")
    
    if is_ajax:
        return JsonResponse({
            'status': 'ok',
            'is_liked': created,
            'likes_count': attraction.likes_count
        })

    return redirect('manager:attraction_detail', attraction_id=attraction.id)


# --- ユーザー登録 ---
def signup_view(request):
    if request.user.is_authenticated:
        return redirect('manager:attraction_list')
        
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            SystemLog.objects.create(user=user, action="新規登録", details=f"ユーザー'{user.username}'が登録しました。")
            messages.success(request, 'ユーザー登録が完了しました。作成したアカウントでログインしてください。')
            return redirect('manager:login')
        else:
            messages.error(request, '入力内容に誤りがあります。内容を確認して再度お試しください。')
    else:
        form = CustomUserCreationForm()
        
    return render(request, 'manager/signup.html', {'form': form})

# --- ログイン ---
def login_view(request):
    if request.user.is_authenticated:
        return redirect('manager:attraction_list')
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST) # こちらに変更
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                
                # ログイン後のリダイレクト先を決定
                next_url = request.GET.get('next')
                if next_url:
                    return redirect(next_url)
                
                if user.is_staff:
                    # 管理者 (admin)
                    return redirect('admin:index')
                elif user.role == 'signage':
                    # サイネージ用アカウント
                    return redirect('manager:signage')
                else:
                    return redirect('manager:attraction_list')
    else:
        form = CustomAuthenticationForm() # こちらに変更
    return render(request, 'manager/login.html', {'form': form})

# --- ログアウト ---
@login_required
def logout_view(request):
    logout(request)
    messages.success(request, "ログアウトしました。")
    return redirect('manager:attraction_list')


# --- ガチャチケット関連 ---
@login_required
def my_tickets(request):
    tickets = GachaTicket.objects.filter(user=request.user).order_by('-issued_at')
    context = {
        'tickets': tickets,
        'base_url': request.build_absolute_uri('/')
    }
    return render(request, 'manager/my_tickets.html', context)

@login_required
def gacha_scan_view(request):
    if not (request.user.role == 'gacha' or request.user.is_staff):
        raise Http404

    message = ''
    error_message = ''
    if request.method == 'POST':
        ticket_id = request.POST.get('ticket_id')
        try:
            ticket = GachaTicket.objects.get(id=ticket_id)
            if not ticket.is_used:
                ticket.is_used = True
                ticket.used_at = timezone.now()
                ticket.used_by = request.user
                ticket.save()
                message = f"チケットを正常に使用済みにしました。\n所有者: {ticket.user.username}\n発行日時: {ticket.issued_at.strftime('%Y-%m-%d %H:%M')}"
                SystemLog.objects.create(user=request.user, action="チケット使用", details=f"チケット(ID: {ticket.id})が使用されました。")
            else:
                error_message = f"このチケットは既に使用済みです。\n使用日時: {ticket.used_at.strftime('%Y-%m-%d %H:%M')}"
        except (GachaTicket.DoesNotExist, ValueError):
            error_message = "無効なチケットIDです。"
            
    context = {
        'message': message,
        'error_message': error_message,
    }
    return render(request, 'manager/gacha_scan.html', context)


# --- サイネージ関連 ---
@login_required
def signage_view(request):
    if request.user.role != 'signage':
        raise Http404
    return render(request, 'manager/signage.html')

def attraction_api(request):
    attractions_list = Attraction.objects.all().order_by('attraction_name')
    data = []
    for attraction in attractions_list:
        data.append({
            'id': attraction.id,
            'name': attraction.attraction_name,
            'group': attraction.group_name,
            'status': attraction.status,
            'is_theater': attraction.is_theater,
            'status_display': attraction.get_status_display(),
        })
    return JsonResponse({'attractions': data})