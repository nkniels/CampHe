importScripts('https://www.gstatic.com/firebasejs/10.8.0/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/10.8.0/firebase-messaging-compat.js');

const firebaseConfig = {
    projectId: "camphe-237",
    appId: "1:206407742812:web:9d03dd72b8d2c9833bfd99",
    storageBucket: "camphe-237.firebasestorage.app",
    apiKey: "AIzaSyB6LXM-HrS3pwRotxu59xWtdW6dib0QoIA",
    authDomain: "camphe-237.firebaseapp.com",
    messagingSenderId: "206407742812",
    measurementId: "G-HD18645TPH"
};

firebase.initializeApp(firebaseConfig);
const messaging = firebase.messaging();

messaging.onBackgroundMessage((payload) => {
    console.log('[firebase-messaging-sw.js] Received background message ', payload);
    const notificationTitle = payload.notification.title;
    const notificationOptions = {
        body: payload.notification.body,
        icon: '/icon-192.png'
    };
    self.registration.showNotification(notificationTitle, notificationOptions);
});

const CACHE_NAME = 'camphe-cache-v2';
const urlsToCache = [
  './',
  './index.html',
  './styles.css',
  './app.js',
  './manifest.json',
  './data/campaigns.json'
];

self.addEventListener('install', event => {
  self.skipWaiting(); // Force SW to activate immediately
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(urlsToCache))
  );
});

self.addEventListener('activate', event => {
  // Clean up old caches
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== CACHE_NAME) {
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', event => {
  // Network-first strategy: try to fetch from network, if fails, use cache.
  // This ensures the app always gets the latest CSS, JS, and JSON when online!
  event.respondWith(
    fetch(event.request)
      .then(response => {
        // Clone and update cache with new version
        const resClone = response.clone();
        caches.open(CACHE_NAME).then(cache => {
          cache.put(event.request, resClone);
        });
        return response;
      })
      .catch(() => caches.match(event.request))
  );
});
