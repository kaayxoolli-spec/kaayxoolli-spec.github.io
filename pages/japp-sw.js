// JÀPP – service worker : l'appli s'ouvre même sans connexion.
const CACHE = 'japp-v1';
const SHELL = ['/japp.html', '/assets/japp/icon.png', '/assets/japp/icon-192.png', '/assets/japp/manifest.webmanifest', '/japp-hors-ligne.html'];
self.addEventListener('install', e => { e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting())); });
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener('fetch', e => {
  const u = new URL(e.request.url);
  if (e.request.method !== 'GET' || u.origin !== location.origin) return; // l'API Google n'est jamais mise en cache
  e.respondWith(fetch(e.request).then(r => {
    if (r.ok && (u.pathname === '/japp.html' || u.pathname.startsWith('/assets/japp/'))) {
      const copy = r.clone(); caches.open(CACHE).then(c => c.put(e.request, copy));
    }
    return r;
  }).catch(() => caches.match(e.request, {ignoreSearch: true}).then(r => r || (e.request.mode === 'navigate' ? caches.match('/japp-hors-ligne.html') : undefined))));
});
