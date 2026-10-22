/* Baran Cook service worker — offline-capable shell + cached atlas data.
   Strategy:
   - static shell: cache-first (versioned CACHE), network refresh fallback
   - /api/*: network-first, cache copy for offline browsing of last seen data
*/
'use strict';
const CACHE = 'barancook-v1.2.0';
const SHELL = ['/', '/css/styles.css', '/js/app.js', '/manifest.webmanifest', '/icons/icon-192.png', '/icons/icon-512.png'];

self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(CACHE).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then((ks) => Promise.all(ks.filter((k) => k !== CACHE).map((k) => caches.delete(k)))).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (e) => {
  const req = e.request;
  if (req.method !== 'GET') return;
  let url;
  try { url = new URL(req.url); } catch { return; }
  if (url.origin !== location.origin) return;

  /* API: network-first, keep last response for offline */
  if (url.pathname.startsWith('/api/')) {
    e.respondWith(
      fetch(req).then((res) => {
        const copy = res.clone();
        caches.open(CACHE).then((c) => c.put(req, copy));
        return res;
      }).catch(() => caches.match(req).then((hit) => hit || new Response(
        JSON.stringify({ ok: false, offline: true, error: 'offline — لا اتصال ولا نسخة محفوظة لهذا الطلب' }),
        { status: 503, headers: { 'Content-Type': 'application/json; charset=utf-8' } }
      )))
    );
    return;
  }

  /* static + navigation: stale-while-revalidate — cached copy is served
     immediately while a fresh network copy refreshes the cache in background,
     so app updates reach users on their second load without manual bumps. */
  e.respondWith(
    caches.open(CACHE).then((c) => c.match(req)).then((hit) => {
      const refresh = fetch(req).then((res) => {
        if (res.ok) {
          const copy = res.clone();
          caches.open(CACHE).then((cc) => cc.put(req, copy));
        }
        return res;
      }).catch(() => hit || caches.match('/'));
      if (hit) e.waitUntil(refresh); // keep SW alive so the background refresh completes
      return hit || refresh;
    })
  );
});
