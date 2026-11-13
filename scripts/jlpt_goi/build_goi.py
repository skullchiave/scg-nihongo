"""JLPT 語彙ドリル（jlpt/N?_goi.html）を組み立てる。
  語のデータ: scripts/jlpt_goi/<lv>_words.txt   … 番号 / しゅるい / 語（字ごとのルビ {銀|ぎん}{行|こう}） / 英語 / にている語の印（無くてよい）
  よみ方に出さない語: scripts/jlpt_goi/<lv>_noyomi.txt … 読みが2つ以上あって、文脈が無いと決まらない語
  型        : scripts/jlpt_goi/goi.tmpl.html     … 画面と動き。見た目の土台は jlpt/N4_bunpou.html の <style> をそのまま写す
  使い方    : py -X utf8 scripts/jlpt_goi/build_goi.py n4          （リポの一番上で）
  ★出力の HTML は手で直さない。直すのは 語のデータ（タブ区切りの .txt）か型。直したらこの道具を回す。
  よみ方のまちがいの選択肢: scripts/jlpt_goi/<lv>_yomi.txt … 番号 / まちがい1 / まちがい2 / まちがい3（語ごと。無い語は よみ方の問題に出さない）
  訳を足す時: <lv>_words.<言語>.txt（番号<TAB>訳）を置くと、その言語を意味に入れる（型の LANGS にも言語を足す）。
  番号は語ごとに1つ（重ねない）。Claude が足した行は「50+」のように、前の行の番号に + を付ける。"""
import sys, re, json, os, glob, collections
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(HERE))
lv = sys.argv[1].lower(); LV = lv.upper()
RB = re.compile(r'\{([^|{}]+)\|([^{}]+)\}')
rows = [l.split('\t') for l in open(os.path.join(HERE, lv + '_words.txt'), encoding='utf-8').read().splitlines() if l.strip()]
extra = {}
for f in glob.glob(os.path.join(HERE, lv + '_words.*.txt')):
    code = os.path.basename(f).split('.')[1]
    extra[code] = dict(l.split('\t')[:2] for l in open(f, encoding='utf-8').read().splitlines() if l.strip())
# よみ方の問題に出さない語：<lv>_noyomi.txt（番号<TAB>語<TAB>ほかの読み）＋ 同じ表記で読みがちがう語（自動）
noyomi = set(); f = os.path.join(HERE, lv + '_noyomi.txt')
if os.path.exists(f):
    for l in open(f, encoding='utf-8').read().splitlines():
        if l.strip() and not l.startswith('#'):
            c = l.split('\t'); hit = [r for r in rows if r[0] == c[0]]
            assert len(hit) == 1 and RB.sub(r'\1', hit[0][2]) == c[1], ('noyomi の番号と語が合わない', l)
            noyomi.add(c[0])
yomi = collections.defaultdict(set)
for r in rows: yomi[RB.sub(r'\1', r[2])].add(RB.sub(r'\2', r[2]))
# よみ方のまちがいの選択肢（語ごと）：<lv>_yomi.txt（番号<TAB>まちがい1<TAB>まちがい2<TAB>まちがい3）。無い語は よみ方の問題に出さない
#   決まり＝正解・その語の別の読みと同じにしない／{ } の外の字（送りがな など）は正解と同じ位置に同じ字／漢字の所は ひらがなだけ
ydist = {}; f = os.path.join(HERE, lv + '_yomi.txt'); byno = {r[0]: r for r in rows}
assert len(byno) == len(rows), '番号が重なっている'
if os.path.exists(f):
    for l in open(f, encoding='utf-8').read().splitlines():
        if not l.strip() or l.startswith('#'): continue
        c = l.split('\t'); assert len(c) >= 4 and c[0] in byno and c[0] not in ydist, ('yomi の行', l)
        w = byno[c[0]][2]; ok = RB.sub(r'\2', w); ds = c[1:4]
        shape = re.compile(''.join('[ぁ-ん]+' if i % 3 else re.escape(x) for i, x in enumerate(RB.split(w)) if i % 3 != 2))
        assert len(set(ds + [ok])) == 4, ('yomi 同じ読みがある', l)
        for d in ds:
            assert shape.fullmatch(d), ('yomi 送りがなが正解とちがう', l, w)
            assert d not in yomi[RB.sub(r'\1', w)], ('yomi その語の別の読み', l)
        ydist[c[0]] = ds
# 文の問題（空所に入る語をえらぶ）：<lv>_cloze.txt（番号<TAB>例文<TAB>まちがい1<TAB>まちがい2<TAB>まちがい3<TAB>その文での意味（英語））。
#   例文は【 】の中が正解。1語に何行あってもよい（意味・使う形ごとに1行）。例文がある語は「いみ」「ことば」では出さず、文の問題で出す。
#   その文での意味の訳：<lv>_cloze.<言語>.txt（番号<TAB>その語の中で何行目か（1から）<TAB>訳）。無ければ英語で出る。
cloze = collections.defaultdict(list); f = os.path.join(HERE, lv + '_cloze.txt')
if os.path.exists(f):
    for l in open(f, encoding='utf-8').read().splitlines():
        if not l.strip() or l.startswith('#'): continue
        c = l.split('\t'); assert len(c) == 6 and c[0] in byno and all(x.strip() for x in c), ('cloze の行', l)
        ans = re.findall(r'【([^】]*)】', c[1]); assert len(ans) == 1 and ans[0].strip(), ('cloze 【 】は1組', l)
        assert len(set(c[2:5] + ans)) == 4, ('cloze 同じ選択肢がある', l)
        for x in c[1:5]: assert not re.search(r'[一-龥]', RB.sub('', x)), ('cloze ルビの無い漢字', l)
        cloze[c[0]].append([c[1], c[2], c[3], c[4], {'en': c[5].strip()}])
    for g in glob.glob(os.path.join(HERE, lv + '_cloze.*.txt')):
        code = os.path.basename(g).split('.')[1]
        for l in open(g, encoding='utf-8').read().splitlines():
            if not l.strip() or l.startswith('#'): continue
            no, k, tr = l.split('\t')[:3]; assert no in cloze and 1 <= int(k) <= len(cloze[no]), ('cloze の訳の行', code, l)
            cloze[no][int(k) - 1][4][code] = tr
data = []; keys = collections.Counter(); order = 'VSIANKFX'; nny = 0
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
    ny = no in noyomi or len(yomi[RB.sub(r'\1', w)]) > 1; nny += ny
    yd = None if ny else ydist.get(no)
    cz = [z[:4] + [z[4] if len(z[4]) > 1 else z[4]['en']] for z in cloze.get(no, [])]
    data.append((order.index(cat), [cat, w, m if len(m) > 1 else en.strip()] + ([tag, 1 if ny else 0, yd, cz] if cz else [tag, 0, yd] if yd else [tag, 1] if ny else [tag] if tag else [])))
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
for code, d in extra.items():
    assert not set(d) - set(byno), ('訳の番号が語のデータに無い', code, sorted(set(d) - set(byno))[:5])
    print('  訳', code, len([n for n in byno if d.get(n)]), '/', len(rows), '（無い語は英語で出る）')
print(p, len(data), '語', collections.Counter(d[0] for d in data), '言語', ['en'] + sorted(extra), 'よみ方に出さない語', nny, 'よみ方の選択肢がある語', sum(1 for d in data if len(d) > 5))
