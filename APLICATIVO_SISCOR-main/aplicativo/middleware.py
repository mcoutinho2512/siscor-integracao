# -*- coding: utf-8 -*-
"""
SISCOR - Middleware de Segurança
Fase 4: Segurança Avançada
"""

import time
import logging
from collections import defaultdict
from django.shortcuts import redirect
from django.http import JsonResponse, HttpResponseForbidden
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger('aplicativo.security')


class SecurityMiddleware(MiddlewareMixin):
    """Middleware de segurança - Proteção de URLs e Headers"""
    
    PUBLIC_URLS = [
        '/login/',
        '/logout/',
        '/admin/',
        '/static/',
        '/media/',
        '/api/',
        '/favicon.ico',
    ]
    
    def process_view(self, request, view_func, view_args, view_kwargs):
        path = request.path
        
        if any(path.startswith(url) for url in self.PUBLIC_URLS):
            return None
        
        if not request.user.is_authenticated:
            ip = self._get_client_ip(request)
            logger.warning(f"Acesso não autorizado: {path} de {ip}")
            return redirect('login')
        
        return None
    
    def process_response(self, request, response):
        if 'X-Frame-Options' not in response:
            response['X-Frame-Options'] = 'SAMEORIGIN'
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        return response
    
    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', 'unknown')


class RateLimitMiddleware(MiddlewareMixin):
    """Middleware para Rate Limiting"""
    
    _login_attempts = defaultdict(lambda: {'count': 0, 'time': 0})
    _api_requests = defaultdict(lambda: {'count': 0, 'time': 0})
    
    LOGIN_MAX_ATTEMPTS = 5
    LOGIN_WINDOW = 900
    API_ANON_MAX = 100
    API_AUTH_MAX = 1000
    API_WINDOW = 60
    
    def process_request(self, request):
        ip = self._get_client_ip(request)
        path = request.path
        now = time.time()
        
        if path == '/login/' and request.method == 'POST':
            return self._check_login(ip, now)
        
        if path.startswith('/api/'):
            return self._check_api(request, ip, now)
        
        return None
    
    def _check_login(self, ip, now):
        key = f'login:{ip}'
        
        if now - self._login_attempts[key]['time'] > self.LOGIN_WINDOW:
            self._login_attempts[key] = {'count': 0, 'time': now}
        
        if self._login_attempts[key]['count'] >= self.LOGIN_MAX_ATTEMPTS:
            remaining = int(self.LOGIN_WINDOW - (now - self._login_attempts[key]['time']))
            logger.warning(f"Rate limit login: {ip}")
            return HttpResponseForbidden(
                f'<html><body style="font-family:Arial;text-align:center;margin-top:100px;background:#1e293b;color:white;">'
                f'<h1 style="color:#ef4444;">🚫 Muitas tentativas</h1>'
                f'<p>Tente novamente em {remaining // 60} minutos.</p></body></html>',
                content_type='text/html'
            )
        
        self._login_attempts[key]['count'] += 1
        self._login_attempts[key]['time'] = now
        return None
    
    def _check_api(self, request, ip, now):
        is_auth = hasattr(request, 'user') and request.user.is_authenticated
        max_req = self.API_AUTH_MAX if is_auth else self.API_ANON_MAX
        identifier = request.user.username if is_auth else ip
        key = f'api:{identifier}'
        
        if now - self._api_requests[key]['time'] > self.API_WINDOW:
            self._api_requests[key] = {'count': 0, 'time': now}
        
        if self._api_requests[key]['count'] >= max_req:
            logger.warning(f"Rate limit API: {identifier}")
            return JsonResponse({
                'success': False,
                'error': 'rate_limit_exceeded',
                'message': 'Muitas requisições. Tente novamente em breve.'
            }, status=429)
        
        self._api_requests[key]['count'] += 1
        return None
    
    def process_response(self, request, response):
        if request.path.startswith('/api/'):
            ip = self._get_client_ip(request)
            is_auth = hasattr(request, 'user') and request.user.is_authenticated
            identifier = request.user.username if is_auth else ip
            key = f'api:{identifier}'
            max_req = self.API_AUTH_MAX if is_auth else self.API_ANON_MAX
            current = self._api_requests.get(key, {}).get('count', 0)
            response['X-RateLimit-Limit'] = str(max_req)
            response['X-RateLimit-Remaining'] = str(max(0, max_req - current))
        return response
    
    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', 'unknown')
