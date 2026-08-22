# -*- coding: utf-8 -*-
"""
ドリルの型（テンプレート＋定義 → 自己完結HTML生成）
====================================================
思想: 21本の自己完結HTMLに複製されている共通エンジン（4モード・じどう送り・自動縮小・
フォント・SW登録…）を「骨格」として1本のテンプレートに固定し、課ごとに違う部分
（タイトル・タブ名・ルール画面・語彙データ）だけを「スロット」として定義ファイルに持つ。
新ドリル＝定義ファイルを書くだけ。配布物は従来どおり完全自己完結の単一HTML（変更なし）。

品質保証: 既存ドリルを定義から**バイト一致で再生成**できること（tests/test_build_drill.py）。
バイト一致＝挙動同一の保証。骨格を直したら全 golden が緑のままか必ず確認する。

使い方:
  python scripts/build_drill.py make-template   # 基準2本から骨格を再抽出（骨格を変えた時だけ）
  python scripts/build_drill.py extract tsunagu/L23-1_meirei.html   # 既存ドリル → 定義ファイル
  python scripts/build_drill.py build drill_defs/L19-1_kanou.json -o tmp/preview.html
  python scripts/build_drill.py check           # 全定義を再生成して実ファイルとバイト比較

新ドリルの手順: 一番近い形の定義 json をコピー → スロット（タイトル/ルールHTML/データ）を
書き換え → build -o tmp/ でプレビュー検証 → tsunagu/ へ出力 → index.html に2行（drills/updates）。
★生成したドリルを後から手直しした時は、必ず extract で定義に反映し check を緑に保つ
（定義と実ファイルがズレたまま放置＝型の腐り。check が検知する）。
"""
import sys, os, json, difflib, io

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE = os.path.join(ROOT, "template", "drill_std.tmpl.html")
DEFS_DIR = os.path.join(ROOT, "drill_defs")
BASE_A = os.path.join(ROOT, "tsunagu", "L19-1_kanou.html")
# 骨格の変数域は「基準×各参照」の差分の和集合。参照＝標準形（動詞活用・グループ3択）の同世代群。
# L7系など旧世代（ルール画面の構造ごと違う）は型の適用外＝既存のまま据え置き。
REFS = ["L27-3_shieki", "L19-3_ukemi", "L14-2_nakereba", "L29-1_shiekiukemi",
        "L23-1_meirei", "L13-3_ikou", "L14-2_jouken", "L8-1_ta", "L8-1_nakatta", "L9"]
MARK = "<<<SLOT{:02d}>>>"
MERGE_GAP = 8   # 差分同士がこの行数以内なら1スロットに束ねる（骨格アンカーを短くしすぎない）

def read_lines(p):
    with io.open(p, encoding="utf-8", newline="") as f:
        return f.read().split("\n")

def write_text(p, text):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with io.open(p, "w", encoding="utf-8", newline="") as f:
        f.write(text)

def make_template():
    a = read_lines(BASE_A)
    var_lines = set()
    fitted_refs = []
    for ref in REFS:
        b = read_lines(os.path.join(ROOT, "tsunagu", ref + ".html"))
        sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
        ratio = sm.ratio()
        if ratio < 0.80:   # 構造ごと違う旧世代は骨格を壊すので参照に使わない
            print(f"  （参照外: {ref} 類似度{ratio:.2f}＝別構造）")
            continue
        fitted_refs.append(ref)
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag != "equal":
                var_lines.update(range(i1, i2))
    var_ranges = []
    for i in sorted(var_lines):
        if var_ranges and i == var_ranges[-1][1]:
            var_ranges[-1][1] = i + 1
        else:
            var_ranges.append([i, i + 1])
    # 近い範囲を束ねる
    merged = []
    for r in var_ranges:
        if merged and r[0] - merged[-1][1] <= MERGE_GAP:
            merged[-1][1] = r[1]
        else:
            merged.append(r)
    out, slots, pos = [], [], 0
    for n, (s, e) in enumerate(merged, 1):
        out.extend(a[pos:s])
        out.append(MARK.format(n))
        slots.append((n, s, e))
        pos = e
    out.extend(a[pos:])
    write_text(TEMPLATE, "\n".join(out))
    # 基準＋適合した参照の定義も同時に出力（golden の種）
    for name in [os.path.splitext(os.path.basename(BASE_A))[0]] + fitted_refs:
        try:
            extract(os.path.join(ROOT, "tsunagu", name + ".html"))
        except SystemExit as e:
            print(f"  （{name}: 抽出不可 → 型の適用外）")
    print(f"テンプレート生成: {os.path.relpath(TEMPLATE, ROOT)}（スロット {len(merged)} 個）")
    for n, s, e in slots:
        first = a[s].strip()[:60]
        print(f"  SLOT{n:02d}: L19-1 の {s+1}〜{e}行目  例) {first}")

def template_parts():
    t = read_lines(TEMPLATE)
    parts, cur = [], []
    for line in t:
        if line.startswith("<<<SLOT") and line.endswith(">>>"):
            parts.append(("skel", cur)); cur = []
            parts.append(("slot", line.strip("<>").replace("SLOT", "")))
        else:
            cur.append(line)
    parts.append(("skel", cur))
    return parts

def extract(drill_path):
    """既存ドリル → 定義 json。骨格行が順番どおり見つからなければ骨格ドリフトとして明示エラー。"""
    tgt = read_lines(drill_path)
    parts = template_parts()
    pos, slots = 0, {}
    it = iter(range(len(parts)))
    i = 0
    while i < len(parts):
        kind, val = parts[i]
        if kind == "skel":
            for k, line in enumerate(val):
                if pos >= len(tgt) or tgt[pos] != line:
                    raise SystemExit(
                        f"★骨格ドリフト: {os.path.basename(drill_path)} の {pos+1}行目が骨格と不一致\n"
                        f"  骨格: {line[:70]!r}\n  実物: {(tgt[pos] if pos < len(tgt) else '<EOF>')[:70]!r}\n"
                        f"  → このドリルは型の適用外（個別進化している）。取り込むなら骨格側の検討を")
                pos += 1
            i += 1
        else:
            slot_no = val
            # 次の骨格ブロックの先頭行まで（一意に決まる前提。曖昧なら最短一致）
            if i + 1 < len(parts):
                nxt = parts[i + 1][1]
                anchor = next((l for l in nxt if l.strip() != ""), None)
                j = pos
                while j < len(tgt) and tgt[j] != anchor:
                    j += 1
            else:
                j = len(tgt)
            slots["SLOT" + slot_no] = "\n".join(tgt[pos:j])
            pos = j
            i += 1
    name = os.path.splitext(os.path.basename(drill_path))[0]
    out = os.path.join(DEFS_DIR, name + ".json")
    write_text(out, json.dumps({"name": name, "out": f"tsunagu/{name}.html", "slots": slots},
                               ensure_ascii=False, indent=1))
    print(f"定義を抽出: {os.path.relpath(out, ROOT)}")
    return out

def build(def_path, out_path=None):
    d = json.load(io.open(def_path, encoding="utf-8"))
    lines = []
    for kind, val in template_parts():
        if kind == "skel":
            lines.extend(val)
        else:
            content = d["slots"]["SLOT" + val]
            if content != "":
                lines.extend(content.split("\n"))
    html = "\n".join(lines)
    out = out_path or os.path.join(ROOT, d["out"])
    write_text(out, html)
    print(f"生成: {os.path.relpath(out, ROOT)}")
    return html

def check():
    ok = ng = 0
    for f in sorted(os.listdir(DEFS_DIR)):
        if not f.endswith(".json"):
            continue
        d = json.load(io.open(os.path.join(DEFS_DIR, f), encoding="utf-8"))
        target = os.path.join(ROOT, d["out"])
        lines = []
        for kind, val in template_parts():
            if kind == "skel":
                lines.extend(val)
            else:
                content = d["slots"]["SLOT" + val]
                if content != "":
                    lines.extend(content.split("\n"))
        built = "\n".join(lines)
        actual = io.open(target, encoding="utf-8", newline="").read()
        if built == actual:
            ok += 1; print(f"  OK  {f} == {d['out']}（バイト一致）")
        else:
            ng += 1
            sm = difflib.unified_diff(actual.split("\n"), built.split("\n"), "実物", "再生成", lineterm="", n=1)
            head = "\n".join(list(sm)[:12])
            print(f"  ★NG {f}: 再生成が実物と不一致（定義かテンプレの反映漏れ）\n{head}")
    print(f"check: {ok} OK / {ng} NG")
    return ng == 0

if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        print(__doc__); sys.exit(0)
    cmd = args[0]
    if cmd == "make-template":
        make_template()
    elif cmd == "extract":
        extract(os.path.join(ROOT, args[1]) if not os.path.isabs(args[1]) else args[1])
    elif cmd == "build":
        out = None
        if "-o" in args:
            out = args[args.index("-o") + 1]
        build(os.path.join(ROOT, args[1]) if not os.path.isabs(args[1]) else args[1], out)
    elif cmd == "check":
        sys.exit(0 if check() else 1)
    else:
        print("コマンド: make-template / extract <drill.html> / build <def.json> [-o out] / check")
        sys.exit(2)
