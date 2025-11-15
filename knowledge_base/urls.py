from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

# All URL patterns are defined without "/api/knowledge" prefix
# PrefixMiddleware handles the "/api/knowledge" prefix from reverse proxy automatically
# Django works internally as if root is "/", but URLs are generated with "/api/knowledge" prefix externally
# Swagger/OpenAPI paths are accessible at /api/knowledge/docs/ and /api/knowledge/schema/ externally
# PrefixMiddleware strips /api/knowledge, so /api/knowledge/docs/ becomes /docs/ internally
urlpatterns = [
    path('admin/', admin.site.urls),
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('', include('api.urls')),
]

if settings.DEBUG:
    # Serve static files (CSS, JS for admin and documentation)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    # Serve media files (uploaded user content)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
