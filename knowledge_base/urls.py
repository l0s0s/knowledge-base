from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

urlpatterns = [
    path('knowledge/admin/', admin.site.urls),
    path('knowledge/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('knowledge/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    path('knowledge/openapi.json', SpectacularAPIView.as_view(), name='schema'),
    path('knowledge/', include('api.urls')),
]

if settings.DEBUG:
    # Serve static files (CSS, JS for admin and documentation)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    # Serve media files (uploaded user content)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
