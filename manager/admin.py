# manager/admin.py

from django.contrib import admin
from django.urls import path
from django.shortcuts import render
from django.db.models import F
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Attraction, Like, GachaTicket, UserActivity, SystemLog, Tag

# --- 管理サイトのカスタマイズ ---
class CustomAdminSite(admin.AdminSite):
    site_header = '文化祭混雑状況管理システム'
    site_title = '管理ページ'
    index_title = 'メニュー'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('ranking/', self.admin_view(self.ranking_view), name='ranking'),
        ]
        return custom_urls + urls

    def ranking_view(self, request):
        visitor_ranking = Attraction.objects.order_by(F('total_visitors').desc())
        like_ranking = Attraction.objects.order_by(F('likes_count').desc())
        context = dict(
           self.each_context(request),
           visitor_ranking=visitor_ranking,
           like_ranking=like_ranking,
        )
        return render(request, "admin/ranking.html", context)

custom_admin_site = CustomAdminSite(name='custom_admin')

# --- 各モデルの管理画面設定 ---
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon')
    search_fields = ('name',)

class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        ('ロールと担当設定', {'fields': ('role', 'managed_attractions')}),
    )
    list_display = ('username', 'email', 'role', 'is_staff')
    list_filter = BaseUserAdmin.list_filter + ('role',)
    filter_horizontal = ('managed_attractions',)

class AttractionAdmin(admin.ModelAdmin):
    list_display = ('attraction_name', 'group_name', 'status', 'tags_display', 'current_visitors', 'capacity')
    list_filter = ('is_theater', 'status', 'tags')
    search_fields = ('attraction_name', 'group_name')
    fieldsets = [
        ('基本情報', {'fields': ['attraction_name', 'group_name', 'tags', 'description', 'video_file']}),
        ('人数・状態管理', {'fields': ['capacity', 'current_visitors', 'status']}),
        ('演劇設定', {'fields': ['is_theater', 'start_time', 'end_time'], 'classes': ('collapse',),}),
        ('集計情報', {'fields': ['total_visitors', 'likes_count']}),
        ('QRコードID', {'fields': ['entry_qr_id', 'exit_qr_id']}),
    ]
    readonly_fields = ('total_visitors', 'likes_count', 'entry_qr_id', 'exit_qr_id')
    filter_horizontal = ('tags',)

    # 一覧ページにタグを表示するためのメソッド
    def tags_display(self, obj):
        return ", ".join([tag.name for tag in obj.tags.all()])
    tags_display.short_description = "タグ"

class SystemLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'user', 'action')
    list_filter = ('user', 'action', 'timestamp')
    search_fields = ('action', 'details', 'user__username')
    readonly_fields = [f.name for f in SystemLog._meta.fields]
    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False

class GachaTicketAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_used', 'issued_at', 'used_at')
    list_filter = ('is_used',)
    search_fields = ('user__username',)
    readonly_fields = ('id', 'user', 'issued_at', 'used_at', 'used_by')

class UserActivityAdmin(admin.ModelAdmin):
    list_display = ('user', 'attraction', 'entry_time', 'exit_time', 'duration_seconds')
    search_fields = ('user__username', 'attraction__attraction_name')

class LikeAdmin(admin.ModelAdmin):
    list_display = ('user', 'attraction', 'created_at')
    search_fields = ('user__username', 'attraction__attraction_name')

# --- モデルをカスタム管理サイトに登録 ---
custom_admin_site.register(Tag, TagAdmin)
custom_admin_site.register(User, UserAdmin)
custom_admin_site.register(Attraction, AttractionAdmin)
custom_admin_site.register(SystemLog, SystemLogAdmin)
custom_admin_site.register(GachaTicket, GachaTicketAdmin)
custom_admin_site.register(Like, LikeAdmin)
custom_admin_site.register(UserActivity, UserActivityAdmin)