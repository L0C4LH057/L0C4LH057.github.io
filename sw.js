const CACHE_NAME = 'zarewa-blog-cache-v1';

// Core assets to cache immediately upon installation
const PRECACHE_ASSETS = [
  './',
  'index.html',
  'whoami.html',
  'write-ups.html',
  'tools.html',
  'manifest.json',
  'images/profile.jpg',
  'images/icon-192.png',
  'images/icon-512.png'
];

// Install Event: open cache and precache core assets
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log('[Service Worker] Pre-caching core assets');
      return cache.addAll(PRECACHE_ASSETS);
    }).then(() => self.skipWaiting())
  );
});

// Activate Event: clean up old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME) {
            console.log('[Service Worker] Removing old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

// Fetch Event: intercept network requests
self.addEventListener('fetch', (event) => {
  // Only handle GET requests
  if (event.request.method !== 'GET') {
    return;
  }

  const url = new URL(event.request.url);

  // Bypass cache for dynamic external APIs, analytics, Firebase, and TTS audio
  if (
    url.hostname.includes('translate.google.com') ||
    url.hostname.includes('google-analytics') ||
    url.hostname.includes('firestore.googleapis.com') ||
    url.hostname.includes('firebaseapp.com') ||
    url.pathname.includes('posts-index.json')
  ) {
    return;
  }

  // Caching strategy:
  // - HTML pages (document navigation): Network-First (ensures fresh blog post content when online, fallback to cache when offline)
  // - Static assets (CSS, JS, Images, Fonts): Stale-While-Revalidate (fast rendering from cache, update in background)
  if (event.request.mode === 'navigate') {
    event.respondWith(
      fetch(event.request)
        .then((networkResponse) => {
          // Cache the latest page version
          if (networkResponse.status === 200) {
            const responseClone = networkResponse.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(event.request, responseClone));
          }
          return networkResponse;
        })
        .catch(() => {
          // Offline: try to return cached page, fallback to homepage
          return caches.match(event.request).then((cachedResponse) => {
            return cachedResponse || caches.match('index.html');
          });
        })
    );
  } else {
    event.respondWith(
      caches.match(event.request).then((cachedResponse) => {
        const fetchPromise = fetch(event.request)
          .then((networkResponse) => {
            if (networkResponse.status === 200) {
              const responseClone = networkResponse.clone();
              caches.open(CACHE_NAME).then((cache) => cache.put(event.request, responseClone));
            }
            return networkResponse;
          })
          .catch(() => {/* ignore network failures for background fetch */});

        // Return cache hit instantly, let background fetch update cache
        return cachedResponse || fetchPromise;
      })
    );
  }
});
