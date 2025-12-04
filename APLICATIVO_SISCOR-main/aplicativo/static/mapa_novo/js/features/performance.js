// =============================================================================
// SISCOR - Lazy Loading e Performance (Fase 7)
// =============================================================================

(function() {
    'use strict';

    // -------------------------------------------------------------------------
    // LAZY LOADING DE IMAGENS
    // -------------------------------------------------------------------------
    const lazyImages = document.querySelectorAll('img[data-src]');
    
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver(function(entries, observer) {
            entries.forEach(function(entry) {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    img.removeAttribute('data-src');
                    img.classList.add('loaded');
                    observer.unobserve(img);
                }
            });
        }, {
            rootMargin: '50px 0px',
            threshold: 0.01
        });

        lazyImages.forEach(function(img) {
            imageObserver.observe(img);
        });
    } else {
        // Fallback para navegadores antigos
        lazyImages.forEach(function(img) {
            img.src = img.dataset.src;
        });
    }

    // -------------------------------------------------------------------------
    // DEBOUNCE PARA EVENTOS FREQUENTES
    // -------------------------------------------------------------------------
    window.SISCORDebounce = function(func, wait) {
        var timeout;
        return function executedFunction() {
            var context = this;
            var args = arguments;
            var later = function() {
                timeout = null;
                func.apply(context, args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    };

    // -------------------------------------------------------------------------
    // THROTTLE PARA LIMITAR CHAMADAS
    // -------------------------------------------------------------------------
    window.SISCORThrottle = function(func, limit) {
        var inThrottle;
        return function() {
            var context = this;
            var args = arguments;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(function() { inThrottle = false; }, limit);
            }
        };
    };

    // -------------------------------------------------------------------------
    // CACHE LOCAL DE REQUISICOES
    // -------------------------------------------------------------------------
    window.SISCORCache = {
        storage: {},
        maxAge: 60000, // 1 minuto

        get: function(key) {
            var item = this.storage[key];
            if (!item) return null;
            
            if (Date.now() - item.timestamp > this.maxAge) {
                delete this.storage[key];
                return null;
            }
            return item.data;
        },

        set: function(key, data) {
            this.storage[key] = {
                data: data,
                timestamp: Date.now()
            };
        },

        clear: function() {
            this.storage = {};
        }
    };

    // -------------------------------------------------------------------------
    // FETCH COM CACHE
    // -------------------------------------------------------------------------
    window.SISCORFetch = function(url, options) {
        options = options || {};
        var useCache = options.cache !== false;
        var cacheKey = url;

        // Verificar cache
        if (useCache) {
            var cached = SISCORCache.get(cacheKey);
            if (cached) {
                console.log('[SISCOR] Cache hit:', url);
                return Promise.resolve(cached);
            }
        }

        // Fazer requisicao
        return fetch(url, options)
            .then(function(response) {
                return response.json();
            })
            .then(function(data) {
                if (useCache) {
                    SISCORCache.set(cacheKey, data);
                }
                return data;
            });
    };

    // -------------------------------------------------------------------------
    // PREFETCH DE LINKS
    // -------------------------------------------------------------------------
    function prefetchLinks() {
        var links = document.querySelectorAll('a[data-prefetch]');
        
        if ('IntersectionObserver' in window) {
            var linkObserver = new IntersectionObserver(function(entries) {
                entries.forEach(function(entry) {
                    if (entry.isIntersecting) {
                        var link = document.createElement('link');
                        link.rel = 'prefetch';
                        link.href = entry.target.href;
                        document.head.appendChild(link);
                        linkObserver.unobserve(entry.target);
                    }
                });
            });

            links.forEach(function(link) {
                linkObserver.observe(link);
            });
        }
    }

    // -------------------------------------------------------------------------
    // OTIMIZACAO DE SCROLL
    // -------------------------------------------------------------------------
    var scrollHandler = SISCORThrottle(function() {
        // Eventos de scroll otimizados
        document.dispatchEvent(new CustomEvent('optimizedScroll'));
    }, 100);

    window.addEventListener('scroll', scrollHandler, { passive: true });

    // -------------------------------------------------------------------------
    // OTIMIZACAO DE RESIZE
    // -------------------------------------------------------------------------
    var resizeHandler = SISCORDebounce(function() {
        document.dispatchEvent(new CustomEvent('optimizedResize'));
    }, 250);

    window.addEventListener('resize', resizeHandler);

    // -------------------------------------------------------------------------
    // INICIALIZACAO
    // -------------------------------------------------------------------------
    document.addEventListener('DOMContentLoaded', function() {
        console.log('[SISCOR] Performance module loaded');
        prefetchLinks();
        
        // Marcar quando a pagina terminou de carregar
        window.addEventListener('load', function() {
            document.body.classList.add('page-loaded');
            
            // Log de performance
            if (window.performance) {
                var timing = performance.timing;
                var loadTime = timing.loadEventEnd - timing.navigationStart;
                console.log('[SISCOR] Page load time:', loadTime + 'ms');
            }
        });
    });

})();
