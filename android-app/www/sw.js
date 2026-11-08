// 大乐透工作台 Service Worker
// 策略：HTML/导航请求 network-first（保证在线更新即时生效），其余静态资源 cache-first 兜底
const CACHE = 'dlt-v2';
const ASSETS = [
  './', './index.html', './data.json', './manifest.webmanifest',
  './icon-192.png', './icon-512.png', './icon-maskable-512.png', './apple-touch-icon.png'
];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(ASSETS)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);
  // 腾讯云函数接口：实时数据，不缓存，直接走网络
  if (url.hostname.includes('tencentscf.com')) return;
  if (e.request.method !== 'GET') return;

  const isNav = e.request.mode === 'navigate'
    || url.pathname.endsWith('/')
    || url.pathname.endsWith('index.html');

  if (isNav) {
    // network-first：先请求线上最新页面，失败才用缓存兜底
    e.respondWith(
      fetch(e.request).then(resp => {
        const cp = resp.clone();
        caches.open(CACHE).then(c => c.put(e.request, cp));
        return resp;
      }).catch(() => caches.match(e.request))
    );
    return;
  }

  // 其余静态资源：cache-first，断网也能用
  e.respondWith(
    caches.match(e.request).then(r =>
      r || fetch(e.request).then(resp => {
        const cp = resp.clone();
        caches.open(CACHE).then(c => c.put(e.request, cp));
        return resp;
      }).catch(() => r)
    )
  );
});
