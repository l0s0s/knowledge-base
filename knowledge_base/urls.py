from django.contrib import admin
from django.urls import path, include, reverse
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
import json

# Debug view для отладки запросов через Nginx
def debug_view(request):
    """
    Временный debug endpoint для диагностики работы Django за Nginx.
    Возвращает JSON с информацией о запросе, заголовках и пути.
    Доступен по /api/knowledge/debug/ (внешне) или /debug/ (внутренне после PrefixMiddleware).
    """
    import json
    from django.urls import reverse
    
    # Собираем информацию о запросе
    debug_info = {
        # Основные пути
        'request.path': request.path,
        'request.path_info': request.path_info,
        'request.get_full_path()': request.get_full_path(),
        'request.get_raw_uri()': request.get_raw_uri() if hasattr(request, 'get_raw_uri') else 'N/A',
        
        # SCRIPT_NAME и заголовки префикса
        'request.META.get("SCRIPT_NAME")': request.META.get('SCRIPT_NAME', 'NOT SET'),
        'request.META.get("HTTP_X_SCRIPT_NAME")': request.META.get('HTTP_X_SCRIPT_NAME', 'NOT SET'),
        
        # Host и протокол
        'request.META.get("HTTP_HOST")': request.META.get('HTTP_HOST', 'NOT SET'),
        'request.META.get("HTTP_X_FORWARDED_HOST")': request.META.get('HTTP_X_FORWARDED_HOST', 'NOT SET'),
        'request.META.get("HTTP_X_FORWARDED_PROTO")': request.META.get('HTTP_X_FORWARDED_PROTO', 'NOT SET'),
        'request.META.get("HTTP_X_FORWARDED_PORT")': request.META.get('HTTP_X_FORWARDED_PORT', 'NOT SET'),
        'request.scheme': request.scheme,
        'request.is_secure()': request.is_secure(),
        
        # Дополнительные заголовки от Nginx
        'request.META.get("HTTP_X_REAL_IP")': request.META.get('HTTP_X_REAL_IP', 'NOT SET'),
        'request.META.get("HTTP_X_FORWARDED_FOR")': request.META.get('HTTP_X_FORWARDED_FOR', 'NOT SET'),
        
        # Генерация URL для проверки
        'reverse("swagger-ui")': reverse('swagger-ui'),
        'reverse("schema")': reverse('schema'),
        
        # Все заголовки, начинающиеся с HTTP_X
        'all_HTTP_X_headers': {
            k: v for k, v in request.META.items() 
            if k.startswith('HTTP_X')
        },
        
        # Все заголовки, связанные с путями
        'path_related_meta': {
            'PATH_INFO': request.META.get('PATH_INFO', 'NOT SET'),
            'SCRIPT_NAME': request.META.get('SCRIPT_NAME', 'NOT SET'),
            'REQUEST_URI': request.META.get('REQUEST_URI', 'NOT SET'),
            'QUERY_STRING': request.META.get('QUERY_STRING', 'NOT SET'),
        }
    }
    
    # Логирование в консоль
    print("\n" + "="*80)
    print("DEBUG VIEW - Request Information")
    print("="*80)
    print(f"Path: {request.path}")
    print(f"Path Info: {request.path_info}")
    print(f"Full Path: {request.get_full_path()}")
    print(f"SCRIPT_NAME: {request.META.get('SCRIPT_NAME', 'NOT SET')}")
    print(f"HTTP_X_SCRIPT_NAME: {request.META.get('HTTP_X_SCRIPT_NAME', 'NOT SET')}")
    print(f"HTTP_HOST: {request.META.get('HTTP_HOST', 'NOT SET')}")
    print(f"HTTP_X_FORWARDED_HOST: {request.META.get('HTTP_X_FORWARDED_HOST', 'NOT SET')}")
    print(f"HTTP_X_FORWARDED_PROTO: {request.META.get('HTTP_X_FORWARDED_PROTO', 'NOT SET')}")
    print(f"Scheme: {request.scheme}")
    print(f"Is Secure: {request.is_secure()}")
    print("="*80 + "\n")
    
    return JsonResponse(debug_info, json_dumps_params={'indent': 2, 'ensure_ascii': False})


# Wrapper view for Swagger UI that ensures schema URL includes /api/knowledge prefix
def swagger_ui_view(request):
    """
    Wrapper for SpectacularSwaggerView that explicitly sets the schema URL
    to include the /api/knowledge prefix. This ensures Swagger UI requests
    the schema from /api/knowledge/schema/ instead of just /schema/.
    """
    # Get the schema URL with the prefix from SCRIPT_NAME
    # SCRIPT_NAME is set by PrefixMiddleware to /api/knowledge
    script_name = request.META.get('SCRIPT_NAME', '')
    schema_path = reverse('schema')
    
    # Construct the full schema URL with prefix
    # If SCRIPT_NAME exists, prepend it; otherwise use the reversed path
    if script_name:
        schema_url = script_name.rstrip('/') + schema_path
    else:
        schema_url = schema_path
    
    return SpectacularSwaggerView.as_view(url=schema_url)(request)


# All URL patterns are defined without "/api/knowledge" prefix
# PrefixMiddleware handles the "/api/knowledge" prefix from reverse proxy automatically
# Django works internally as if root is "/", but URLs are generated with "/api/knowledge" prefix externally
# Swagger/OpenAPI paths are accessible at /api/knowledge/docs/ and /api/knowledge/schema/ externally
# PrefixMiddleware strips /api/knowledge, so /api/knowledge/docs/ becomes /docs/ internally
# Swagger UI wrapper ensures it requests schema from /api/knowledge/schema/ (external URL)
urlpatterns = [
    path('admin/', admin.site.urls),
    path('debug/', debug_view, name='debug'),  # Debug endpoint для диагностики
    path('docs/', swagger_ui_view, name='swagger-ui'),  # Swagger UI with explicit schema URL
    path('redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    path('schema/', SpectacularAPIView.as_view(), name='schema'),  # OpenAPI schema endpoint
    path('', include('api.urls')),
]

if settings.DEBUG:
    # Serve static files (CSS, JS for admin and documentation)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    # Serve media files (uploaded user content)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
