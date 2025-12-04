// Service Worker basico para SISCOR
const CACHE_NAME = 'siscor-v1';

self.addEventListener('install', function(event) {
    console.log('[SW] Instalado');
});

self.addEventListener('fetch', function(event) {
    // Pass through - nao fazer cache por enquanto
    event.respondWith(fetch(event.request));
});
