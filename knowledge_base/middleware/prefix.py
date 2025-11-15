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
        original_path_info = request.path_info
        original_script_name_header = request.META.get('HTTP_X_SCRIPT_NAME', '')
        script_name = original_script_name_header.rstrip('/')
        
        # Логирование для отладки
        print("\n" + "-"*80)
        print("PrefixMiddleware - Processing Request")
        print("-"*80)
        print(f"Original path_info: {original_path_info}")
        print(f"HTTP_X_SCRIPT_NAME header: {original_script_name_header}")
        print(f"Extracted script_name: {script_name}")
        
        if script_name:
            # Remove the prefix from path_info so Django routes work normally
            # Example: "/api/knowledge/admin/" becomes "/admin/" internally
            # Example: "/api/knowledge/knowledge/docs/" becomes "/knowledge/docs/" internally
            if request.path_info.startswith(script_name):
                request.path_info = request.path_info[len(script_name):]
                # Ensure path_info starts with "/" (handle case where script_name was the entire path)
                if not request.path_info.startswith('/'):
                    request.path_info = '/' + request.path_info
                print(f"Stripped prefix: path_info changed from '{original_path_info}' to '{request.path_info}'")
            else:
                print(f"WARNING: path_info '{request.path_info}' does not start with script_name '{script_name}'")
            
            # Set SCRIPT_NAME in META so Django's URL generation includes the prefix
            # This ensures redirects, static URLs, etc. are generated correctly with "/api/knowledge" prefix
            request.META['SCRIPT_NAME'] = script_name
            print(f"Set SCRIPT_NAME in META: {script_name}")
        else:
            print("WARNING: No HTTP_X_SCRIPT_NAME header found! PrefixMiddleware will not modify request.")
            print("This is normal if accessing Django directly (not through nginx).")
        
        print(f"Final path_info: {request.path_info}")
        print(f"Final SCRIPT_NAME: {request.META.get('SCRIPT_NAME', 'NOT SET')}")
        print("-"*80 + "\n")
        
        return self.get_response(request)

