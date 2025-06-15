# bunkasai_prj/urls.py

from django.urls import path, include
from manager.admin import custom_admin_site
from django.conf import settings          # ★追加
from django.conf.urls.static import static  # ★追加

urlpatterns = [
    path('admin/', custom_admin_site.urls),
    path('', include('manager.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)