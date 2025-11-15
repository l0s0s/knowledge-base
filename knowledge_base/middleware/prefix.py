"""
PrefixMiddleware: Handles X-Script-Name header from reverse proxy.

This middleware allows Django to work internally as if the root URL is "/",
while the reverse proxy (nginx/LB) adds the "/api/knowledge" prefix externally.

When nginx sends "X-Script-Name: /api/knowledge" header:
- Strips the prefix from request.path_info so Django routes work normally
- Sets request.META['SCRIPT_NAME'] so Django generates correct URLs with the prefix

This ensures:
- Django routes don't need "/api/knowledge" prefix internally
- Django-generated URLs (redirects, static files, etc.) include "/api/knowledge" prefix
- Works transparently behind reverse proxy
"""


class PrefixMiddleware:
    """
    Middleware to handle X-Script-Name header from reverse proxy.
    
    The reverse proxy (nginx) sends X-Script-Name header with the prefix.
    This middleware:
    1. Reads X-Script-Name from request headers
    2. Strips it from path_info so Django routing works as if root is "/"
    3. Sets SCRIPT_NAME in META so Django URL generation includes the prefix
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Get the script name prefix from X-Script-Name header (sent by nginx)
        # Example: nginx sends "X-Script-Name: /api/knowledge"
        script_name = request.META.get('HTTP_X_SCRIPT_NAME', '').rstrip('/')
        
        if script_name:
            # Remove the prefix from path_info so Django routes work normally
            # Example: "/api/knowledge/admin/" becomes "/admin/" internally
            # Example: "/api/knowledge/knowledge/docs/" becomes "/knowledge/docs/" internally
            if request.path_info.startswith(script_name):
                request.path_info = request.path_info[len(script_name):]
                # Ensure path_info starts with "/" (handle case where script_name was the entire path)
                if not request.path_info.startswith('/'):
                    request.path_info = '/' + request.path_info
            
            # Set SCRIPT_NAME in META so Django's URL generation includes the prefix
            # This ensures redirects, static URLs, etc. are generated correctly with "/api/knowledge" prefix
            request.META['SCRIPT_NAME'] = script_name
        
        return self.get_response(request)

