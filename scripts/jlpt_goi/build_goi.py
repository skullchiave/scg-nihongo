"""JLPT 語彙ドリル（jlpt/N?_goi.html）を組み立てる。
  語のデータ: scripts/jlpt_goi/<lv>_words.txt   … 番号 / しゅるい / 語（字ごとのルビ {銀|ぎん}{行|こう}） / 英語 / にている語の印（無くてよい）
  型        : scripts/jlpt_goi/goi.tmpl.html     … 画面と動き。見た目の土台は jlpt/N4_bunpou.html の <style> をそのまま写す
  使い方    : py -X utf8 scripts/jlpt_goi/build_goi.py n4          （リポの一番上で）
  ★出力の HTML は手で直さない。直すのは 語のデータ（タブ区切りの .txt）か型。直したらこの道具を回す。
  訳を足す時: <lv>_words.<言語>.txt（番号<TAB>訳）を置くと、その言語を意味に入れる（型の LANGS にも言語を足す）。"""
import sys, re, json, os, glob, collections
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(HERE))
lv = sys.argv[1].lower(); LV = lv.upper()
RB = re.compile(r'\{([^|{}]+)\|([^{}]+)\}')
rows = [l.split('\t') for l in open(os.path.join(HERE, lv + '_words.txt'), encoding='utf-8').read().splitlines() if l.strip()]
extra = {}
for f in glob.glob(os.path.join(HERE, lv + '_words.*.txt')):
    code = os.path.basename(f).split('.')[1]
    extra[code] = dict(l.split('\t')[:2] for l in open(f, encoding='utf-8').read().splitlines() if l.strip())
data = []; keys = collections.Counter(); order = 'VSIANKFX'
for r in rows:
    assert len(r) in (4, 5), r
    no, cat, w, en = r[:4]; tag = r[4] if len(r) == 5 else ''
    assert cat in order and en.strip(), r
    for b, y in RB.findall(w): assert re.fullmatch(r'[一-龥々]+', b) and re.fullmatch(r'[ぁ-ん]+', y), ('ルビ', r)
    assert not re.search(r'[一-龥]', RB.sub('', w)), ('ルビの無い漢字', r)
    keys[RB.sub(r'\1', w) + '/' + RB.sub(r'\2', w)] += 1
    m = {'en': en.strip()}
    for code, d in extra.items():
        if d.get(no): m[code] = d[no]
    data.append((order.index(cat), [cat, w, m if len(m) > 1 else en.strip()] + ([tag] if tag else [])))
assert not [k for k, n in keys.items() if n > 1], [k for k, n in keys.items() if n > 1]
data = [d for _, d in sorted(data, key=lambda x: x[0])]          # しゅるいごとにまとめる（中の順は TSV のまま）
base = open(os.path.join(ROOT, 'jlpt', 'N4_bunpou.html'), encoding='utf-8').read()
css = base[base.index('<style>') + 7: base.index('</style>')].strip('\n')
t = open(os.path.join(HERE, 'goi.tmpl.html'), encoding='utf-8').read()
js = '[\n' + ',\n'.join(json.dumps(d, ensure_ascii=False) for d in data) + '\n]'
out = t.replace('/*__BASECSS__*/', css).replace('/*__DATA__*/', js).replace('__LV__', LV).replace('__lv__', lv)
assert '__' not in re.sub(r'__drillLog|__jlptStudy', '', out), '置きかえ残り'
p = os.path.join(ROOT, 'jlpt', LV + '_goi.html')
open(p, 'w', encoding='utf-8', newline='\n').write(out)
print(p, len(data), '語', collections.Counter(d[0] for d in data), '言語', ['en'] + sorted(extra))
