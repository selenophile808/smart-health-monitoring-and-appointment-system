"""
health_system URL Configuration
"""

from django.contrib import admin
from django.urls import path, include, re_path
from django.views.static import serve
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('django-admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('health/', include('health.urls')),
    path('appointments/', include('appointments.urls')),
    path('', include('dashboard.urls')),
]

# Profile photos / avatars (media files) must also show on the live Render site,
# where DEBUG is False and nothing else serves /media/. Fine for a demo.
urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
