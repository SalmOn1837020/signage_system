# manager/urls.py (新規作成)

from django.urls import path
from . import views

# アプリケーションの名前空間を設定（URLの逆引き時に利用）
app_name = 'manager'

urlpatterns = [
    # --- トップページ ---
    path('', views.attraction_list, name='attraction_list'),

    # --- アカウント関連 ---
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # --- 出し物詳細・評価 ---
    path('attraction/<int:attraction_id>/', views.attraction_detail, name='attraction_detail'),
    path('attraction/<int:attraction_id>/like/', views.like_attraction, name='like_attraction'),

    # --- ガチャチケット関連 ---
    path('my_tickets/', views.my_tickets, name='my_tickets'),
    path('gacha/scan/', views.gacha_scan_view, name='gacha_scan'),

    # --- サイネージ ---
    path('signage/', views.signage_view, name='signage'),
    path('api/attractions/', views.attraction_api, name='attraction_api'), # データ供給用API
    
    path('qr-codes/', views.qr_code_list, name='qr_code_list'),

    # 例: /qr/codes/
    path('qr_codes/', views.qr_code_list, name='qr_code_list'),
    
    # 例: /process/entry/{UUID}/
    path('process/entry/<uuid:qr_id>/', views.process_entry, name='process_entry'),

    # 例: /process/exit/{UUID}/
    path('process/exit/<uuid:qr_id>/', views.process_exit, name='process_exit'),
]