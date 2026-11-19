// Bokk Yoon – service worker : l'appli s'ouvre même sans connexion.
const CACHE = 'bokkyoon-v1';
const SHELL = ['/bokkyoon.html', '/assets/bokkyoon/icon.png', '/assets/bokkyoon/icon-192.png', '/assets/bokkyoon/manifest.webmanifest', '/bokkyoon-hors-ligne.html'];
self.addEventListener('install', e => { e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting())); });
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener('fetch', e => {
  const u = new URL(e.request.url);
  if (e.request.method !== 'GET' || u.origin !== location.origin) return; // l'API Google n'est jamais mise en cache
  e.respondWith(fetch(e.request).then(r => {
    if (r.ok && (u.pathname === '/bokkyoon.html' || u.pathname.startsWith('/assets/bokkyoon/'))) {
      const copy = r.clone(); caches.open(CACHE).then(c => c.put(e.request, copy));
    }
    return r;
  }).catch(() => caches.match(e.request, {ignoreSearch: true}).then(r => r || (e.request.mode === 'navigate' ? caches.match('/bokkyoon-hors-ligne.html') : undefined))));
});
