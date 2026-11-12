# -*- coding: utf-8 -*-
"""JLPT 文法ページの分野の表示名を「形が主役・用語は小さく」にする（1回かぎりの書きかえ道具）。
使い方（リポの根で）: py -X utf8 scripts/jlpt_catforms.py
すでに書きかえ済みのページは、CATF の中身だけを下の表で入れ直す。
代表の形を直したいときは下の FORMS を直してもう一度回す。"""
import pathlib, json, re, sys

FORMS = {
 'N4': {
  '条件': '〜ば・〜たら',
  '授受（あげる・くれる・もらう）': '〜てあげる・〜てもらう',
  '推量・様子・伝聞': '〜そうだ・〜ようだ',
  '可能・受身・使役': '〜られる・〜させる',
  'て形の表現': '〜ておく・〜てしまう',
  '意志・予定・決定': '〜ようと{思|おも}う・〜つもりだ',
  '義務・許可・命令': '〜なくてもいい・〜なさい',
  '時間・状態': '〜{間|あいだ}に・〜ながら',
  '程度・比較・難易': '〜すぎる・〜やすい',
  '名詞化・引用・疑問': '〜こと・〜という',
  '接続・副詞': '〜し・〜のに',
  '敬語': 'いらっしゃる・お〜になる',
  'その他': '〜がる・〜{必要|ひつよう}がある',
 },
 'N3': {
  '時間・変化': '〜うちに・〜たとたん',
  '原因・理由・結果': '〜おかげで・〜せいで',
  '推量・判断': '〜に{違|ちが}いない・〜わけだ',
  '様子・たとえ': 'まるで〜ようだ・〜っぽい',
  '程度・限定・強調': '〜ほど・〜さえ',
  '複合動詞': '〜きる・〜{込|こ}む・〜{直|なお}す',
  '逆接・仮定': '〜くせに・たとえ〜ても',
  '関係・観点': '〜について・〜にとって',
  '引用・伝聞・定義': '〜ということだ・〜というのは',
  '決まり・習慣・必要': '〜ことになっている・〜べきだ',
  '話し言葉・縮約': '〜てごらん・〜ずに',
  '敬語': 'お〜です・〜させていただく',
  '副詞・接続詞': '{決|けっ}して〜ない・まさか',
 },
 'N2': {
  '時間・変化': '〜あげく・〜かと{思|おも}ったら',
  '原因・理由・結果': '〜ばかりに・〜からこそ',
  '推量・判断': '〜かねない・〜っこない',
  '様子・たとえ': '〜げ・〜かのように',
  '程度・限定・強調': '〜ばかりか・〜どころか',
  '逆接・仮定・条件': '〜ものの・〜にもかかわらず',
  '関係・観点': '〜から{言|い}うと・〜からして',
  '主張・評価・感情': '〜ことだ・〜ものではない',
  '必要・可能・義務': '〜ざるを{得|え}ない・〜よりほかない',
  '敬語': 'お〜{願|ねが}う',
  '副詞・接続詞': 'あるいは・ちなみに',
 },
 'N1': {
  '時間・変化': '〜が{早|はや}いか・〜なり',
  '原因・理由・目的': '〜ばこそ・〜べく',
  '推量・判断': '〜だろうに・〜ではあるまいか',
  '様子・たとえ': '〜ぶる・〜がましい',
  '程度・限定・強調': '〜だに・〜だの〜だの',
  '逆接・仮定・条件': '〜であれ・〜かと{思|おも}いきや',
  '関係・観点': '〜がてら・〜いかんでは',
  '主張・評価・感情': '〜でなくてなんだろう・〜ほうがましだ',
  '必要・可能・不可能': '〜べからず・〜べくもない',
  '副詞・接続詞': 'あえて・あくまでも',
  '文末表現': '〜さ・〜ってば',
 },
}
ALL = 'ぜんぶ'
OLD_ALL = "'すべての <ruby>分野<rt>ぶんや</rt></ruby>'"
REPL = [  # (前, 後)  どれも1ページに1回だけ出る
 ("const catR = c => CATR[c] ? ruby(CATR[c]) : esc(c);",
  "const catR = c => CATR[c] ? ruby(CATR[c]) : esc(c);\n"
  "// 分野の表示名：学生が見分けられる「形」を主役にし、用語は小さく添える（中身は scripts/jlpt_catforms.py の表）\n"
  "const CATF = __CATF__;\n"
  "const catF = c => CATF[c] ? ruby(CATF[c])+' など' : catR(c);\n"
  "const catL = c => CATF[c] ? '<span class=\"cf\">'+ruby(CATF[c])+' など</span><small class=\"ct\">'+catR(c)+'</small>' : catR(c);"),
 ("""'<option value="">すべての 分野（ぶんや）</option>'+CAT_ORDER.map(c=>`<option value="${esc(c)}">${esc(c)}</option>`)""",
  """'<option value="">""" + ALL + """</option>'+CAT_ORDER.map(c=>`<option value="${esc(c)}">${esc(CATF[c]?plain(CATF[c])+' など':c)}</option>`)"""),
 ('$("catRuby").innerHTML=c?ruby(CATR[c]||c):' + OLD_ALL + ';', '$("catRuby").innerHTML=c?catL(c):\'' + ALL + '\';'),
 ('$("catPill").innerHTML=$("catRuby").innerHTML;', '$("catPill").innerHTML=c?catF(c):\'' + ALL + '\';'),
 ("${k?catR(k):" + OLD_ALL + "}", "${k?catL(k):'" + ALL + "'}"),
 ("<span>${catR(c)}（${xs.length}）</span>", "<span>${catF(c)}<small class=\"ct\">${catR(c)}（${xs.length}）</small></span>"),
 ("<span>この<ruby>分野<rt>ぶんや</rt></ruby>を<ruby>練習<rt>れんしゅう</rt></ruby></span>", "<span>これを<ruby>練習<rt>れんしゅう</rt></ruby></span>"),
 ("""<button data-go="${esc(c)}"${n?"":" disabled"}><span>${catR(c)}</span>""", """<button data-go="${esc(c)}"${n?"":" disabled"}><span>${catL(c)}</span>"""),
 ('<label class="lbl" for="catSel"><ruby>分野<rt>ぶんや</rt></ruby></label>', '<label class="lbl" for="catSel">グループ</label>'),
 ("\n.catruby{margin", "\n.cf{display:block;}\n.ct{display:block;font-size:.72em;font-weight:500;color:var(--sub);line-height:1.8;}\n.catruby{margin"),
]
ok = True
for lv, forms in FORMS.items():
    p = pathlib.Path(f'jlpt/{lv}_bunpou.html'); raw = p.read_bytes().decode('utf-8'); nl = '\r\n' if '\r\n' in raw else '\n'
    s = raw.replace('\r\n', '\n')
    cats = []
    for m in re.finditer(r'^\s*\["([^"]+)","[^"]+",', s, re.M):
        if m.group(1) not in cats and m.group(1) != 'setup': cats.append(m.group(1))
    miss = [c for c in cats if c not in forms]; extra = [c for c in forms if c not in cats]
    if miss or extra: print('★NG', lv, '表に無い分野', miss, '余り', extra); ok = False; continue
    catf = json.dumps(forms, ensure_ascii=False)
    if 'const CATF = ' in s:
        s2 = re.sub(r'const CATF = \{.*?\};', lambda m: 'const CATF = ' + catf + ';', s, count=1); print(lv, '表だけ入れ直し')
    else:
        cnt = [s.count(a) for a, b in REPL]
        if any(c != 1 for c in cnt): print('★NG', lv, '書きかえ箇所の数', cnt); ok = False; continue
        s2 = s
        for a, b in REPL: s2 = s2.replace(a, b.replace('__CATF__', catf))
        print(lv, '書きかえ', len(REPL), '箇所・分野', len(cats))
    p.write_bytes(s2.replace('\n', nl).encode('utf-8'))
sys.exit(0 if ok else 1)
