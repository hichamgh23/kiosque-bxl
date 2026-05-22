from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

admin.site.site_header = 'Le Kiosque BXL'
admin.site.site_title  = 'Le Kiosque BXL'
admin.site.index_title = 'Gestion'

ADMIN_PATH = getattr(settings, 'ADMIN_PATH', 'bxl-mgmt-9k2z')

urlpatterns = [
    path(f'{ADMIN_PATH}/', admin.site.urls),
    path('i18n/', include('django.conf.urls.i18n')),
    path('', include('core.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
