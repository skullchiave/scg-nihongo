# -*- coding: utf-8 -*-
"""
見た目の自動点検（教科書ドリル24本＋JLPT ドリル）
=========================================
問題・語彙・ドリルを足したら、これを1回回す。はみ出し・エラーが0件なら見た目は崩れていない。

  py scripts/check_layout.py                  # 全ドリル×全モード×3サイズを点検（約3分）
  py scripts/check_layout.py L7-1 L9          # 名前の一部で絞る
  py scripts/check_layout.py --shots tmp/shots/after          # 画面写真も保存する
  py scripts/check_layout.py --ref HEAD --shots tmp/shots/before   # コミット済みの版で撮る（比較の基準）
  py scripts/check_layout.py --compare tmp/shots/before tmp/shots/after   # 2組の写真を1画素ずつ比べる
  py scripts/check_layout.py --sp --zoom 1.3   # スマホ幅だけ・文字サイズ Aa 130% で（1.15 / 1.3）

サイズ: スマホ 375×760 ／ PC 1920×1080 ／ PC 1280×800
見るもの（★＝NG＝直す。・＝参考）
  ★ JSエラー
  ★ 横のはみ出し（ページ全体・画面・カード/ボタン/問題の1つ1つ）… はみ出した語をそのまま印字
  ★ グループ分け・リズムが縦に1画面へ収まらない（この2つは1画面で使う前提）
  ★ 絵文字が見えている／ルール画面のカード上端の色帯／スマホで44pxより低いボタン
  ・ ルール・めくりの縦スクロール（読む画面・カードが多い画面は縦スクロール可）
語彙の長さは「めくり」で全カード（表・裏）を見る＝全語が1回は検査される。
仕組み: Playwright＋インストール済みの Chrome。/scg-nihongo/ をこのリポのファイルで返す（本番と同じHTMLのまま）。
乱数は固定＝同じ版なら何度撮っても同じ写真（--compare で前後比較できる）。終了コード: NG があれば 1。
"""
import sys, os, re, glob, subprocess, argparse, mimetypes

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORIGIN = "http://scg.test"
SIZES = [("sp", 375, 760), ("pc1920", 1920, 1080), ("pc1280", 1280, 800)]
FIT_MODES = ("sort", "rhythm")   # 1画面に収まるべきモード

INIT = """(function(){var s=12345;Math.random=function(){s=(s*1103515245+12345)%2147483648;return s/2147483648;};})();
try{localStorage.clear()}catch(e){}"""

PROBE = r"""() => {
  const out = {page: 0, screen: 0, sy: 0, items: []};
  const d = document.documentElement;
  out.page = d.scrollWidth - d.clientWidth;
  const s = document.querySelector('.screen.on') || document.querySelector('main') || document.body;
  out.screen = s.scrollWidth - s.clientWidth;
  out.sy = s.scrollHeight - s.clientHeight;
  const sel = '.face, .qcard, .rcard, .choices button, .rule, .rules > *, .note, .dui-segb, .dui-hd, .sortbtns button, .rauto, .opt, .q, .sim';
  const seen = new Set();
  for (const el of document.querySelectorAll(sel)) {
    if (!el.getClientRects().length) continue;            // 隠れている物は見ない
    // 中身の実際の位置（縮小 transform も反映）が枠の内側に収まっているか
    const r = el.getBoundingClientRect(), rg = document.createRange();
    rg.selectNodeContents(el);
    const c = rg.getBoundingClientRect();
    if (!c.width) continue;
    const inL = r.left + el.clientLeft, inR = inL + el.clientWidth * (r.width / (el.offsetWidth || r.width));
    const over = Math.round(Math.max(c.right - inR, inL - c.left));
    if (over > 1) {
      const t = (el.innerText || el.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 24);
      const k = el.className + '|' + t;
      if (!seen.has(k)) { seen.add(k); out.items.push((el.className || el.tagName) + '「' + t + '」+' + over + 'px'); }
    }
  }
  // 絵文字が見えている（端末で絵がちがう・大きさがそろわない）
  const vis = (el) => el && el.getClientRects().length && getComputedStyle(el).visibility !== 'hidden';
  out.emoji = [];
  const tw = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  let n;
  while ((n = tw.nextNode())) {
    const m = n.nodeValue.match(/[\u{1F300}-\u{1FAFF}⭕❌★⚠✅]/u);
    if (m && vis(n.parentElement) && !n.parentElement.closest('script,style,nav')) out.emoji.push(m[0]);
  }
  // ルール画面のカード上端の色帯（3px以上）
  out.band = 0;
  if (s.id === 'rule') for (const el of s.querySelectorAll('*')) {
    if (vis(el) && parseFloat(getComputedStyle(el).borderTopWidth) >= 3) out.band++;
  }
  // 44px より低いボタン（スマホ）
  out.small = [];
  if (innerWidth <= 640) for (const el of document.querySelectorAll('.screen.on button, .dui-hd button, .dui-hd a')) {
    const r = el.getBoundingClientRect();
    if (vis(el) && r.height && r.height < 43.5) out.small.push((el.innerText || el.getAttribute('aria-label') || el.className).trim().slice(0, 12) + ' ' + Math.round(r.height) + 'px');
  }
  return out;
}"""


class Source:
    """ファイルの出どころ（作業ツリー or git の版）"""
    def __init__(self, ref=None):
        self.ref = ref

    def read(self, rel):
        rel = rel.replace("\\", "/")
        if self.ref:
            r = subprocess.run(["git", "-C", ROOT, "show", f"{self.ref}:{rel}"], capture_output=True)
            return r.stdout if r.returncode == 0 else None
        p = os.path.join(ROOT, rel)
        return open(p, "rb").read() if os.path.isfile(p) else None

    def drills(self):
        if self.ref:
            r = subprocess.run(["git", "-C", ROOT, "ls-tree", "--name-only", self.ref, "tsunagu/"], capture_output=True, text=True)
            return sorted(x for x in r.stdout.split() if x.endswith(".html"))
        return sorted("tsunagu/" + os.path.basename(p) for p in glob.glob(os.path.join(ROOT, "tsunagu", "*.html")))


def serve(src):
    def handler(route):
        url = route.request.url
        if not url.startswith(ORIGIN + "/scg-nihongo/"):
            return route.abort()
        rel = url[len(ORIGIN + "/scg-nihongo/"):].split("?")[0].split("#")[0] or "index.html"
        if rel.endswith("/"): rel += "index.html"
        body = src.read(rel)
        if body is None:
            return route.fulfill(status=404, body=b"")
        ct = mimetypes.guess_type(rel)[0] or "application/octet-stream"
        if rel.endswith(".js"): ct = "text/javascript"
        if rel.endswith(".woff2"): ct = "font/woff2"
        route.fulfill(status=200, body=body, headers={"content-type": ct})
    return handler


def run_check(args):
    from playwright.sync_api import sync_playwright
    src = Source(args.ref)
    targets = [d for d in src.drills() if not args.names or any(n in d for n in args.names)]
    # JLPT ドリル（jlpt/*.html＝N4・N3・N2…。共通UIは使わない自前の見た目）
    jl = sorted("jlpt/" + os.path.basename(x) for x in glob.glob(os.path.join(ROOT, "jlpt", "*.html"))) if not args.ref else         sorted(x for x in subprocess.run(["git", "-C", ROOT, "ls-tree", "--name-only", args.ref, "jlpt/"], capture_output=True, text=True).stdout.split() if x.endswith(".html"))
    targets += [j for j in jl if not args.names or any(n in j for n in args.names)]
    if args.shots: os.makedirs(args.shots, exist_ok=True)
    ng, notes, count = [], [], 0
    with sync_playwright() as p:
        br = p.chromium.launch(channel="chrome")
        for tag, W, H in [x for x in SIZES if not args.sp or x[0] == "sp"]:
            if args.zoom: tag = f"{tag}z{int(round(float(args.zoom) * 100))}"
            ctx = br.new_context(viewport={"width": W, "height": H}, device_scale_factor=1, service_workers="block")
            ctx.route("**/*", serve(src))
            ctx.add_init_script(INIT + (f"try{{localStorage.setItem('drill_zoom','{args.zoom}')}}catch(e){{}}" if args.zoom else ""))
            for rel in targets:
                html = (src.read(rel) or b"").decode("utf-8", "ignore")
                name = os.path.basename(rel)[:-5]
                modes = re.findall(r'<button[^>]*data-s="([a-z]+)"', html) or [""]
                for m in modes:
                    page = ctx.new_page()
                    errs = []
                    page.on("pageerror", lambda e, errs=errs: errs.append(str(e)[:120]))
                    page.goto(f"{ORIGIN}/scg-nihongo/{rel}", wait_until="load")
                    page.evaluate("document.fonts.ready")
                    if m:
                        page.evaluate(f"show({m!r})")
                    page.wait_for_timeout(450)
                    r = page.evaluate(PROBE)
                    label = f"{tag:6} {name}{(':' + m) if m else ''}"
                    count += 1
                    if errs: ng.append(f"{label}  JSエラー: {errs[0]}")
                    if r["page"] > 1: ng.append(f"{label}  ページが横に {r['page']}px はみ出し")
                    if r["screen"] > 1: ng.append(f"{label}  画面が横に {r['screen']}px はみ出し")
                    for it in r["items"]: ng.append(f"{label}  はみ出し {it}")
                    if r["emoji"]: ng.append(f"{label}  絵文字 {''.join(sorted(set(r['emoji'])))}")
                    if r["band"]: ng.append(f"{label}  カード上端の色帯 {r['band']}か所")
                    for it in r["small"]: ng.append(f"{label}  44pxより低いボタン「{it}」")
                    if r["sy"] > 1:
                        # 1画面に収まるべきなのは Aa 100% の時だけ（文字を大きくしたら縦スクロールは可）
                        (ng if m in FIT_MODES and not args.zoom else notes).append(f"{label}  縦スクロール {r['sy']}px")
                    if args.shots:
                        page.screenshot(path=os.path.join(args.shots, f"{tag}_{name}{('_' + m) if m else ''}.png"))
                    # 操作した後の画面（めくり＝全部めくった裏面／グループ分け＝1問こたえた後）
                    act = {"flip": "document.querySelectorAll('.screen.on .fcard').forEach(c=>c.click())",
                           "sort": "(document.querySelector('.screen.on .choices button')||{click(){}}).click()"}.get(m)
                    if act:
                        n_err = len(errs)
                        page.evaluate(act)
                        page.wait_for_timeout(700)
                        r = page.evaluate(PROBE)
                        for it in r["items"]: ng.append(f"{label}(操作後)  はみ出し {it}")
                        if r["screen"] > 1: ng.append(f"{label}(操作後)  画面が横に {r['screen']}px はみ出し")
                        if m in FIT_MODES and r["sy"] > 1 and not args.zoom: ng.append(f"{label}(操作後)  縦スクロール {r['sy']}px")
                        if len(errs) > n_err: ng.append(f"{label}(操作後)  JSエラー: {errs[-1]}")
                        if args.shots:
                            page.screenshot(path=os.path.join(args.shots, f"{tag}_{name}_{m}_after.png"))
                    page.close()
            ctx.close()
        br.close()
    print(f"点検した画面: {count}（{len(targets)}ページ × モード × サイズ{('・Aa ' + args.zoom) if args.zoom else ''}）")
    print(f"★NG: {len(ng)}件")
    for x in ng: print("  ★", x)
    print(f"・参考（ルール・めくりの縦スクロール）: {len(notes)}件")
    if args.verbose:
        for x in notes: print("  ・", x)
    if args.shots: print("写真:", os.path.abspath(args.shots))
    return 1 if ng else 0


def run_compare(a, b):
    from PIL import Image, ImageChops
    names = sorted(f for f in os.listdir(a) if f.endswith(".png"))
    diff, missing, wobble = [], [], []
    for f in names:
        pb = os.path.join(b, f)
        if not os.path.exists(pb): missing.append(f); continue
        x, y = Image.open(os.path.join(a, f)).convert("RGB"), Image.open(pb).convert("RGB")
        if x.size != y.size: diff.append((f, "大きさが違う")); continue
        bb = ImageChops.difference(x, y).getbbox()
        # 回転したカード（めくりの裏面）の角は描くたびに1画素ゆれる＝4画素以下は「ゆれ」として別に数える
        if bb and (bb[2] - bb[0]) * (bb[3] - bb[1]) <= 4: wobble.append((f, bb))
        elif bb: diff.append((f, bb))
    print(f"比べた写真: {len(names)} / 違う: {len(diff)} / 片方に無い: {len(missing)} / 1画素のゆれ（無視）: {len(wobble)}")
    for f, bb in diff: print("  差", f, bb)
    for f in missing: print("  無し", f)
    return 1 if diff or missing or not names else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("names", nargs="*")
    ap.add_argument("--ref")
    ap.add_argument("--shots")
    ap.add_argument("--compare", nargs=2)
    ap.add_argument("-v", "--verbose", action="store_true")
    ap.add_argument("--sp", action="store_true", help="スマホ幅だけ")
    ap.add_argument("--zoom", help="文字サイズ Aa の倍率（1.15 / 1.3）")
    a = ap.parse_args()
    sys.exit(run_compare(*a.compare) if a.compare else run_check(a))
