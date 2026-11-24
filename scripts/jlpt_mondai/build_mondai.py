# -*- coding: utf-8 -*-
"""JLPT 模試（言語知識）の問題データを作る道具。

batches（作った問題の TSV）→ jlpt/mondai/n1.js〜n4.js（級ごと。模試のページ jlpt/moshi.html が読む）

使い方（リポの直下で）:
  py -X utf8 scripts/jlpt_mondai/build_mondai.py            # 点検と数だけ（書かない）
  py -X utf8 scripts/jlpt_mondai/build_mondai.py --execute  # 書く（前の版は tmp/mondai_backup/ へ）
  --src <フォルダ>  batches のある out_mondai（既定＝scratch/20261123-mondai/out_mondai）

★問題を直したら（別の窓の見直しなど）、これを回し直すだけで入れかわる。js は手で直さない。
★本番の構成（形式ごとの数）は下の COMPOSITION が正本。ページはデータの中の構成を読む。
★N4 だけ ルビ を付ける（n4_ruby.py。pykakasi が要る）。まだ確かめていない読みが出たら、ここが知らせる。

出さない問題（理由ごとに数を出す）:
  確認の列が空でない／形がこわれている（選択肢が4つない・正答が1〜4でない・下線や空欄の印が無い・
  文の組み立ての並びと正答が合わない など）。番号だけ印字する（中身は出さない）。
"""
import argparse, csv, datetime, glob, json, os, random, re, shutil, sys
from collections import Counter, defaultdict

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
SRC_DEFAULT = os.path.join(REPO, 'scratch', '20261123-mondai', 'out_mondai')
OUT_DIR = os.path.join(REPO, 'jlpt', 'mondai')
BACKUP_DIR = os.path.join(REPO, 'tmp', 'mondai_backup')

# 大問の順（本番の順）。ページはこの番号で形式を引く。
FORMS = ['漢字読み', '表記', '語形成', '文脈規定', '言い換え類義', '用法',
         '文法形式判断', '文の組み立て', '文章の文法']
VOCAB_FORMS = set(FORMS[:6])   # 文字・語彙（残りは文法）

# 本番の構成（2026-11-24 きあ確認）。模試の取り出しデータ 69回分で数えた数。
# N1〜N3 はどの本でも同じ。N4 は 2020年12月の時間短縮のあとの型（SUCCESS N4 など）。
COMPOSITION = {
    'N1': {'漢字読み': 6, '文脈規定': 7, '言い換え類義': 6, '用法': 6,
           '文法形式判断': 10, '文の組み立て': 5, '文章の文法': 5},
    'N2': {'漢字読み': 5, '表記': 5, '語形成': 5, '文脈規定': 7, '言い換え類義': 5, '用法': 5,
           '文法形式判断': 12, '文の組み立て': 5, '文章の文法': 5},
    'N3': {'漢字読み': 8, '表記': 6, '文脈規定': 11, '言い換え類義': 5, '用法': 5,
           '文法形式判断': 13, '文の組み立て': 5, '文章の文法': 5},
    'N4': {'漢字読み': 7, '表記': 5, '文脈規定': 8, '言い換え類義': 4, '用法': 4,
           '文法形式判断': 13, '文の組み立て': 4, '文章の文法': 4},
}
STARS = {'★★★': 3, '★★': 2, '★': 1}
COLS = ['番号', '級', '種類', '対象', '形式', '問題文', '選択肢1', '選択肢2', '選択肢3', '選択肢4',
        '正答', '並び', '解説', '確認']
UNDERLINE_FORMS = {'漢字読み', '表記', '言い換え類義'}   # 問題文に【 】
BLANK_FORMS = {'語形成', '文脈規定', '文法形式判断', '文章の文法'}   # 問題文に（　　）
RE_BLANK = re.compile(r'（[\s　]*[0-9０-９]*[\s　]*）')
RE_SLOT = re.compile(r'＿[＿★]＿')   # 文の組み立ての空欄（＿＿＿ と ＿★＿）
BATCH_NAME = re.compile(r'^[A-Z]\d{3}\.tsv$')


def read_jobs(src):
    star = {}
    with open(os.path.join(src, 'jobs.tsv'), encoding='utf-8', newline='') as f:
        for r in csv.DictReader(f, delimiter='\t', quoting=csv.QUOTE_NONE):
            star[r['id']] = STARS.get(r['★'], 0)
    return star


def check_row(r):
    """出せない理由を返す（出せる時は None）。"""
    form = r['形式']
    if form not in FORMS:
        return '形式が9つ以外'
    if r['級'] not in COMPOSITION:
        return '級がN1〜N4以外'
    if form not in COMPOSITION[r['級']]:
        return 'その級に無い形式'
    if (r['確認'] or '').strip():
        return '確認の列あり'
    ch = [(r['選択肢%d' % i] or '').strip() for i in range(1, 5)]
    if not all(ch):
        return '選択肢が4つない'
    if len(set(ch)) < 4:
        return '選択肢が重なる'
    if r['正答'].strip() not in ('1', '2', '3', '4'):
        return '正答が1〜4でない'
    q = (r['問題文'] or '').strip()
    if not q:
        return '問題文が空'
    if not (r['対象'] or '').strip():
        return '対象が空'
    if form in UNDERLINE_FORMS and not ('【' in q and '】' in q):
        return '下線の印【】が無い'
    if form == '用法' and not all('【' in c and '】' in c for c in ch):
        return '用法の選択肢に【】が無い'
    if form in BLANK_FORMS:
        nb = len(RE_BLANK.findall(q))
        # 文法形式判断は「A であれ B であれ」の形で空欄が2つの問題がある（本番にもある）
        if not (nb == 1 or (form == '文法形式判断' and nb == 2)):
            return '空欄（　）の数がちがう'
    if form == '文の組み立て':
        slots = RE_SLOT.findall(q)
        if len(slots) != 4 or slots.count('＿★＿') != 1:
            return '組み立ての空欄が4つ・★1つでない'
        order = r['並び'].strip().split('-')
        if sorted(order) != ['1', '2', '3', '4']:
            return '並びが1〜4の並べ替えでない'
        if order[slots.index('＿★＿')] != r['正答'].strip():
            return '並びと正答が合わない'
    return None


def load(src):
    star = read_jobs(src)
    ok = defaultdict(list)        # 級 -> [問題]
    ng = defaultdict(list)        # 理由 -> [番号]
    ignored = []
    files = sorted(glob.glob(os.path.join(src, 'batches', '*.tsv')))
    used = 0
    for p in files:
        name = os.path.basename(p)
        if not BATCH_NAME.match(name):
            ignored.append(name)
            continue
        used += 1
        bid = name[:-4]
        with open(p, encoding='utf-8', newline='') as f:
            lines = f.read().split('\n')
        head = lines[0].rstrip('\r').split('\t')
        if head != COLS:
            sys.exit('止めました：%s の列名が決まりとちがいます' % name)
        for ln, line in enumerate(lines[1:], 2):
            line = line.rstrip('\r')
            if not line.strip():
                continue
            cells = line.split('\t')
            qid = '%s-%s' % (bid, cells[0])
            if len(cells) != len(COLS):
                ng['列の数が14でない'].append(qid)
                continue
            r = dict(zip(COLS, cells))
            why = check_row(r)
            if why:
                ng[why].append(qid)
                continue
            ok[r['級']].append([
                qid, FORMS.index(r['形式']), star.get(bid, 0), r['対象'].strip(),
                r['問題文'].strip(), [r['選択肢%d' % i].strip() for i in range(1, 5)],
                int(r['正答']), r['並び'].strip() if r['形式'] == '文の組み立て' else '',
                r['解説'].strip(),
            ])
    return ok, ng, ignored, used


RE_RUBY = re.compile(r'\{([^{}|]+)\|([^{}|]+)\}')


def check_ruby(ok):
    """ルビの形と置き場を点検する。まちがいの番号を返す。
    N3 から上には付けない／漢字読み・表記の選択肢と解説、漢字読み・表記・用法の【 】の中には付けない／{ } の形がこわれていない。"""
    bad = []
    for lv, rows in ok.items():
        for q in rows:
            f = FORMS[q[1]]
            texts = [q[4]] + q[5] + [q[8]]
            if lv != 'N4':
                if any('{' in t for t in texts):
                    bad.append(q[0] + '(N4以外)')
                continue
            for t in texts:
                if RE_RUBY.sub('', t).count('{') or RE_RUBY.sub('', t).count('}'):
                    bad.append(q[0] + '(形)')
            if f in ('漢字読み', '表記') and any('{' in t for t in q[5] + [q[8]]):
                bad.append(q[0] + '(選択肢・解説)')
            if f in ('漢字読み', '表記', '用法'):
                for t in texts:
                    if any('{' in m for m in re.findall(r'【[^】]*】', t)):
                        bad.append(q[0] + '(【】の中)')
    return bad


def sample_exam(pool_by_form, comp, rng):
    """ページと同じ選び方：大問の順に、まだ出していない対象だけを無作為に取る。"""
    used, out = set(), []
    for f in FORMS:
        need = comp.get(f, 0)
        if not need:
            continue
        cand = pool_by_form[f][:]
        rng.shuffle(cand)
        got = 0
        for q in cand:
            if q[3] in used:
                continue
            used.add(q[3]); out.append(q); got += 1
            if got == need:
                break
        if got < need:
            return None
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--src', default=SRC_DEFAULT)
    ap.add_argument('--execute', action='store_true', help='jlpt/mondai/*.js を書く')
    ap.add_argument('--trials', type=int, default=2000, help='試しに組む回数（足りなくならないかの確認）')
    a = ap.parse_args()

    ok, ng, ignored, used = load(a.src)
    print('読んだ束: %d（名前が束の形でないので読まなかった物 %d）' % (used, len(ignored)))
    # N4 だけ ルビ（2026-11-24 きあ：本番の N4 は N5 より上の漢字にルビがある）。決まりは n4_ruby.py
    import n4_ruby
    rb = n4_ruby.Ruby()
    for q in ok['N4']:
        n4_ruby.apply(q, FORMS[q[1]], rb)
    bad_ruby = check_ruby(ok)
    nr = sum(1 for q in ok['N4'] if '{' in q[4] + ''.join(q[5]) + q[8])
    unc = rb.unchecked()
    print('N4 のルビ: %d問に付けた（語と読みの組 %d・直しの表 %d行）' % (nr, len(rb.seen), len(rb.fix)))
    if unc:
        print('  ★まだ確かめていない組 %d（前後を見て、まちがいなら n4_ruby_fix.txt に、見たら n4_ruby_checked.txt に足す）：' % len(unc))
        for (k, r), (n, qid) in sorted(unc.items())[:30]:
            print('    %s %s（%d回・例 %s）' % (k, r, n, qid))
    for k, (n, qid) in rb.unaligned.items():
        print('  ★読みと字を合わせられなかった所：%s（%s）' % (k, qid))
    if bad_ruby:
        print('  ★ルビの置き場のまちがい %d：%s' % (len(bad_ruby), ' '.join(bad_ruby[:12])))
    print('出す問題: ' + '・'.join('%s %d' % (lv, len(ok[lv])) for lv in COMPOSITION))
    nng = sum(len(v) for v in ng.values())
    print('出さない問題: %d' % nng)
    for why, ids in sorted(ng.items(), key=lambda x: -len(x[1])):
        print('  %s %d：%s' % (why, len(ids), ' '.join(ids[:12]) + (' …' if len(ids) > 12 else '')))

    bad = False
    rng = random.Random(20261124)
    for lv, comp in COMPOSITION.items():
        by = defaultdict(list)
        for q in ok[lv]:
            by[FORMS[q[1]]].append(q)
        print('\n%s（1回 %d問）' % (lv, sum(comp.values())))
        for f in FORMS:
            if f not in comp:
                continue
            n_t = len({q[3] for q in by[f]})
            mark = '' if len(by[f]) >= comp[f] and n_t >= comp[f] else '  ← 足りない'
            bad |= bool(mark)
            print('  %-8s 本番 %2d問／作った %4d問（対象 %4d）%s' % (f, comp[f], len(by[f]), n_t, mark))
        fails = sum(1 for _ in range(a.trials) if sample_exam(by, comp, rng) is None)
        print('  試しに %d回組んで、足りなくなった回 %d' % (a.trials, fails))
        bad |= fails > 0

    if bad:
        sys.exit('\n止めました：構成の数に足りない級があります（書いていません）')
    if bad_ruby:
        sys.exit('\n止めました：答えにかかわる所にルビが付いています（書いていません）')
    if not a.execute:
        print('\n（点検だけ。書く時は --execute）')
        return

    os.makedirs(OUT_DIR, exist_ok=True)
    olds = glob.glob(os.path.join(OUT_DIR, 'n*.js'))
    if olds:
        bk = os.path.join(BACKUP_DIR, datetime.datetime.now().strftime('%Y%m%d-%H%M%S'))
        os.makedirs(bk, exist_ok=True)
        for p in olds:
            shutil.copy2(p, bk)
        print('\n前の版を退避: %s（%d本）' % (os.path.relpath(bk, REPO), len(olds)))
    for lv, comp in COMPOSITION.items():
        key = lv.lower()
        head = {'lv': lv, 'forms': FORMS, 'vocab': [f for f in FORMS if f in VOCAB_FORMS],
                'comp': comp, 'n': len(ok[lv]), 'ruby': lv == 'N4',
                'cols': ['番号', '形式', '★', '対象', '問題文', '選択肢', '正答', '並び', '解説']}
        body = ',\n'.join(json.dumps(q, ensure_ascii=False, separators=(',', ':')) for q in ok[lv])
        txt = ('/* 自動生成（手で直さない）：py -X utf8 scripts/jlpt_mondai/build_mondai.py --execute\n'
               '   元＝scratch/20261123-mondai/out_mondai/batches。問題を直したら道具を回し直す。 */\n'
               '(window.MONDAI=window.MONDAI||{}).%s=%s;\nwindow.MONDAI.%s.q=[\n%s\n];\n'
               % (key, json.dumps(head, ensure_ascii=False, separators=(',', ':')), key, body))
        p = os.path.join(OUT_DIR, key + '.js')
        with open(p, 'w', encoding='utf-8', newline='\n') as f:
            f.write(txt)
        print('書いた: %s（%d問・%.2f MB）' % (os.path.relpath(p, REPO), len(ok[lv]),
                                           os.path.getsize(p) / 1024 / 1024))


if __name__ == '__main__':
    main()
