# -*- coding: utf-8 -*-
"""N4 の模試の問題文に ルビ を付ける（build_mondai.py から使う）。2026-11-24 きあ決定。

決まり:
  - N5 の漢字（assets/jlpt-kanji.js の n4 の先頭80字）だけの語には付けない。それ以外の漢字が入る語に付ける
    （本番の模試 SUCCESS N4 に近い形。やさしい字＝人・来・話・読 などはそのまま）。
  - 答えにかかわる所には付けない：漢字読みの【 】・表記の【 】・用法の【 】、漢字読みと表記の選択肢。
  - 書き方は ドリルと同じ {漢字|よみ}（ページが <ruby> にする）。

読みは pykakasi で付け、Claude が確かめた（n4_ruby_checked.txt＝確かめた 漢字<TAB>よみ の組）。
  確かめ方（2026-11-24）：①718組を例1つずつ ②1字の語は「漢字・よみ・送りがなの1字目」ごと（964組）に例を3つまで
  ③読みが文で変わる字（開・空・通・止・方 など）は全部の文。①だけだった時に「まどを開（ひら）けました」を見落とした
  （道具がいつも同じ読みを付ける字は①に出てこない）＝新しい字が増えたら②③もやる。
まちがっていた読みは n4_ruby_fix.txt で直す（1行＝ 道具が付けた形<TAB>直した形。前後の字を含めてよい。
  re: で始まる行は正規表現）。
問題が直されて、まだ確かめていない組が出てきたら、build_mondai.py が数と語を出す
  → 前後を見て、まちがいなら fix に足し、checked に足す。
"""
import os, re

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..'))
KAN = re.compile(r'[一-鿿々〆]')
PIECE = re.compile(r'[一-鿿々〆]+|[^一-鿿々〆]+')


def n5_kanji():
    js = open(os.path.join(REPO, 'assets', 'jlpt-kanji.js'), encoding='utf-8').read()
    n4 = re.search(r"n4:\s*'([^']+)'", js).group(1)
    # 先頭80字が N5（JLPT Sensei の並び。80字目＝雨、81字目＝会 から N4）
    if not (n4[79] == '雨' and n4[80] == '会'):
        raise SystemExit('止めました：jlpt-kanji.js の n4 の並びが変わっています（N5 の80字を取り出せない）')
    return set(n4[:80])


def _hira(s):
    return ''.join(chr(ord(c) - 0x60) if 'ァ' <= c <= 'ヶ' else c for c in s)


def _load_tsv(name):
    p = os.path.join(HERE, name)
    out = []
    if os.path.isfile(p):
        for line in open(p, encoding='utf-8'):
            line = line.rstrip('\n')
            if line and not line.startswith('#'):
                out.append(line.split('\t'))
    return out


class Ruby:
    def __init__(self):
        try:
            import pykakasi
        except ImportError:
            raise SystemExit('止めました：pykakasi が要ります（py -m pip install pykakasi）')
        self.kks = pykakasi.kakasi()
        self.n5 = n5_kanji()
        self.fix = [(a, b) for a, b in _load_tsv('n4_ruby_fix.txt')]
        self.checked = {(r[0], r[1]) for r in _load_tsv('n4_ruby_checked.txt') if len(r) >= 2}
        self.seen = {}        # (漢字, よみ) -> [回数, 例の番号]
        self.unaligned = {}   # 読みと字を合わせられなかった所 -> [回数, 例]

    def _plain(self, s, qid):
        segs = self.kks.convert(s)
        if ''.join(x['orig'] for x in segs) != s:
            self.unaligned.setdefault('(区切りが合わない) ' + s[:20], [0, qid])[0] += 1
            return s
        res = []
        for x in segs:
            o, h = x['orig'], x['hira']
            if not KAN.search(o):
                res.append(o)
                continue
            pieces = PIECE.findall(o)
            pat = ''.join('(.+?)' if KAN.match(p) else re.escape(_hira(p)) for p in pieces)
            m = re.fullmatch(pat, h)
            if not m:
                if any(c not in self.n5 for c in o if KAN.match(c)):
                    self.unaligned.setdefault(o + '→' + h, [0, qid])[0] += 1
                res.append(o)
                continue
            g = 0
            for p in pieces:
                if KAN.match(p):
                    g += 1
                    if any(c not in self.n5 for c in p):
                        r = m.group(g)
                        k = self.seen.setdefault((p, r), [0, qid]); k[0] += 1
                        res.append('{%s|%s}' % (p, r))
                    else:
                        res.append(p)
                else:
                    res.append(p)
        return ''.join(res)

    def text(self, s, qid, protect=False):
        """protect＝【 】の中には付けない。"""
        out = []
        for part in re.split(r'(【[^】]*】)', s):
            if part.startswith('【') and protect:
                out.append(part)
            elif part:
                out.append(self._plain(part, qid))
        r = ''.join(out)
        for a, b in self.fix:   # まちがった読みを直す（ルビ付きの形で置きかえ。re: で始まる行は正規表現）
            r = re.sub(a[3:], b, r) if a.startswith('re:') else r.replace(a, b)
        return r

    def unchecked(self):
        return {k: v for k, v in self.seen.items() if k not in self.checked}


def apply(q, form, rb):
    """q＝[番号, 形式, ★, 対象, 問題文, [選択肢], 正答, 並び, 解説] を書きかえる。"""
    qid = q[0]
    if form in ('漢字読み', '表記'):
        # 字そのものを問う問題：選択肢と解説には付けない（解説に まちがいの選択肢の字＝実在しない語 が出てくるため）
        q[4] = rb.text(q[4], qid, protect=True)
        return q
    if form == '用法':
        q[5] = [rb.text(c, qid, protect=True) for c in q[5]]   # 問題文＝【語】だけ
    else:
        q[4] = rb.text(q[4], qid)
        q[5] = [rb.text(c, qid) for c in q[5]]
    q[8] = rb.text(q[8], qid)
    return q
