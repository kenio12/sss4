# middleware.py

from django.http import HttpResponsePermanentRedirect

class RedirectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host()
        if host == 'sss4.life':
            return HttpResponsePermanentRedirect('https://www.sss4.life' + request.path)
        response = self.get_response(request)
        return response