# -*- coding: utf-8 -*-
"""
SISCOR - Utilitarios de Cache (Fase 7)
"""
from functools import wraps
from django.core.cache import cache
from django.http import JsonResponse
import hashlib
import json

def cache_api_response(timeout=300, key_prefix='api'):
    """
    Decorator para cachear respostas de API
    
    Uso:
        @cache_api_response(timeout=60)
        def minha_api(request):
            return JsonResponse({...})
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Gerar chave de cache
            cache_key = f"{key_prefix}:{view_func.__name__}"
            
            # Adicionar parametros GET na chave
            if request.GET:
                params = hashlib.md5(
                    json.dumps(dict(request.GET), sort_keys=True).encode()
                ).hexdigest()[:8]
                cache_key += f":{params}"
            
            # Verificar cache
            cached = cache.get(cache_key)
            if cached is not None:
                return JsonResponse(cached, safe=False)
            
            # Executar view
            response = view_func(request, *args, **kwargs)
            
            # Cachear resposta JSON
            if isinstance(response, JsonResponse):
                try:
                    data = json.loads(response.content)
                    cache.set(cache_key, data, timeout)
                except:
                    pass
            
            return response
        return wrapper
    return decorator


def clear_api_cache(prefix='api'):
    """Limpar cache de APIs"""
    # Em producao, usar cache.delete_pattern se disponivel
    cache.clear()
