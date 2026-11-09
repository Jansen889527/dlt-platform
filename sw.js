// 大乐透工作台 Service Worker
// 策略：HTML/导航请求 network-first（保证在线更新即时生效），其余静态资源 cache-first 兜底
const CACHE = 'dlt-v5';
// 开奖数据 data.json 与 version.json 不入缓存：每次请求都走网络，保证刷新即最新
// 完全离线时页面会用内置 FALLBACK 快照兜底，不依赖 SW 缓存
const ASSETS = [
  './', './index.html', './manifest.webmanifest',
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

  // 开奖数据 / 版本号：永远读线上最新，绝不读缓存（刷新、切页签都能拿到新期）
  if (url.pathname.endsWith('/data.json') || url.pathname.endsWith('/version.json')) {
    e.respondWith(
      fetch(e.request, {cache:'no-store'}).catch(() => new Response('', {status:503, statusText:'offline'}))
    );
    return;
  }

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
