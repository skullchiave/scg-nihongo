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

## 公開・拡散ガバナンス（ユーザーと合意・要遵守）
- **認証なし開放が正**（中身は無害な文法ドリル＝答案・個人情報・成績は無い）。**答案/名簿/クラス限定情報は開放URLに置かない**（必要なら最初からログイン制の別の場所に作る）。
- **QR表示は投影(PC幅)専用**・スマホ非表示＝再配布に小さな摩擦を残す。
- **合言葉はリアクティブ**: 今は入れない。「拡散がコントロールを離れた」兆候（"他校の子が""広まってる"等）が出たら簡易合言葉＋半年ローテで導入。→ 関連話題が出たら自分から提示する。
- **英語トグルは入れない**（2026-06-13決定・蒸し返さない）。読めなさ対策はふりがな＋やさしい日本語＋自明UIで全員に効かせる。

詳細な意思決定の背景はユーザーの記憶（memory: `project_tsunagu_drills`）と git log（日本語コミットに「なぜ」付き）にもある。
