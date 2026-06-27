const CACHE_NAME = 'mardior-v1';
const urlsToCache = ['/dashboard', '/emails', '/orders', '/shipping', '/influencers', '/settings', '/static/app.css'];

self.addEventListener('install', event => {
    event.waitUntil(caches.open(CACHE_NAME).then(cache => cache.addAll(urlsToCache)));
});

self.addEventListener('fetch', event => {
    event.respondWith(
        caches.match(event.request).then(response => response || fetch(event.request))
    );
});
