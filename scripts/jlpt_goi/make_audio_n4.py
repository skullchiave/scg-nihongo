"""★ふだんは回さない。N4 の語の音声（jlpt/audio/n4/kenzaki/）を作った時の道具と、きあが聞きくらべで えらんだ作り方の表（OVR・P10・P11・ACAT）の記録。
  そのまま回すと 全語を作り直す（出力は scratch/20261112-audio/n4_all/＝git の外。本番の jlpt/audio/ には書かない）。きあが聞いた音と 1バイトも変えないために、
  本番の音は作り直さない。読みを変えた語・足した語だけ、ここで作った物を きあが聞いてから jlpt/audio/n4/kenzaki/ と n4_audio.txt に入れる（CLAUDE.md「語の音声」）。
  scratch/20261112-audio/n4_all/marked2.tsv・sample1.txt・check.html（検分の記録。家PCの社用ドライブの clone にだけある）が要る。
  ---- 以下、作った時の説明 ----
  N4 の全語の音声を、11/12 にきあが決めた作り方で作り、検分ページを出す。
  手元の VOICEVOX（127.0.0.1:50021）だけ。話者 21＝剣崎雌雄、速さ 0.85。外には何も送らない。本体（jlpt/ など）には書かない。
  出力: scratch/20261112-audio/n4_all/kenzaki/<番号>.mp3 ・ n4_all/ledger.tsv（台帳）・ n4_all/check.html（検分ページ）
  使い方: py -X utf8 scratch/20261112-audio/make_all.py

  作り方（設計図 2-2・2-2b）
    読み   ：漢字で解析 → 正本のルビと合わなければ かな で解析 → それでも合わなければ ★（人が見る）
    そのまま：終わりが下がる型・1音の語・副詞・あいさつ
    写す   ：名詞・カタカナ語の3音以上（下がらない型）。「〜が」の時の高さを写し、語だけの時の1音目の高さに全体を合わせ、2音目から後を +0.04
    11/13 きあの検分（見本51語で7語に印）から足した決まり：
      ・いちばん高い音を 5.00 までに抑える（そのまま・写す。高低の幅を縮める。縮めるのは 0.6倍まで）＝「語気が強い」の直し
      ・切る語で、最後の音より前が全部 無声の時（月 など）は、最後の音を 4.90 までに
      ・1つの長い音だけの語で 頭が高い型（用 など）は、2音目を 1音目より 0.06 だけ低くして つなげる
      ・FIX＝人が聞いて型を直した語（かな＋アクセント記号）
    切る   ：名詞・カタカナ語の2音＝「〜が」0.12秒／動詞・い形容詞＝「〜の」0.15秒／な形容詞・する名詞＝「〜が」0.15秒
    切る・写す の検査：付けても切れ方と音の並びが変わらない／切った後の最後の母音が無声でない。だめなら そのまま にして ★"""
import os, re, json, subprocess, urllib.request, urllib.parse, html, copy, collections, random
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, 'scratch', '20261112-audio', 'n4_all'); AUD = os.path.join(OUT, 'kenzaki'); os.makedirs(AUD, exist_ok=True)
API = 'http://127.0.0.1:50021'; SPK = 21; SPEED = 0.85; PRE = 0.05; TOP = 5.00
FIX = {'242': "ネム'イ",    # 眠い：ねむ＼い（11/13 きあ）
       '615': "チョ'オ"}    # 〜町：かなで渡すと「ちょ・う」と う をはっきり読む（11/13 きあ 2回目）
import hashlib
# 語ごとの直し（11/13 きあ 2回目の印のうち、決まりにできなかった語。数字からの見立てで直した＝きあが聞いて確かめる）。ms＝その語の音のならび
def _lowfirst(ms, d=0.10): ms[0]['pitch'] = ms[1]['pitch'] - d            # 1音目を2音目より低く（ほめ＼る が ほ＼める に聞こえる）
def _shift(ms, d):
    for m in ms:
        if m['pitch'] > 0: m['pitch'] += d
def _t329(ms): ms[-1]['pitch'] = ms[-2]['pitch'] - 0.06                    # 鏡：み が上がる
def _t82(ms): ms[1]['pitch'] = ms[0]['pitch'] - 0.02                       # 釣る：る が上がる
def _t123(ms): _lowfirst(ms); ms[2]['pitch'] = max(ms[2]['pitch'], 4.58)   # 見える：音割れ（大きく下がる所）
def _t226(ms): _lowfirst(ms); ms[1]['consonant_length'] = 0.06             # うまい：ウ・マイ
def _t229(ms): ms[1]['pitch'] = ms[0]['pitch'] - 0.06; ms[1]['vowel_length'] = 0.15; ms[2]['pitch'] = 4.58; ms[2]['vowel_length'] = 0.16   # 多い：声が震える（低くて長い終わり）
def _t153(ms): ms[1]['pitch'] = ms[0]['pitch']; ms[3]['pitch'] = ms[2]['pitch'] - 0.04    # 営業：音割れ（長い音の中の段）
def _t220(ms): ms[2]['pitch'] = ms[1]['pitch'] - 0.04                      # 利用：音割れ（長い音の中の段）
def _t439(ms): ms[0]['vowel_length'] = 0.09                                # 妻：つ の母音が短くて 高い所が聞こえない
def _t264(ms): ms[1]['vowel_length'] = 0.07; ms[2]['pitch'] = ms[1]['pitch'] - 0.03       # すてき：て が短く、き が下がる
def _t198(ms):
    for m in ms: m['vowel_length'] *= 0.85                                 # 注意：遅い
def _t420(ms): ms[0]['vowel_length'] = 0.14                                # 線：せ が長い
TWEAK = {'329': _t329, '117': _lowfirst, '226': _t226, '439': _t439, '420': _t420,
         '208': lambda ms: _shift(ms, -0.07), '566': lambda ms: _shift(ms, -0.07)}   # ファックス・将来：語気が強い。ここの7語は 3回目の検分で印が消えた＝きあ了承
SPLIT = {}   # 「ん」の後で短く切る案は 外れ（11/13 きあ：ネイティブは ゲーイン・テーイン・ターイン と言う）

# ---- きあが聞きくらべ（out/listen9.html・fix9.py）で えらんだ作り方（11/13 3回目）。fix9.py と同じ計算で作る ----
def kq(k):   # かな＋アクセント記号で直接指定
    a = query('あ'); a['accent_phrases'] = json.loads(post('/accent_phrases', {'text': k, 'speaker': SPK, 'is_kana': 'true'})); a['kana'] = k; return a
def o_cap(ms, top=4.95):
    t = max(m['pitch'] for m in ms)
    if t > top:
        for m in ms:
            if m['pitch'] > 0: m['pitch'] -= t - top
def o_iso(w):   # 何もしない（語だけ）
    a = query(w); o_cap(moras(a), 5.00); return a, None
def o_copy(w, tail):   # 写す：高さを「〜の／が」の時の物に。語だけの時の1音目に合わせる
    a = query(w); b = query(w + tail); c = copy.deepcopy(a)
    va = [m['pitch'] for m in moras(a) if m['pitch'] > 0][0]; vb = [m['pitch'] for m in moras(b) if m['pitch'] > 0][0]; sh = min(0, va - vb)
    for m, mb in zip(moras(c), moras(b)):
        if mb['pitch'] > 0: m['pitch'] = mb['pitch'] + sh
    ms = moras(c)
    if len(ms) >= 3 and ms[-1]['pitch'] > ms[-2]['pitch'] - 0.06 > 0: ms[-1]['pitch'] = ms[-2]['pitch'] - 0.06
    o_cap(ms, 5.00); return c, None
def o_cut(b, n, L=0.15):   # 切る：丸ごと作って手前で切る。b＝付けた語こみの解析
    f = copy.deepcopy(b); fm = moras(f); fm[n - 1]['vowel_length'] = L
    if n >= 3 and fm[n - 1]['pitch'] > fm[n - 2]['pitch'] - 0.06 > 0: fm[n - 1]['pitch'] = fm[n - 2]['pitch'] - 0.06
    o_cap(fm[:n]); return f, (PRE + sum((m['consonant_length'] or 0) + m['vowel_length'] for m in fm[:n])) / SPEED
OVR = {   # 番号: (作り方の名前, 作る関数)。★ 原因・店員・退院は わざと正本のかなと ちがう音にしている（ネイティブの発音）
    '66':  ('下がらない型・切る（の）',      lambda: o_cut(kq("スクノ'"), 2)),          # 空く：かなで渡すと す＼く になる。おなかが すく は 下がらない型
    '82':  ('何もしない（語だけ）',          lambda: o_iso('釣る')),
    '123': ('写す（の）',                    lambda: o_copy('見える', 'の')),
    '153': ('切る（が・0.12）',              lambda: o_cut(query('営業が'), 4, 0.12)),
    '220': ('写す（が）',                    lambda: o_copy('利用', 'が')),
    '198': ('切る（が・0.15）',              lambda: o_cut(query('注意が'), 3)),
    '229': ('何もしない（語だけ）',          lambda: o_iso('多い')),
    '264': ('何もしない（語だけ）',          lambda: o_iso('すてき')),
    '554': ('切る（が・0.15）',              lambda: o_cut(query('ワープロが'), 4)),
    '168': ('ゲーイン・切る（が）',          lambda: o_cut(kq("ゲエインガ'"), 4)),
    '443': ('テーイン・切る（が）',          lambda: o_cut(kq("テエインガ'"), 4)),
    '193': ('ターイン・切る（が）',          lambda: o_cut(kq("タアインガ'"), 4)),
}
# ---- きあが 2つ目の聞きくらべ（out/listen10.html・fix10.py）で えらんだ作り方（11/14・60語。420 線 は 今のまま）。fix10.py と同じ計算 ----
P10 = {'切る少し': '2 4', '切る大きく': '12 20 21', '語だけ': '40 55 60 291 340 358 441', '写す': '72 337 386 462',
       '語だけ・低め': '23 36 42 46 58 61 62 63 67 68 76 80 81 83 88 89 90 101 117 126 128 132 133 190 329',
       '全体を短く': '150 208 288 495 524', '子音を短く': '226 289 295 297 391 439 552 566 591 615', '切る0.12': '300 306 336'}
# 11/14 新しい語（623〜）の検分で印29語 → 聞きくらべ（out/listen11.html）で えらんだ24語。お目にかかる・祝い・大家・経営 は どれもだめ、現金 は 未選択
P11 = {'最後の音を短く': '623 630 639 644 696 700 717 791 824', '1音目を低く': '643 652 658', '語だけ・低め': '683 686 687 739 782 879',
       '語だけ': '797 833 837 885', '写す': '806', '子音を短く': '840'}
PICK10 = {no: k for P in (P10, P11) for k, v in P.items() for no in v.split()}
def pick10(kind, a, text, cat, n):   # 返す：(解析, 切る秒, 母音を最後まで鳴らすか)
    tail = 'の' if cat in 'VI' else 'が'; c = copy.deepcopy(a); ms = moras(c)
    if kind in ('語だけ', '語だけ・低め'):
        o_cap(ms, 5.00)
        if kind == '語だけ・低め': _shift(ms, -0.08)
        return c, None, False
    if kind == '最後の音を短く': ms[-1]['vowel_length'] *= 0.7; o_cap(ms, 5.00); return c, None, False
    if kind == '1音目を低く':
        o_cap(ms, 5.00)
        if ms[0]['pitch'] > 0: ms[0]['pitch'] -= 0.10
        return c, None, False
    if kind == '子音を短く':
        for m in ms[1:]:
            if (m['consonant_length'] or 0) > 0.04: m['consonant_length'] = 0.04
        o_cap(ms, 5.00); return c, None, False
    if kind == '全体を短く':
        for m in ms:
            m['vowel_length'] *= 0.85
            if m['consonant_length']: m['consonant_length'] *= 0.85
        o_cap(ms, 5.00); return c, None, False
    b = query(text + tail); pb = moras(b)
    assert len(pb) == n + 1 and [m['text'] for m in pb[:n]] == [m['text'] for m in moras(a)], ('付けると音の並びが変わる', text)
    if kind == '写す':
        va = [m['pitch'] for m in moras(a) if m['pitch'] > 0][0]; vb = [m['pitch'] for m in pb if m['pitch'] > 0][0]; sh = min(0, va - vb)
        for m, mb in zip(ms, pb):
            if mb['pitch'] > 0: m['pitch'] = mb['pitch'] + sh
        o_cap(ms, 5.00); return c, None, False
    L, drop, late = {'切る少し': (0.15, 0.06, False), '切る大きく': (0.15, 0.15, False), '切る0.12': (0.12, None, True)}[kind]
    pb[n - 1]['vowel_length'] = L
    if drop is not None and pb[n - 2]['pitch'] > 0: pb[n - 1]['pitch'] = pb[n - 2]['pitch'] - drop
    o_cap(pb[:n], 4.95); return b, (PRE + sum((m['consonant_length'] or 0) + m['vowel_length'] for m in pb[:n])) / SPEED, late
# 11/14 listen11 で どれもだめ だった4語 → listen12.html（fix12.py）で えらんだ作り方
def o_k(k, d=0.0): a = kq(k); o_cap(moras(a), 5.00); _shift(moras(a), d); return a, None
def o_hi(w, d): a, _ = o_iso(w); _shift(moras(a), d); return a, None
OVR.update({
    '626': ('おめに・かか＼る（2つに分ける）', lambda: o_k("オメニ'/カカ'ル")),
    '693': ('平ら・切る（が）',               lambda: o_cut(kq("イワイガ'"), 3)),
    '694': ('語だけ・全体を高く +0.10',       lambda: o_hi('大家', 0.10)),
    '698': ('ケイエイ（イをはっきり）',       lambda: o_k("ケイエイ'")),
})
# 音を作る時だけの しゅるい。きあが聞いた後（11/14 13:17）に 語の表で S→N に変わった3語（水泳・暖房・冷房）。聞いた時の作り方（S＝切る）のままにする
ACAT = {'186': 'S', '195': 'S', '222': 'S'}
CHG = set()   # 今回 音が変わった語（前の mp3 と中身がちがう）
MARKED = set(l.split('\t')[0] for l in open(os.path.join(OUT, 'marked2.tsv'), encoding='utf-8').read().splitlines() if l.strip())   # 2回目の検分で印が付いた72語
RB = re.compile(r'\{([^|{}]+)\|([^{}]+)\}')
rows = [l.split('\t') for l in open(os.path.join(ROOT, 'scripts', 'jlpt_goi', 'n4_words.txt'), encoding='utf-8').read().splitlines() if l.strip()]
CAT = {'V': '動詞', 'S': 'する名詞', 'I': 'い形容詞', 'A': 'な形容詞', 'N': '名詞', 'K': 'カタカナ', 'F': '副詞など', 'X': 'そのほか'}
def post(path, q, body=None):
    url = API + path + '?' + urllib.parse.urlencode(q)
    req = urllib.request.Request(url, data=(json.dumps(body).encode() if body is not None else b''), headers={'Content-Type': 'application/json'}, method='POST')
    return urllib.request.urlopen(req).read()
def query(t): return json.loads(post('/audio_query', {'text': t, 'speaker': SPK}))
def hira(s): return ''.join(chr(ord(c) - 96) if 'ァ' <= c <= 'ヶ' else c for c in s)
VOW = {'a': 'あかさたなはまやらわがざだばぱゃぁ', 'i': 'いきしちにひみりぎじぢびぴぃ', 'u': 'うくすつぬふむゆるぐずづぶぷゅぅ', 'e': 'えけせてねへめれげぜでべぺぇ', 'o': 'おこそとのほもよろをごぞどぼぽょぉ'}
def vowel(c):
    for v, cs in VOW.items():
        if c in cs: return v
def loose(s):   # 発音の形にそろえる（こう＝こお、せい＝せえ、ー＝前の母音、を＝お、ぢ・づ＝じ・ず）
    s = hira(s).replace('を', 'お').replace('ぢ', 'じ').replace('づ', 'ず'); o = ''
    for c in s:
        p = vowel(o[-1]) if o else None
        if c == 'ー' and p: c = 'あいうえお'['aiueo'.index(p)]
        elif c == 'う' and p == 'o': c = 'お'
        elif c == 'い' and p == 'e': c = 'え'
        o += c
    return o
def moras(aq): return [m for p in aq['accent_phrases'] for m in p['moras']]
def yomi(aq): return ''.join(m['text'] for m in moras(aq))
def save(no, aq, cut=None, late=False):
    aq = copy.deepcopy(aq); aq['speedScale'] = SPEED; aq['prePhonemeLength'] = PRE; aq['postPhonemeLength'] = 0.12
    wav = post('/synthesis', {'speaker': SPK}, aq)
    args = ['ffmpeg', '-y', '-v', 'error', '-i', 'pipe:0']
    if cut and late: args += ['-t', f'{cut + 0.13:.3f}', '-af', f'afade=t=out:st={cut - 0.01:.3f}:d=0.04']   # 母音を最後まで鳴らしてから消す
    elif cut: args += ['-t', f'{cut + 0.1:.3f}', '-af', f'afade=t=out:st={cut - 0.04:.3f}:d=0.04']
    p = os.path.join(AUD, no.replace('+', 'p') + '.mp3')
    subprocess.run(args + ['-c:a', 'libmp3lame', '-b:a', '32k', '-ac', '1', '-ar', '24000', p], input=wav, check=True)
    return os.path.getsize(p)

led = []; cnt = collections.Counter(); total = 0
for r in rows:
    no, cat, w = r[0], ACAT.get(r[0], r[1]), r[2]
    w2 = re.sub(r'（[^）]*）|\([^)]*\)|〜', '', w); surf = RB.sub(r'\1', w2); kana = RB.sub(r'\2', w2); want = loose(kana)
    flag = []; text = surf; a = query(surf); src = '漢字'; note = []
    def same(aq): y = loose(yomi(aq)); return y == want or (kana.endswith('は') and y == loose(kana[:-1] + 'わ'))   # または＝またわ
    if no in FIX:
        a['accent_phrases'] = json.loads(post('/accent_phrases', {'text': FIX[no], 'speaker': SPK, 'is_kana': 'true'})); a['kana'] = FIX[no]; src = '手で指定'; note.append('型を手で指定')
        assert same(a), ('FIX の読みが正本と合わない', no)
    elif not same(a):
        text = kana; a = query(kana); src = 'かな'
        if not same(a): flag.append('読みが合わない（エンジン：' + hira(yomi(a)) + '）')
    ps = a['accent_phrases']; ms = moras(a); n = len(ms); how = 'そのまま'; cut = None; aq = a
    flat = len(ps) == 1 and n >= 2 and ps[0]['accent'] == n and no not in FIX
    if len(ps) > 1 and cat not in 'X': flag.append('2つ以上に切れた')
    plan = None; NEW = int(re.match(r'\d+', no).group()) > 622; lowv = NEW and flat and not flag and cat in 'VI'
    if flat and not flag:
        if cat in 'NK': plan = ('が', 0.15, '切る') if n == 2 else ('が', None, '写す')   # 11/13 2回目：0.12 は「切るのが早い」→ 0.15
        elif cat in 'VI': plan = None if NEW else ('の', 0.15, '切る')   # 11/14：623番から後は「語だけ・低め」（きあが 動詞32語中24語で えらんだ作り方）。1〜622 は きあが聞いて合格した音なので さわらない
        elif cat in 'AS': plan = ('が', 0.15, '切る')
    if plan:
        tail, L, kind = plan; b = query(text + tail); pb = moras(b)
        if len(b['accent_phrases']) == 1 and len(pb) == n + 1 and [m['text'] for m in pb[:n]] == [m['text'] for m in ms]:
            if kind == '写す':
                aq = copy.deepcopy(a)
                va = [m['pitch'] for m in ms if m['pitch'] > 0][0]; vb = [m['pitch'] for m in pb if m['pitch'] > 0][0]; sh = min(0, va - vb)
                for i, (m, mb) in enumerate(zip(moras(aq), pb)):
                    if mb['pitch'] > 0: m['pitch'] = mb['pitch'] + sh + (0.04 if i else 0)
                how = '写す'
            elif pb[n - 1]['vowel'] in 'UI': flag.append('切ると最後の母音が無声')
            else:
                aq = copy.deepcopy(b); fm = moras(aq); fm[n - 1]['vowel_length'] = L
                pv = [m['pitch'] for m in fm[:n - 1] if m['pitch'] > 0]; lastm = fm[n - 1]; late = cat in 'NK' and n == 2
                if not pv:
                    if lastm['pitch'] > 4.90: lastm['pitch'] = 4.90; note.append('前が無声＝最後を4.90に')
                elif n == 2 and lastm['pitch'] > pv[0] + 0.10: lastm['pitch'] = pv[0] + 0.10; note.append('2音：上がりを0.10までに')
                elif n >= 3 and lastm['pitch'] > pv[-1] - 0.06: lastm['pitch'] = pv[-1] - 0.06; note.append('最後の音を前の音より低く')
                top = max(m['pitch'] for m in fm[:n])
                if top > 4.95 + 0.005:
                    for m in fm[:n]:
                        if m['pitch'] > 0: m['pitch'] -= top - 4.95
                    note.append(f'切る語：全体を下げた（元の最高 {top:.2f}）')
                cut = (PRE + sum((m['consonant_length'] or 0) + m['vowel_length'] for m in fm[:n])) / SPEED
                how = f'切る（{tail}・{L}）'
        else: flag.append(f'「{tail}」を付けると切れ方が変わる')
    elif flat and cat in 'FX': flag.append('下がらない型だが 作り方を決めていない しゅるい')
    if how == 'そのまま' and len(ps) == 1 and n == 2 and ps[0]['accent'] == 1 and ms[1]['consonant'] is None and ms[1]['vowel'] == ms[0]['vowel'] and ms[0]['pitch'] > 0:
        aq = copy.deepcopy(a); m2 = moras(aq); m2[1]['pitch'] = m2[0]['pitch'] - 0.06; m2[0]['vowel_length'] = 0.14; m2[1]['vowel_length'] = 0.16; note.append('長い音をつなげる')
    FRIC = ('s', 'sh', 'z', 'j', 'ts', 'ch', 'h', 'f', 'hy')
    if how == 'そのまま' and len(ps) == 1 and ps[0]['accent'] == 1 and 2 <= n <= 3 and '長い音をつなげる' not in note:   # 頭が高い短い語：「イ・カ」と分かれる／間が長い
        if aq is a: aq = copy.deepcopy(a)
        m2 = moras(aq); hit = False
        for m in m2[1:]:
            lim = 0.10 if m['consonant'] in FRIC else 0.07
            if (m['consonant_length'] or 0) > lim: m['consonant_length'] = lim; hit = True
        if hit: note.append('頭が高い短い語：子音を短く')
        if n == 2 and m2[0]['pitch'] > 0 and m2[1]['pitch'] > m2[0]['pitch'] - 0.20: m2[1]['pitch'] = m2[0]['pitch'] - 0.20; note.append('2音目を下げた')
    if n == 1 and ms[0]['pitch'] > 0:   # 1音の語：息切れ
        if aq is a: aq = copy.deepcopy(a)
        m1 = moras(aq)[0]; m1['vowel_length'] = max(m1['vowel_length'], 0.22); m1['pitch'] = max(m1['pitch'], 4.60); note.append('1音：長く・少し高く')
    if not cut:   # いちばん高い音を TOP までに（高低の幅を縮める）
        vs = [m['pitch'] for m in moras(aq) if m['pitch'] > 0]
        if vs and max(vs) > TOP + 0.005:
            if aq is a: aq = copy.deepcopy(a)
            mean = sum(vs) / len(vs); k = max(0.6, (TOP - mean) / (max(vs) - mean)) if max(vs) > mean and mean < TOP else 0.6
            for m in moras(aq):
                if m['pitch'] > 0: m['pitch'] = mean + (m['pitch'] - mean) * k
            rest = max(m['pitch'] for m in moras(aq)) - TOP   # 縮めても TOP を超える分は、全体を下げる
            if rest > 0.005:
                for m in moras(aq):
                    if m['pitch'] > 0: m['pitch'] -= rest
            note.append(f'高さを抑えた（幅 {k:.2f}倍・元の最高 {max(vs):.2f}）')
    if no in TWEAK or no in SPLIT:
        if aq is a: aq = copy.deepcopy(a)
        if no in TWEAK: TWEAK[no](moras(aq)[:n])
        if no in SPLIT:
            allm = moras(aq); k = SPLIT[no]; PAU = 0.025
            aq['accent_phrases'] = [
                {'moras': allm[:k], 'accent': 1, 'pause_mora': {'text': '、', 'consonant': None, 'consonant_length': None, 'vowel': 'pau', 'vowel_length': PAU, 'pitch': 0.0}, 'is_interrogative': False},
                {'moras': allm[k:], 'accent': 1, 'pause_mora': None, 'is_interrogative': False}]
            if cut: cut += PAU / SPEED
        note.append('語ごとの直し')
    if no in OVR:
        name, fn = OVR[no]; aq, cut = fn(); how = 'きあがえらんだ：' + name; note = ['聞きくらべで えらんだ作り方']; flag = []
        assert len(moras(aq)) - (1 if cut else 0) == n, ('えらんだ作り方の音の数が合わない', no)
    late = bool(cut) and cat in 'NK' and n == 2 and no not in OVR
    if no in PICK10:
        aq, cut, late = pick10(PICK10[no], a, text, cat, n); how = 'きあがえらんだ：' + PICK10[no]; note = ['聞きくらべ2で えらんだ作り方']; flag = []
    elif lowv:
        aq, cut, late = pick10('語だけ・低め', a, text, cat, n); how = '語だけ・低め（新しい語の動詞・い形容詞）'; note = ['語だけ・低め']
    for x in note: cnt['直し：' + x.split('（')[0]] += 1
    fp = os.path.join(AUD, no.replace('+', 'p') + '.mp3'); before = hashlib.md5(open(fp, 'rb').read()).hexdigest() if os.path.exists(fp) else ''
    size = save(no, aq, cut, late); total += size
    if hashlib.md5(open(fp, 'rb').read()).hexdigest() != before: CHG.add(no)
    cnt[how.split('（')[0]] += 1; cnt['★ 人が見る語'] += bool(flag); cnt['読みは ' + src + ' で渡した'] += 1
    led.append(dict(no=no, cat=cat, surf=RB.sub(r'\1', w), kana=RB.sub(r'\2', w), how=how, src=src, acc=a['kana'], n=n, flat=int(flat), flag=' / '.join(flag), size=size, note=' / '.join(note),
                    pit=' '.join(f"{m['text']}:{m['consonant'] or ''}{(m['consonant_length'] or 0):.2f}:{m['vowel']}{m['vowel_length']:.2f}:{m['pitch']:.2f}" for m in moras(aq)[:n])))
open(os.path.join(OUT, 'ledger.tsv'), 'w', encoding='utf-8', newline='\n').write('番号\tしゅるい\t語\t読み\t作り方\t渡し方\tエンジンの読み\t音の数\t下がらない型\t★\tバイト\t11/13の直し\t音ごと（音:子音と長さ:母音と長さ:高さ）\n'
    + ''.join('\t'.join(str(d[k]) for k in ('no', 'cat', 'surf', 'kana', 'how', 'src', 'acc', 'n', 'flat', 'flag', 'size', 'note', 'pit')) + '\n' for d in led))
for k, v in sorted(cnt.items()): print(v, k)
print('語', len(led), '合計', round(total / 1e6, 2), 'MB', '1語平均', round(total / len(led) / 1024, 2), 'KB')

# ---- 検分ページ ----
random.seed(20261113)
OLDF = os.path.join(OUT, 'sample1.txt')   # 1回目の見本（check.html から取っておく。2回目は別の語を出す）
if not os.path.exists(OLDF):
    open(OLDF, 'w', encoding='utf-8').write('\n'.join(re.findall(r'<tr class="s [^"]*" data-no="([^"]+)"', open(os.path.join(OUT, 'check.html'), encoding='utf-8').read())) + '\n')
OLD = set(open(OLDF, encoding='utf-8').read().split())
def changed(d): return d['no'] in MARKED or any(x.split('（')[0] in ('型を手で指定', '前が無声＝最後を4.90に', '長い音をつなげる') for x in d['note'].split(' / '))
groups = collections.defaultdict(list)
for d in led:
    if not d['flag'] and d['no'] not in OLD: groups[(d['how'].split('（')[0], d['cat'])].append(d)
sample = set(); want_n = 50; pool = sum(len(v) for v in groups.values())
for k, v in groups.items():
    for d in random.sample(v, max(1, round(len(v) * want_n / pool))): sample.add(d['no'])
def row(d):
    cls = ('f ' if d['flag'] else '') + ('n ' if int(re.match(r'\d+', d['no']).group()) > 622 else '') + ('m ' if d['no'] in MARKED else '') + ('t' if d['no'] in OVR or d['no'] in PICK10 else '')
    return (f'<tr class="{cls}" data-no="{html.escape(d["no"])}"><td>{html.escape(d["no"])}</td><td class="w">{html.escape(d["surf"])}</td><td>{html.escape(d["kana"])}</td>'
            f'<td><button class="p" data-f="kenzaki/{d["no"].replace("+", "p")}.mp3">▶</button></td>'
            f'<td><label><input type="checkbox" class="ng"> へん</label></td><td><input class="memo" placeholder="メモ"></td>'
            f'<td class="h">{CAT[d["cat"]]}・{html.escape(d["how"])}<br>{html.escape(d["acc"])}{("<br>" + html.escape(d["note"])) if d["note"] else ""}{("<br><b>★" + html.escape(d["flag"]) + "</b>") if d["flag"] else ""}</td></tr>')
NEWN = sum(1 for d in led if int(re.match(r'\d+', d['no']).group()) > 622)
page = f'''<!doctype html><html lang="ja"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>N4 音声の検分</title>
<style>
body{{font-family:"BIZ UDPGothic","Yu Gothic",sans-serif;margin:16px;max-width:1000px}}
table{{border-collapse:collapse;width:100%}}td,th{{border:1px solid #ccc;padding:6px 8px;font-size:14px}}
td.w{{font-size:20px}}td.h{{font-size:11px;color:#666}}tr.f td.h b{{color:#b00}}
button.p{{font-size:18px;padding:6px 18px}}tr.on{{background:#fff3c4}}tr.bad{{background:#ffd9d9}}
.bar{{position:sticky;top:0;background:#fff;padding:8px 0;border-bottom:2px solid #333;z-index:2}}
.bar button{{font-size:15px;padding:6px 12px;margin-right:6px}}.bar button.cur{{background:#333;color:#fff}}
textarea{{width:100%;height:90px;font-size:14px}}.hide{{display:none}}input.memo{{width:10em}}
</style>
<h1>N4 語彙：音声の検分 5回目（剣崎雌雄・0.85）</h1>
<p>▶ で聞く。へんな語は「へん」に印（メモは書かなくてよい）。印は このブラウザに残る。終わったら 下の「印を付けた語」をコピーして Claude に貼る。試作なので公開しない。</p>
<div class="bar">
<button data-v="n" class="cur">新しい語（623番から） {NEWN}語</button><button data-v="t">聞きくらべで えらんだ {len(OVR) + len(PICK10)}語</button><button data-v="m">2回目に 印を付けた {len(MARKED)}語</button><button data-v="f">★ 機械が自信の無い語 {sum(1 for d in led if d["flag"])}</button><button data-v="all">ぜんぶ {len(led)}語</button>
<span id="stat"></span></div>
<table><tr><th>番号</th><th>語</th><th>読み</th><th>聞く</th><th>判定</th><th>メモ</th><th>作り方・エンジンの読み（' の所で下がる）</th></tr>{"".join(row(d) for d in led)}</table>
<h2>印を付けた語</h2><textarea id="out" readonly></textarea><button id="copy">コピー</button>
<script>
const KEY='n4_audio_check_v6'; let st={{}}; try{{st=JSON.parse(localStorage.getItem(KEY)||'{{}}')||{{}};}}catch(e){{}}
const trs=[...document.querySelectorAll('tr[data-no]')]; let au=null, view='n';
function save(){{ try{{localStorage.setItem(KEY,JSON.stringify(st));}}catch(e){{}} paint(); }}
function paint(){{
  let heard=0,bad=0,shown=0; const lines=[];
  trs.forEach(tr=>{{ const no=tr.dataset.no, s=st[no]||{{}};
    const vis = view==='all' || tr.classList.contains(view); tr.classList.toggle('hide',!vis);
    tr.querySelector('.ng').checked=!!s.ng; if(document.activeElement!==tr.querySelector('.memo')) tr.querySelector('.memo').value=s.memo||'';
    tr.classList.toggle('on',!!s.h&&!s.ng); tr.classList.toggle('bad',!!s.ng);
    if(vis){{shown++; if(s.h) heard++;}} if(s.ng){{bad++; lines.push(no+'\\t'+tr.children[1].textContent+'\\t'+tr.children[2].textContent+'\\t'+(s.memo||''));}} }});
  document.getElementById('stat').textContent='聞いた '+heard+' / '+shown+'　へん '+bad;
  document.getElementById('out').value=lines.join('\\n');
}}
trs.forEach(tr=>{{ const no=tr.dataset.no;
  tr.querySelector('.p').onclick=e=>{{ if(au) au.pause(); au=new Audio(e.target.dataset.f); au.play(); (st[no]=st[no]||{{}}).h=1; save(); }};
  tr.querySelector('.ng').onchange=e=>{{ (st[no]=st[no]||{{}}).ng=e.target.checked?1:0; save(); }};
  tr.querySelector('.memo').oninput=e=>{{ (st[no]=st[no]||{{}}).memo=e.target.value; save(); }};
}});
document.querySelectorAll('.bar button').forEach(b=>b.onclick=()=>{{ view=b.dataset.v; document.querySelectorAll('.bar button').forEach(x=>x.classList.toggle('cur',x===b)); paint(); }});
document.getElementById('copy').onclick=()=>{{ const t=document.getElementById('out'); t.select(); try{{navigator.clipboard.writeText(t.value);}}catch(e){{document.execCommand('copy');}} }};
paint();
</script></html>'''
p = os.path.join(OUT, 'check6.html'); open(p, 'w', encoding='utf-8', newline='\n').write(page); print(p, '見本', len(sample))
