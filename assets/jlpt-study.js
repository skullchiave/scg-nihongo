/* JLPT 文法ドリル共通：「続ける仕組み」（2026-11-12・仕様 scratch/20261112-portal/spec_1to5.md）
   jlpt/N?_bunpou.html の本体スクリプトの「後」に読む。本体の rec / save / pool / start / answer / updateStats / recPill を
   そのまま使い、上にかぶせるだけ（本体のコード・記録キーは変えない）。このファイルが読めない時は、今までどおり動く。
   記録の形： rec[文法] = {n, ok, last, t, box, due}
     t   = 最後に解いた日（YYYY-MM-DD・端末の日付）
     box = 定着の段階 0〜4（正解で1つ上がる・まちがいで0）
     due = 次に出す日
   古い記録（t が無い）は box = last===1 ? 1 : 0、due = 今日 として読む（書き戻すのは次に解いた時だけ）。
   drill_days = {日付: その日に解いた問題数}（4レベル共通・400日より古い日は消す） */
(function(){
  'use strict';
  if(typeof ITEMS==='undefined' || typeof rec==='undefined' || typeof answer!=='function') return;

  /* ---- きあが後で動かせる数字 ---- */
  var GAP=[1,1,3,7,14,30];        // box 0〜5 → 次に出すまでの日数（まちがい＝明日）。はじめての正解（box 1）も明日＝4択は知らなくても当たるので、2回つづけて正解してから間をあける（2026-11-14）
  var MASTER=2;                   // 「おぼえた」＝ box がこれ以上
  var DAY_LINE=10;                // 「やった日」＝ 1日にこれ以上解いた日
  var WEEK_GOAL=4;                // 週の目標（日）
  var TODAY_N=10;                 // きょうの◯問
  var NEW_MIN=3;                  // きょうの◯問に、新しい問題を少なくともこの数だけ入れる（復習がたまっても進むように）
  var EXAMS=['2026-12-06','2027-07-04','2027-12-05'];   // 2026-12-06 は確定。★2027年の2つは未発表＝第1日曜で計算した仮の日付（きあ 11/12）。発表されたら直す
  var DAYS_KEY='drill_days';

  /* ---- 日付 ---- */
  function pad(n){ return (n<10?'0':'')+n; }
  function fmt(d){ return d.getFullYear()+'-'+pad(d.getMonth()+1)+'-'+pad(d.getDate()); }
  function parse(s){ var a=s.split('-'); return new Date(+a[0],+a[1]-1,+a[2]); }
  function today(){   // 動作確認用に ?today=YYYY-MM-DD で日付を変えられる
    var m=/[?&]today=(\d{4}-\d{2}-\d{2})/.exec(location.search);
    return m?m[1]:fmt(new Date());
  }
  function addDays(s,n){ var d=parse(s); d.setDate(d.getDate()+n); return fmt(d); }
  function diffDays(a,b){ return Math.round((parse(b)-parse(a))/86400000); }

  /* ---- 記録の読み方（古い形もここで吸収） ---- */
  function boxOf(r){ if(!r) return 0; return (typeof r.box==='number')?r.box:(r.last===1?1:0); }
  function dueOf(r){ return (r&&r.due)?r.due:today(); }
  function stageOf(id){ var r=rec[id]; if(!r) return 0; return boxOf(r)>=MASTER?2:1; }   // 0まだ 1れんしゅう中 2おぼえた

  function loadDays(){ try{ return JSON.parse(localStorage.getItem(DAYS_KEY)||'{}')||{}; }catch(e){ return {}; } }
  function bumpDay(){
    try{
      var d=loadDays(), t=today(), lim=addDays(t,-400);
      d[t]=(d[t]||0)+1;
      Object.keys(d).forEach(function(k){ if(k<lim) delete d[k]; });
      localStorage.setItem(DAYS_KEY,JSON.stringify(d));
    }catch(e){}
  }

  /* ---- 1・2：答えた時に 日付・段階・次に出す日 を残す ---- */
  var _answer=answer;
  window.answer=function(oi){
    if(answered) return;
    var id=cur.id, pb=boxOf(rec[id]);
    _answer(oi);
    var r=rec[id]; if(!r) return;
    var ok=r.last===1, t=today();
    r.box=ok?Math.min(GAP.length-1,pb+1):0;
    r.t=t;
    r.due=addDays(t, ok?GAP[r.box]:1);
    save(); bumpDay();
  };

  /* ---- 2：きょうの10問 ---- */
  function pickToday(){
    var p=pool(), t=today(), out=[], used={};
    function take(xs){ for(var i=0;i<xs.length&&out.length<TODAY_N;i++){ if(!used[xs[i].id]){ used[xs[i].id]=1; out.push(xs[i]); } } }
    var due=p.filter(function(it){ return rec[it.id] && dueOf(rec[it.id])<=t; })
             .sort(function(a,b){ var x=dueOf(rec[a.id]), y=dueOf(rec[b.id]); return x<y?-1:x>y?1:0; });
    // 新しい問題は まぜて出す（リストの順＝動詞ばかり、にしない）。復習が多い日も NEW_MIN 問は新しい問題にする
    var fresh=p.filter(function(it){ return !rec[it.id]; });
    for(var i=fresh.length-1;i>0;i--){ var j=Math.floor(Math.random()*(i+1)), x=fresh[i]; fresh[i]=fresh[j]; fresh[j]=x; }
    take(due.slice(0, TODAY_N-Math.min(NEW_MIN,fresh.length))); var nDue=out.length;
    take(fresh); var nNew=out.length-nDue;
    take(due); nDue=out.length-nNew;
    take(p.filter(function(it){ return rec[it.id]; })
          .sort(function(a,b){ var x=boxOf(rec[a.id])-boxOf(rec[b.id]); if(x) return x; var c=dueOf(rec[a.id]), d=dueOf(rec[b.id]); return c<d?-1:c>d?1:0; }));
    return {list:out, due:nDue, fresh:nNew};
  }

  /* ---- 見た目（このファイルの中だけ。スマホ＝そのまま／PC＝1920基準で大きく） ---- */
  var MON='<ruby>問<rt>もん</rt></ruby>';
  var css=''
   +'.jsm-card{background:#fff;border-radius:16px;box-shadow:var(--card-shadow);margin-top:12px;padding:12px 16px;}'
   +'.jsm-exam{font-size:15px;font-weight:700;line-height:1.9;}'
   +'.jsm-exam b{font-size:20px;color:var(--accentT);font-variant-numeric:tabular-nums;margin:0 2px;}'
   +'.jsm-exam .s{display:block;font-size:13px;color:var(--muted);}'
   +'.jsm-exam .s b{font-size:16px;}'
   +'.jsm-week{display:flex;align-items:center;gap:6px;margin-top:8px;padding-top:8px;border-top:1px solid #edf1f7;font-size:13px;font-weight:700;color:var(--muted);flex-wrap:wrap;}'
   +'.jsm-week i{width:14px;height:14px;border-radius:50%;background:#e6ebf3;display:inline-block;flex-shrink:0;}'
   +'.jsm-week i.on{background:var(--ok);}'
   +'.jsm-week i.now{outline:2px solid var(--accentStrong);outline-offset:1px;}'
   +'.jsm-week .t{margin-left:6px;line-height:1.9;}'
   +'.jsm-week .t b{font-size:16px;color:var(--ink);font-variant-numeric:tabular-nums;}'
   +'.jsm-week .t.done{color:var(--ok);}'
   +'.jsm-bar{display:flex;height:12px;border-radius:999px;overflow:hidden;background:#e6ebf3;margin-top:12px;}'
   +'.jsm-bar i{display:block;height:100%;}'
   +'.jsm-bar .a{background:var(--ok);} .jsm-bar .b{background:var(--accentStrong);}'
   +'.jsm-leg{display:flex;flex-wrap:wrap;gap:4px 14px;margin-top:6px;font-size:12px;font-weight:700;color:var(--muted);line-height:1.9;}'
   +'.jsm-leg span{white-space:nowrap;} .jsm-leg b{font-variant-numeric:tabular-nums;color:var(--ink);margin-left:3px;}'
   +'.jsm-dot{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:5px;background:#c9d4e6;vertical-align:baseline;}'
   +'.jsm-dot.s2{background:var(--ok);} .jsm-dot.s1{background:var(--accentStrong);}'
   +'.jsm-st{flex-shrink:0;margin-top:9px;margin-right:0;margin-left:auto;}'
   +'.gtop .jsm-st + .pill{margin-left:6px;}'
   +'.bigbtn.jsm-today{background:var(--accentStrong);}'
   +'.bigbtn.jsm-today small{color:#fff;}'
   +'.bigbtn.jsm-today + .bigbtn{margin-top:10px;}'
   +'@media (min-width:641px){'
   +'.jsm-card{border-radius:28px;margin-top:24px;padding:20px 32px;display:flex;align-items:center;justify-content:space-between;gap:32px;flex-wrap:wrap;}'
   +'.jsm-exam{font-size:28px;} .jsm-exam b{font-size:40px;} .jsm-exam .s{font-size:22px;} .jsm-exam .s b{font-size:28px;}'
   +'.jsm-week{margin-top:0;padding-top:0;border-top:none;font-size:22px;gap:10px;}'
   +'.jsm-week i{width:24px;height:24px;} .jsm-week .t b{font-size:28px;}'
   +'.jsm-bar{height:20px;margin-top:20px;}'
   +'.jsm-leg{font-size:20px;gap:6px 28px;margin-top:10px;}'
   +'.jsm-dot{width:16px;height:16px;margin-right:8px;}'
   +'.jsm-st{margin-top:14px;}'
   +'.bigbtn.jsm-today + .bigbtn{margin-top:20px;}'
   +'}';
  var st=document.createElement('style'); st.textContent=css; document.head.appendChild(st);

  var setup=document.getElementById('setup'), stats=setup.querySelector('.stats'), rnd=setup.querySelector('[data-mode="random10"]');
  // 語彙ドリルの新しいホーム（2026-11-15）は、部品をページの側が持つ（.stats が無い）。ここからは 部品を足さず、数え方だけ渡す（__jlptStudy）
  var OWN=!stats||!rnd, card, prog, tb;
  if(!OWN){
  card=document.createElement('div'); card.className='jsm-card'; card.id='jsmCard';
  setup.insertBefore(card,stats);
  prog=document.createElement('div'); prog.id='jsmProg';
  stats.parentNode.insertBefore(prog,stats.nextSibling);
  tb=document.createElement('button'); tb.className='bigbtn jsm-today'; tb.id='jsmToday';
  tb.innerHTML=rnd.querySelector('svg').outerHTML+'<span><b>きょうの '+TODAY_N+MON+'</b><small id="jsmTodaySub"></small></span>';
  rnd.parentNode.insertBefore(tb,rnd);
  tb.onclick=function(){ var x=pickToday(); if(x.list.length) start(x.list); };
  }
  function exam(){   // 次の試験日と、あと何日か
    var t=today();
    for(var i=0;i<EXAMS.length;i++){ if(EXAMS[i]>t) return {date:EXAMS[i], left:diffDays(t,EXAMS[i])}; }
    return null;
  }

  function week(){   // 今週（月〜日）：DAY_LINE 問以上 解いた日
    var d=loadDays(), t=today(), mon=addDays(t,-((parse(t).getDay()+6)%7)), done=0, days=[];
    for(var k=0;k<7;k++){ var ds=addDays(mon,k), on=(d[ds]||0)>=DAY_LINE; if(on) done++; days.push({on:on, now:ds===t}); }
    return {done:done, goal:WEEK_GOAL, line:DAY_LINE, days:days};
  }

  /* ---- 3・4・5：メニューの表示 ---- */
  function paint(){
    if(OWN) return;
    var p=pool(), n=[0,0,0];
    p.forEach(function(it){ n[stageOf(it.id)]++; });
    var tot=p.length||1;
    prog.innerHTML='<div class="jsm-bar" role="img" aria-label="おぼえた '+n[2]+'、れんしゅうちゅう '+n[1]+'、まだ '+n[0]+'">'
      +'<i class="a" style="width:'+(n[2]/tot*100)+'%"></i><i class="b" style="width:'+(n[1]/tot*100)+'%"></i></div>'
      +'<div class="jsm-leg"><span><i class="jsm-dot s2"></i>おぼえた<b>'+n[2]+'</b></span>'
      +'<span><i class="jsm-dot s1"></i>れんしゅう<ruby>中<rt>ちゅう</rt></ruby><b>'+n[1]+'</b></span>'
      +'<span><i class="jsm-dot"></i>まだ<b>'+n[0]+'</b></span></div>';

    var x=pickToday();
    var sub=document.getElementById('jsmTodaySub');
    sub.innerHTML = x.due ? 'ふくしゅう '+x.due+MON+(x.fresh?'　あたらしい '+x.fresh+MON:'')
                  : x.fresh ? 'あたらしい '+x.fresh+MON
                  : 'もう<ruby>一度<rt>いちど</rt></ruby> れんしゅう';
    tb.disabled=!x.list.length;

    // 試験日までの距離（そのレベル全体で数える）
    var t=today(), ex=null;
    for(var i=0;i<EXAMS.length;i++){ if(EXAMS[i]>t){ ex=EXAMS[i]; break; } }
    var h='';
    if(ex){
      var left=diffDays(t,ex), rest=ITEMS.filter(function(it){ return stageOf(it.id)!==2; }).length;
      h+='<div class="jsm-exam">JLPTまで あと<b>'+left+'</b><ruby>日<rt>にち</rt></ruby>'
        +(rest?'<span class="s"><ruby>1日<rt>いちにち</rt></ruby><b>'+Math.ceil(rest/left)+'</b>'+MON+'で ぜんぶ おぼえられる</span>':'')+'</div>';
    }
    // 今週（月〜日）：10問以上解いた日
    var d=loadDays(), now=parse(t), mon=addDays(t,-((now.getDay()+6)%7)), done=0, dots='';
    for(var k=0;k<7;k++){
      var ds=addDays(mon,k), on=(d[ds]||0)>=DAY_LINE; if(on) done++;
      dots+='<i class="'+(on?'on':'')+(ds===t?' now':'')+'"></i>';
    }
    h+='<div class="jsm-week" aria-label="こんしゅう '+done+'にち">'+dots
      +(done>=WEEK_GOAL ? '<span class="t done"><ruby>今週<rt>こんしゅう</rt></ruby>の もくひょう たっせい！</span>'
                        : '<span class="t"><ruby>今週<rt>こんしゅう</rt></ruby> <b>'+done+'</b> / <ruby>'+WEEK_GOAL+'日<rt>'+(['','いちにち','ふつか','みっか','よっか','いつか','むいか','なのか'][WEEK_GOAL]||'')+'</rt></ruby></span>')
      +'</div>';
    card.innerHTML=h;
  }
  var _upd=updateStats;
  window.updateStats=function(){ _upd(); try{ paint(); }catch(e){} };

  /* ---- 3：文法リスト・くわしく の各行に段階の印 ---- */
  if(typeof recPill==='function'){
    var _pill=recPill, LBL=['まだ','れんしゅうちゅう','おぼえた'];
    window.recPill=function(id){ var s=stageOf(id); return '<i class="jsm-dot jsm-st s'+s+'" role="img" aria-label="'+LBL[s]+'" title="'+LBL[s]+'"></i>'+_pill(id); };
  }

  // 分野を変えた時（select の onchange は本体が古い updateStats を直接つかんでいる）
  var sel=document.getElementById('catSel'); if(sel) sel.onchange=function(){ updateStats(); };
  window.__jlptStudy={pickToday:pickToday,stageOf:stageOf,today:today,exam:exam,week:week};
  updateStats();
  if(typeof view!=='undefined' && view==='list' && typeof renderList==='function') renderList();
})();
