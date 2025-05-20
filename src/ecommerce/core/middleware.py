from django.shortcuts import redirect

class AnonymousRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.allowed_paths = [
            '/account/register/',
        ]
    
    def __call__(self, request):
        if request.user.is_authenticated and request.path in self.allowed_paths:
            return redirect('/')
        
        return self.get_response(request)