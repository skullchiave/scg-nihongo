// SCG日本語ドリル Service Worker
// 方針:
//  - ドリル本体 = stale-while-revalidate（SWR）:
//      キャッシュを即返して速さ・オフラインを確保しつつ、オンラインなら裏で最新を取得して差し替える。
//      → 次に開くと自動で新版。中身が変わってなければ HTTPキャッシュ/304 でほぼ通信ゼロ。
//  - ポータル(index) = network-first: オンライン時は最新のドリル一覧、圏外時はキャッシュ。
// ドリルを増やしても、ここの編集は不要（開かれたものを自動キャッシュ・自動更新）。
// CACHE版数は通常さわらなくてよい（SWRで内容は自動更新）。キャッシュ方式自体を変えた時だけ +1 する。
const CACHE = 'scg-v2';

// 最初に焼いておく「ガワ」（ポータルとアイコン類。小さいので一括）
const SHELL = [
  './', 'index.html', 'manifest.webmanifest',
  'logo-school.png', 'logo-mark.png',
  'icon-180.png', 'icon-192.png', 'icon-512.png', 'icon-512-maskable.png',
  'fonts/BIZUDPGothic-Regular.subset.woff2', 'fonts/BIZUDPGothic-Bold.subset.woff2'
];

self.addEventListener('install', e => {
  self.skipWaiting();
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL).catch(() => {})));
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys()
      .then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (url.origin !== location.origin) return; // 外部リクエストは触らない

  const isPortal = url.pathname.endsWith('/') || url.pathname.endsWith('/index.html');

  // 再取得は cache:'no-cache' で条件付き再検証（サーバに変更有無を確認＝未変更は304で激安・変更時のみ実DL）
  const fresh = () => fetch(new Request(url.href, { cache: 'no-cache' }));

  if (isPortal) {
    // network-first: 最新のドリル一覧を出す。オフライン時はキャッシュへフォールバック
    e.respondWith(
      fresh()
        .then(r => { const cp = r.clone(); caches.open(CACHE).then(c => c.put(req, cp)); return r; })
        .catch(() => caches.match(req).then(m => m || caches.match('index.html')))
    );
  } else {
    // stale-while-revalidate: キャッシュを即返し、裏で最新を取得して差し替える
    e.respondWith(
      caches.open(CACHE).then(cache =>
        cache.match(req).then(cached => {
          const network = fresh()
            .then(net => { if (net && net.ok) cache.put(req, net.clone()); return net; })
            .catch(() => null);
          e.waitUntil(network);          // 背景更新をSW終了から守る
          return cached || network;      // 初回（未キャッシュ）はネット待ち
        })
      )
    );
  }
});
