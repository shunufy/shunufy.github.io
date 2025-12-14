
/* Minimal Service Worker for GitHub Pages static sites */
// NOTE: v4 = fixes stale blog/posts.json caused by cache-first.
const CACHE = "shunufy-cache-v4";
const CORE = [
  "./",
  "./index.html",
  "./games.html",
  "./about.html",
  "./blog.html",
  "./post.html",
  "./style.css",
  "./app.js",
  "./shared.js",
  "./md.js",
  "./blog.js",
  "./post.js",
  "./offline.html",
  "./manifest.webmanifest",
  "./assets/icon-192.png",
  "./assets/icon-512.png"
];

function isBlogDynamic(pathname) {
  // Works both on custom domain and /repo/ style paths
  return pathname.includes("/posts/") || pathname.includes("/secret/");
}

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE).then((cache) => cache.addAll(CORE)).then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then(keys => Promise.all(keys.map(k => (k === CACHE ? null : caches.delete(k)))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  const req = event.request;
  if (req.method !== "GET") return;

  event.respondWith((async () => {
    const url = new URL(req.url);

    // Navigation: network-first (to get latest), fallback to cached, then offline page
    if (req.mode === "navigate") {
      try {
        const fresh = await fetch(req);
        const cache = await caches.open(CACHE);
        cache.put(req, fresh.clone());
        return fresh;
      } catch (e) {
        const cached = await caches.match(req);
        return cached || caches.match("./offline.html");
      }
    }

    // Blog content (posts.json / markdown): network-first
    // Fixes "更新したのに前の表示になる" caused by cache-first.
    if (url.origin === location.origin && isBlogDynamic(url.pathname)) {
      try {
        const fresh = await fetch(req);
        const cache = await caches.open(CACHE);
        cache.put(req, fresh.clone());
        return fresh;
      } catch (e) {
        const cached = await caches.match(req);
        return cached || caches.match("./offline.html");
      }
    }

    // Static: cache-first
    const cached = await caches.match(req);
    if (cached) return cached;

    try {
      const fresh = await fetch(req);
      const cache = await caches.open(CACHE);
      // Only cache same-origin static resources
      if (url.origin === location.origin) cache.put(req, fresh.clone());
      return fresh;
    } catch (e) {
      return caches.match("./offline.html");
    }
  })());
});
