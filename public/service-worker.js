const CACHE_NAME = 'tqqq-tracker-v1';
const ASSETS = [
    '/',
    '/index.html',
    '/style.css',
    '/logo.svg',
    '/manifest.json'
];

self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => cache.addAll(ASSETS))
    );
});

self.addEventListener('fetch', (event) => {
    // For data.json, always fetch from network (bypass cache)
    if (event.request.url.includes('data.json')) {
        event.respondWith(fetch(event.request));
        return;
    }

    event.respondWith(
        caches.match(event.request)
            .then((response) => response || fetch(event.request))
    );
});
