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
  'fonts/BIZUDPGothic-Regular.subset.woff2', 'fonts/BIZUDPGothic-Bold.subset.woff2',
  'assets/catalog.js', 'assets/drill-base.css', 'assets/drill-ui.css', 'assets/drill-ui.js'
];

self.addEventListener('install', e => {
  self.skipWaiting();
  // 1件ずつキャッシュして失敗を数える（addAll+握りつぶしだと「オフライン対応済みのつもりで
  // 実は焼けていない」が誰にも見えない。失敗してもinstall自体は成功させ、焼けた分だけ効かせる）
  e.waitUntil(caches.open(CACHE).then(c =>
    Promise.allSettled(SHELL.map(u => c.add(u))).then(rs => {
      const ng = rs.filter(r => r.status === 'rejected').length;
      if (ng) console.warn('[SCG SW] シェル ' + ng + '/' + SHELL.length + ' 件のキャッシュに失敗（オフライン対応が不完全な可能性）');
    })
  ));
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

  // ドリル一覧(catalog.js)もポータルと同じ network-first＝ドリルを足したら次に開いた時すぐ出る
  // ★共通UI(drill-base.css・drill-ui.css/js)も network-first（2026-11-11）。SWRだと見た目を直しても
  //   1回目は旧版が出て「直っていない」に見える（PC版レイアウト公開時に実際に起きた）
  const p = url.pathname;
  const isPortal = p.endsWith('/') || p.endsWith('/index.html') || p.endsWith('/assets/catalog.js')
    || p.endsWith('/assets/drill-base.css') || p.endsWith('/assets/drill-ui.css') || p.endsWith('/assets/drill-ui.js');

  // 再取得は cache:'no-cache' で条件付き再検証（サーバに変更有無を確認＝未変更は304で激安・変更時のみ実DL）
  const fresh = () => fetch(new Request(url.href, { cache: 'no-cache' }));

  if (isPortal) {
    // network-first: 最新のドリル一覧を出す。オフライン時はキャッシュへフォールバック
    // ★r.ok のときだけキャッシュする（SWR側と同じガード）。デプロイ直後等の 404/503 を
    //   put すると正常な index のキャッシュがエラーページで上書きされ、
    //   以後オフラインの学生にエラー画面が出続けてしまう
    e.respondWith(
      fresh()
        .then(r => { if (r && r.ok) { const cp = r.clone(); caches.open(CACHE).then(c => c.put(req, cp)); } return r; })
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
