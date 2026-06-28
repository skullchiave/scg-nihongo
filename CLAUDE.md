# CLAUDE.md — SCG日本語ドリル 開発メモ（次セッションの自分/他AIへ）

このファイルは「会話の記憶が消えても作業を再開できる」ための正本。コードと一緒に GitHub に残る。
ユーザー＝日本語学校の教員（非エンジニア・アーキテクト）。コードは書かないが構造判断は的確。

## これは何
- 日本語学校の授業用ドリル集。GitHub Pages で公開し、**教室プロジェクター投影＋学生スマホ**の両方で使う。
- 公開URL（学生に配る唯一の入口）: **https://skullchiave.github.io/scg-nihongo/**
- リポジトリ（**正本＝GitHub**）: `skullchiave/scg-nihongo`（public）。ローカルの clone 先はマシンで異なる（自宅: `Desktop\0.4 claude-drills`）。複数拠点では GitHub を介して同期する（下記「作業場所・同期」）。

## ⚠ 最重要ルール（事故防止）
- **`index.html` は手編集が正本**（2026-06-15〜）。ロゴ・ラベル・CSS を直接書いてある。
- **`scratch/_RETIRED_build_index.py` は絶対に実行しない**（旧 index.html 生成スクリプト。実行すると手編集が消える。実行ガード入り）。ドリル追加は下記「ドリルの足し方」で index.html を直接編集する。
- ユーザーが手編集を始めた本番ファイルは再生成しない／勝手に作り直さない。危険操作（削除・上書き・外部影響）は事前確認。

## ファイル構成
- `index.html` … 母艦ポータル（**正本・手編集**）。冒頭に `DATA`（カード定義）、ヘッダーに学校ロゴ、ハッシュルーティング（`#/textbook/tsunagu` 等）。
- `tsunagu/*.html` … つなぐにほんご ドリル本体8本（各HTML自己完結・外部依存なし）。L7-1/L7-2/L7-3/L8-1_ta/L8-1_nakatta/L8-2_keiyou/L8-2_matome/L9。
- `logo-school.png`（横ロゴ＝ホーム下）, `logo-mark.png`（ブロブ＝ヘッダー左）, `icon-*.png`（PWAアイコン）, `manifest.webmanifest`, `.nojekyll`（必須・無いとPagesがREADMEをindex化）。
- `_original/` … 投影用の原本HTML8本（触らず温存・参照のみ）。
- `fonts/BIZUDPGothic-{Regular,Bold}.subset.woff2` … 本文フォント（**自己ホスト・追跡する**）。下記「字体」参照。
- `scratch/` `tmp/` … 実験・一時（**git追跡しない**＝GitHubに上がらない）。検証スクリプトはここ。
- `README.md` … 公開URL・構成・公開方針の概要。`CLAUDE.md`（本書）… 開発・運用の詳細。

## ドリルの足し方（データ駆動）
`index.html` 冒頭の `DATA.drills` に1行足す：
```js
{tb:'tsunagu', lesson:'L7', label:'ない<ruby>形<rt>けい</rt></ruby>', file:'tsunagu/L7-2.html', ready:true},
```
`ready:false`＝「じゅんびちゅう」（押せない）。HTMLを作って `ready:true` で公開。将来カテゴリ用に `general/`(ドリル) `quiz/`(問題) フォルダを予定。

## ドリル本体の作り（8本共通）
- 4モード構成: ①ルール(rule) ②めくり(flip) ③並べ替え/おわり(sort) ④リズム(rhythm)。タブ`show(id)`で画面切替（タブは履歴に含めない）。
- **リズムの「じどう送り」（2026-06-29〜・8本共通）**: リズム画面に `▶ じどう`＋速度3段 `おそい(5s)/ふつう(3s)/はやい(1s)`（既定ふつう）。ONで等間隔に`rStep`自動実行（問題↔答えを刻む）。じどう中の画面タップ＝一時停止/再開、OFF時は従来の手動めくり。`show()`がリズム以外への切替で`rSetAuto(false)`し裏で回り続けないようにする。**新規ドリルにもこのコントロール一式（HTML `#rauto`＋CSS `.rauto/.rplay/.rspd`＋JS `rSetAuto`機構）を必ず含める**。一括追加は `scratch/patch_rhythm_autoplay.py` 参照（アンカー: `.rcount`ルール / `rcount`div / `rhythmarea onclick` / `show()`）。
- 1ファイルで投影/スマホ両対応: `@media(max-width:640px)` ＋ `clamp()` ＋ `100dvh`。スマホでナビは2×2、③の選択肢はgrid。
- ナビ左上: `🏠 ホーム`(`../`でポータルへ) ＋ `◀もどる`/`すすむ▶`（`history.back()/forward()`＝PWAでブラウザ戻りが無い対策）。

## 命名規約（日本語教育の用語に準拠）
- 形容詞は「い形容詞／な形容詞」。表示は「い・な形容詞」。
- L7-3＝**い・な形容詞の普通形①**（現在）、L8-2＝**い・な形容詞・名詞の過去 普通形②**（過去）。①②でペア。
- 「なかった形」とは言わない→ラベルは「なかった」。
- ③の結合ボタンは「た/て」を大きく＋「（2・3グループ）」を小さい2行（2・3グループはおわりが同じなので1ボタン。判定は `data-e` で「おわり」のみ）。

## iOS文字はみ出し対策（めくりカード）
- 原因＝iOS Safari の文字自動拡大(font boosting)。`-webkit-text-size-adjust:100%` を **html(root)** に付与して抑止。
- 加えて保険の自動縮小JS（`.fitwrap`＋MutationObserver/IntersectionObserver、はみ出したら `transform:scale` で縮める）。flipDealは触らず汎用。**iOS実機はこの環境で再現不可→最終確認はユーザーのiPhone**。

## 検証手順（ヘッドレスChrome＋scratch）
```
"C:/Program Files/Google/Chrome/Application/chrome.exe" --headless=new \
  --remote-debugging-port=9222 --remote-allow-origins=* \
  --user-data-dir="<repoフォルダ>/tmp/headless-profile" about:blank &
python scratch/<撮影・計測スクリプト>.py     # CDP経由でfile:///を撮影・DOM計測
taskkill //F //IM chrome.exe
```
- `--remote-allow-origins=*` 必須（無いとCDPが403）。`show('flip')` 等でタブ切替して撮る。
- 一括パッチは `scratch/patch_*.py`（8本共通構造にアンカー置換）。試作・スクショは scratch/ に閉じ込める。

## 作業場所・同期（複数拠点）
- **正本は GitHub**（`skullchiave/scg-nihongo`）。複数のPC/拠点で作業するなら **git clone / pull / push で同期**する。GitHub が単一の真実。
- ⚠ **`.git` を含むこのフォルダを Google Drive 等のクラウド同期フォルダに置かない**。クラウド同期が `.git` 内部を file 単位で同期して破損する典型事故。バックアップ目的なら GitHub が既にそれ。
- 自宅 clone: `Desktop\0.4 claude-drills`。職場PCは別パスに `git clone` する。`scratch/` `tmp/` は同期不要（gitignore済だが、クラウド同期は gitignore を無視するので特に注意）。

## デプロイ
ローカルで編集 → `git add` → `git commit` → `git push`。GitHub Pages が数十秒〜1分で反映。コミットemailはnoreply化済。

## オフライン対応（Service Worker・2026-06-15〜）
通信節約＋オフライン動作のため、`sw.js`（site全体・scope `/scg-nihongo/`）。各HTMLは `</body>` 直前のインライン1スニペットで登録。
- **方式**: ドリル本体＝**stale-while-revalidate**（キャッシュを即返して速さ・オフラインを確保しつつ、オンラインなら裏で最新を取得しキャッシュを差し替え→次に開くと自動で新版）。`index.html`＝**network-first**。
- **自動更新＋通信節約の両立**: 背景の再取得は `cache:'no-cache'`（条件付き再検証）。中身が変わってなければ **304でほぼ通信ゼロ**、変わった時だけ実DL。GitHub Pages の ETag が効く。
- **運用**: 学生は学校Wi-Fiで一度開く→圏外でもギガ消費なしで反復。ドリルを直して push すれば、学生が次にオンラインで開いた時に自動で新版へ。
- ⚠ **基本 `CACHE='scg-vN'` の版上げは不要**（内容はSWRで自動更新）。版を上げるのは「キャッシュ方式そのものを変えた／壊れたキャッシュを全員から強制破棄したい」時だけ（activateで旧キャッシュ削除）。現在 `scg-v2`。
- ドリルを**増やす**ぶんも sw.js 編集不要（開かれたものを自動キャッシュ・自動更新）。
- 検証: ローカルを `/scg-nihongo/` ベースで serve（junction）→ headless Chrome＋CDP（Node内蔵WebSocket、`tmp/sw_test.mjs` の prime/update/offline 3フェーズ）。**サーバを実際に落として**「キャッシュ済＝開ける／未キャッシュ＝失敗」、**ファイルにマーカー注入→オンライン再訪で差し替わる**ことを実測（CDPの offline エミュレーションは localhost に効かない／背景fetchは `no-cache` でないとHTTPキャッシュの旧版を掴む）。

## その他の学生向け仕様（2026-06-15〜）
- **本文は選択可・カード/操作部は選択不可**（`user-select`）。狙い＝学生が分からない語を長押し→コピー→翻訳アプリに渡せるようにしつつ、タップ誤選択は防ぐ。`</style>` 直前のCSSで上書き。
- **利用記録（端末ローカル・表示なし）**: `localStorage['drill_stats']` に各ドリルの `opens/last`（＋将来用に `correct/total` と `window.__drillLog(ok)` フック）を貯める。ログイン不要・サーバー無し・名簿無し。**今は表示UIなし**（記録を貯めるだけ。将来「🔥連続」等を出すなら配線する）。

## 字体（BIZ UDPGothic 自己ホスト・2026-06-16〜）
- **なぜ**: 旧 `Yu Gothic` 等のゴシックは き・さ・ふ 等のはらいが繋がり、学習者が手で書く形と違う（「繋ぎ字」問題）。教育用UDフォント **BIZ UDPGothic**（Morisawa, OFL）に変更。き・さ等が学習向けに分離し、太く明快で投影・小画面の視認性も高い。
- **自己ホストの理由**: 学生スマホ（iPhone/Android）に教育フォントは入っていない＋本サイトはオフラインSW対応。CDN依存だと圏外で游ゴシックに戻る。→ `fonts/` に woff2 同梱し SW(`SHELL`)でプリキャッシュ。
- **読み込み**: 全HTML（index＋tsunagu/8本）の `<style>` 冒頭に `@font-face`（400/700, パスは**絶対** `/scg-nihongo/fonts/...`＝深さ非依存・アイコンと同流儀）。`body` の font-family 先頭に `"BIZ UDPGothic"` を追加（既存スタックはフォールバックで温存）。weight 800/900 は最寄りの 700 face を使う。
- **サブセット**: 常用漢字＋全ひらがな/カタカナ/ASCII/記号＋現ドリルの全使用文字（計~3800グリフ）で各~490KB。元TTF（~4.6MB×2）と中間物は `tmp/`（非追跡）。
- **新ドリルで常用外の漢字を使った時だけ**サブセット再生成が要る（フォールバックで游ゴシック表示になり字体が混ざる）。再生成手順:
  ```
  # tmp/ に BIZUDPGothic-{Regular,Bold}.ttf を置く（公式: googlefonts/morisawa-biz-ud-gothic）
  pip install fonttools brotli
  # subset_text.txt = 常用漢字 + 全HTMLの使用文字、を用意して:
  python -m fontTools.subset tmp/BIZUDPGothic-Regular.ttf --text-file=tmp/subset_text.txt \
    --unicodes="U+0020-007E,U+00A0-00FF,U+2000-206F,U+2190-21FF,U+2460-24FF,U+25A0-25FF,U+2600-27BF,U+3000-30FF,U+FF00-FFEF" \
    --layout-features='kern,palt,vert,vrt2,liga,calt' --flavor=woff2 --no-hinting --desubroutinize \
    --output-file=fonts/BIZUDPGothic-Regular.subset.woff2   # Bold も同様
  ```
- **検証済**: headless Chrome + CDP で `document.fonts.check('400/700 24px "BIZ UDPGothic"')=true`、両ウェイト loaded、body に適用を実測（2026-06-16）。

## 公開・拡散ガバナンス（ユーザーと合意・要遵守）
- **認証なし開放が正**（中身は無害な文法ドリル＝答案・個人情報・成績は無い）。**答案/名簿/クラス限定情報は開放URLに置かない**（必要なら最初からログイン制の別の場所に作る）。
- **QR表示は投影(PC幅)専用**・スマホ非表示＝再配布に小さな摩擦を残す。
- **合言葉はリアクティブ**: 今は入れない。「拡散がコントロールを離れた」兆候（"他校の子が""広まってる"等）が出たら簡易合言葉＋半年ローテで導入。→ 関連話題が出たら自分から提示する。
- **英語トグルは入れない**（2026-06-13決定・蒸し返さない）。読めなさ対策はふりがな＋やさしい日本語＋自明UIで全員に効かせる。

詳細な意思決定の背景はユーザーの記憶（memory: `project_tsunagu_drills`）と git log（日本語コミットに「なぜ」付き）にもある。
