/* SCG日本語ドリル 共通UI（組み替え） — 全ドリル共通。各ドリルの本体スクリプトの「後」に読み込む。
   ・旧ナビを隠し、新しいヘッダー（‹ 課一覧／課名／Aa／つぎの課）と下のタブバーを作る
   ・各モードの見た目を新デザイン用に組み替える（DOMの移動・ラベル差し替えだけ）
   ・ドリル側の関数（show / rSetAuto / applyZoom）と id はそのまま使う。データ・判定・出題順は触らない
   読み込み前提: assets/catalog.js（ドリル一覧）。無くてもヘッダーは旧ナビのタイトルで動く。 */
(function(){
'use strict';
var D=document;
function $(id){return D.getElementById(id);}
function qa(sel,root){return Array.prototype.slice.call((root||D).querySelectorAll(sel));}
var BASE='/scg-nihongo/';

// ---------- アイコン（線画SVG。stroke=currentColor） ----------
var IC={
  back:'<path d="M15 6l-6 6 6 6"/>',
  fwd:'<path d="M9 6l6 6-6 6"/>',
  rule:'<path d="M4 5h16M4 10h16M4 15h10M4 20h7"/>',
  flip:'<rect x="5" y="3" width="14" height="18" rx="2"/><path d="M9 12h6"/>',
  sort:'<rect x="3" y="3" width="7" height="7" rx="2"/><rect x="14" y="3" width="7" height="7" rx="2"/><rect x="8.5" y="14" width="7" height="7" rx="2"/>',
  rhythm:'<path d="M9 18V5l11-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="17" cy="16" r="3"/>',
  spk:'<path d="M11 5L6 9H3v6h3l5 4z"/><path d="M15.5 8.5a5 5 0 0 1 0 7M18.5 5.5a9 9 0 0 1 0 13"/>',
  spkoff:'<path d="M11 5L6 9H3v6h3l5 4z"/><path d="M16 9l5 6M21 9l-5 6"/>',
  shuffle:'<path d="M16 3h5v5M4 20L21 3M21 16v5h-5M15 15l6 6M4 4l5 5"/>',
  flipall:'<path d="M3 12a9 9 0 0 1 15.5-6.3L21 8M21 3v5h-5M21 12a9 9 0 0 1-15.5 6.3L3 16M3 21v-5h5"/>',
  warn:'<path d="M12 3l10 18H2z"/><path d="M12 10v4M12 17.5v.01"/>',
  down:'<path d="M12 5v14M6 13l6 6 6-6"/>',
  play:'<path d="M7 4.5v15l12-7.5z" fill="currentColor" stroke="none"/>',
  pause:'<rect x="6" y="5" width="4" height="14" rx="1" fill="currentColor" stroke="none"/><rect x="14" y="5" width="4" height="14" rx="1" fill="currentColor" stroke="none"/>'
};
function ic(n){
  return '<svg class="dui-ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="'+(n==='back'?'2.2':'2')
    +'" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'+(IC[n]||IC.rule)+'</svg>';
}

var oldNav=D.querySelector('body > nav');
var screens=qa('.screen');
if(!oldNav||!screens.length) return;   // 想定外の構造なら何もしない（旧UIのまま動く）

// ---------- 自分の位置（カタログ） ----------
var cat=window.SCG_CATALOG||{textbooks:[],drills:[]};
var self=window.SCG_SELF||location.pathname.split('/').slice(-2).join('/');   // 例 tsunagu/L7-1.html
var list=(cat.drills||[]).filter(function(d){return d.ready;});
var idx=-1; list.forEach(function(d,i){ if(d.file===self) idx=i; });
var me=idx>=0?list[idx]:null, next=idx>=0?list[idx+1]:null;
var tbId=me?me.tb:self.split('/')[0];
var tb=(cat.textbooks||[]).filter(function(t){return t.id===tbId;})[0];
var code=self.split('/').pop().replace(/\.html$/,'').split('_')[0];        // L7-1 / L9
var ttlEl=oldNav.querySelector('.ttl small');
var title=me?me.label:(ttlEl?ttlEl.innerHTML.replace(/\s*ドリル\s*$/,''):code);

// ---------- ヘッダー ----------
var hd=D.createElement('header'); hd.className='dui-hd';
hd.innerHTML='<div class="dui-hdrow">'
  +'<a class="dui-ibtn dui-back" href="'+BASE+'#/textbook/'+tbId+'" aria-label="もどる">'+ic('back')+'</a>'
  +'<div class="dui-ttl"><div class="dui-ttl-s">'+(tb?tb.label+' ':'')+code+'</div><div class="dui-ttl-m">'+title+'</div></div>'
  +'<button class="dui-ibtn dui-aa" type="button" aria-label="もじの おおきさ">Aa</button>'
  +(next?'<a class="dui-next" href="'+BASE+next.file+'" aria-label="つぎの課"><span class="dui-nexttx">つぎの<ruby>課<rt>か</rt></ruby></span>'+ic('fwd')+'</a>':'')
  +'</div><div class="dui-prog" hidden><div class="dui-bar"><i></i></div><span class="dui-cnt"></span></div>';
oldNav.parentNode.insertBefore(hd,oldNav);
var prog=hd.querySelector('.dui-prog'), progBar=hd.querySelector('.dui-bar i'), progCnt=hd.querySelector('.dui-cnt');

// ---------- タブバー ----------
var modeBtns=qa('button[data-s]',oldNav);
var tabs=D.createElement('div'); tabs.className='dui-tabs';
var tin=D.createElement('div'); tin.className='dui-tabsin'; tin.setAttribute('role','tablist');
// 文字の長いタブ（じょうけん形の おわり 等）も1行に：各タブは文字の幅以上、残りを等分
tin.style.gridTemplateColumns='repeat('+modeBtns.length+',minmax(max-content,1fr))';
modeBtns.forEach(function(b){
  var t=D.createElement('button'); t.type='button'; t.className='dui-tab'; t.dataset.s=b.dataset.s;
  t.innerHTML=ic(b.dataset.s)+'<span>'+b.innerHTML.replace(/^\s*[①-⑳]\s*/,'')+'</span>';
  t.onclick=function(){ window.show(b.dataset.s); };
  tin.appendChild(t);
});
tabs.appendChild(tin);
D.body.appendChild(tabs);
// PC版（641px以上）：モードの切り替えはヘッダーの中（下のタブバーは CSS で隠す）
var seg=D.createElement('div'); seg.className='dui-seg'; seg.setAttribute('role','tablist');
qa('.dui-tab',tin).forEach(function(t){
  var c=t.cloneNode(true); c.className='dui-segb'; c.onclick=t.onclick; seg.appendChild(c);
});
hd.querySelector('.dui-ttl').insertAdjacentElement('afterend',seg);
function syncTabs(id){ qa('.dui-tab,.dui-segb').forEach(function(t){ if(t.dataset.s===id) t.setAttribute('aria-current','page'); else t.removeAttribute('aria-current'); }); }

// show() を包む：タブバーの選択表示と進捗バーをいっしょに更新
var _show=window.show;
window.show=function(id){ _show(id); syncTabs(id); updProg(); relayout(); };

// ---------- 進捗（グループ分け・リズムのときだけ） ----------
function curId(){ var s=D.querySelector('.screen.on'); return s?s.id:''; }
function pos(){
  var id=curId();
  try{ if(id==='sort') return [sortIdx+1, sortPool.length]; }catch(e){}
  try{ if(id==='sort') return [qIdx+1, qPool.length]; }catch(e){}       // L8-2_matome は名前が q〜
  try{ if(id==='rhythm') return [rIdx+1, rPool.length]; }catch(e){}
  return null;
}
function updProg(){
  var p=pos();
  if(!p||!p[1]){ prog.hidden=true; return; }
  prog.hidden=false; progCnt.textContent=p[0]+' / '+p[1];
  progBar.style.width=Math.min(100,p[0]/p[1]*100)+'%';
}

// ---------- 文字サイズ（Aa＝3段で切り替え）＋投影（PC幅）の拡大 ----------
var STEPS=[1,1.15,1.3], uz=1;
try{ uz=parseFloat(localStorage.getItem('drill_zoom'))||1; }catch(e){}
// PC版は drill-ui.css の @media(min-width:641px) で 1920×1080 基準の寸法にしてあるので、その比率で全体を縮める
function fitF(){ var w=window.innerWidth,h=window.innerHeight; if(w<=640) return 1; return Math.max(0.45,Math.min(w/1920,h/1080,2)); }
window.applyZoom=function(){
  uz=Math.min(1.6,Math.max(0.7,Math.round(uz*100)/100));
  var f=fitF();
  D.body.style.zoom=f; D.body.style.height=(100/f)+'dvh';
  oldNav.style.zoom='';
  screens.forEach(function(s){ s.style.zoom=uz; });
  hd.querySelector('.dui-aa').classList.toggle('on',uz>1.01);
  try{ localStorage.setItem('drill_zoom',uz); }catch(e){}
};
hd.querySelector('.dui-aa').onclick=function(){
  var i=0; STEPS.forEach(function(s,k){ if(Math.abs(s-uz)<0.05) i=k; });
  uz=STEPS[(i+1)%STEPS.length]; window.applyZoom(); relayout();
};
// 文字サイズ・画面幅・モードが変わった時にやり直す物（めくりの文字の縮小、ボタンの文字が入るか）
var relayouts=[];
function relayout(){ requestAnimationFrame(function(){ relayouts.forEach(function(f){ f(); }); }); }
window.addEventListener('resize',relayout);
if(D.fonts&&D.fonts.ready) D.fonts.ready.then(relayout);
// フォントは使う字が出た時に追加で読まれる（サブセット）＝読み終わるたびにやり直す（重い端末で縮小を取りこぼさない）
if(D.fonts&&D.fonts.addEventListener) D.fonts.addEventListener('loadingdone',relayout);
window.addEventListener('resize',window.applyZoom);

// ---------- 文言（スマホ向け：クリック→タップ、キーボード表記は出さない） ----------
function retext(root){
  var w=D.createTreeWalker(root,NodeFilter.SHOW_TEXT,null), n;
  while((n=w.nextNode())){ if(n.nodeValue.indexOf('クリック')>=0) n.nodeValue=n.nodeValue.replace(/クリック/g,'タップ'); }
}
screens.forEach(function(s){
  qa('h2,.hint',s).forEach(retext);
  qa('kbd',s).forEach(function(k){
    var p=k.previousSibling; if(p&&p.nodeType===3) p.nodeValue=p.nodeValue.replace(/／\s*$/,'');
    var nx=k.nextSibling; if(nx&&nx.nodeType===3) nx.nodeValue=nx.nodeValue.replace(/^\s*で/,'で');
    k.remove();
  });
});

// ---------- ① ルール（グループのカード） ----------
qa('.rule').forEach(function(r){
  var g=r.classList.contains('r1')?1:r.classList.contains('r2')?2:r.classList.contains('r3')?3:0;
  var h3=r.querySelector('h3'); if(h3&&g){ h3.classList.add('dui-glabel','dui-bg'+g); }
  var ex=r.querySelector('.ex'); if(!ex) return;
  var lines=ex.innerHTML.split(/<br\s*\/?>/i).map(function(s){return s.trim();}).filter(Boolean);
  if(lines.length<2) return;
  ex.classList.add('dui-exgrid');
  // 長い例（（学校へ）きます → くる 等）が2列で折り返すなら1列にする
  var plainLen=function(h){ return h.replace(/<rt>.*?<\/rt>/g,'').replace(/<[^>]+>/g,'').length; };
  if(Math.max.apply(null,lines.map(plainLen))>11) ex.classList.add('dui-ex1');
  ex.innerHTML=lines.map(function(l){
    l=l.replace(/<span class="v">ま<\/span>/,'ま');
    var k=l.indexOf('→'); var left=k>=0?l.slice(0,k):l, right=k>=0?l.slice(k):'';
    if(g && !/^[（(]〜/.test(left)) left=left.replace(/([ぁ-んー])ます/,'<span class="dui-hl'+g+'">$1</span>ます');
    return '<div>'+left+right+'</div>';
  }).join('');
});
// 新しい形のルール画面（.ru1＝1グループの表、.ru.r2/.r3＝2・3グループのカード）
// 見出しの「1グループ」等を色ラベルにする（カード上端の色帯はやめた＝CSS）
qa('.ru1 > h3, .ru > h3').forEach(function(h){
  h.innerHTML=h.innerHTML.replace(/^\s*([123])グループ/,'<span class="dui-glabel dui-bg$1">$1グループ</span>');
});
// 「段・語尾・例」の表：1行ぶん（.from＋語尾＋例）を束ねる。スマホは 段＋語尾 の下に例を1つずつ縦に（PCは display:contents で元の3列のまま）
function splitEx(el){
  var parts=el.innerHTML.split(/\s*／\s*/);
  // 1つの例の中で折り返すなら矢印の所だけ（例の途中では折り返さない）
  el.innerHTML=parts.map(function(x){
    var k=x.split(/\s*→\s*/);
    var h=k.length===2?'<span class="dui-nw">'+k[0]+'</span> → <span class="dui-nw">'+k[1]+'</span>':x;
    return '<span class="dui-exi">'+h+'</span>';
  }).join('<span class="dui-exsep"> ／ </span>');
}
qa('.onbin').forEach(function(ob){
  var kids=Array.prototype.slice.call(ob.children), row=null, hd=null;
  kids.forEach(function(k){
    if(k.classList.contains('from')||!row){
      row=D.createElement('div'); row.className='dui-onrow';
      hd=D.createElement('div'); hd.className='dui-onhd'; row.appendChild(hd);
      ob.insertBefore(row,k);
    }
    if(k.classList.contains('ex')){ splitEx(k); row.appendChild(k); } else hd.appendChild(k);
  });
});
// 絵文字（⭕❌★⚠）は色つきの文字に（端末で絵がちがう・大きさがそろわないため）。答え合わせの欄（#sortfb）は③の処理が先に読むので除く
var EMO=/[⭕❌★⚠]️?/;
function deEmoji(root){
  var w=D.createTreeWalker(root,NodeFilter.SHOW_TEXT,null), n, hit=[];
  while((n=w.nextNode())){ if(EMO.test(n.nodeValue)&&!(n.parentNode.closest&&n.parentNode.closest('#sortfb,script,style'))) hit.push(n); }
  hit.forEach(function(t){
    var sp=D.createElement('span');
    sp.innerHTML=t.nodeValue.replace(/&/g,'&amp;').replace(/</g,'&lt;')
      .replace(/⭕️?/g,'<b class="dui-mk dui-mko">○</b>').replace(/❌️?/g,'<b class="dui-mk dui-mkx">×</b>')
      .replace(/⚠️?\s*/g,'')
      .replace(/★\s*([^（(]*)/g,'<b class="dui-mk dui-mks">$1</b>');
    while(sp.firstChild) t.parentNode.insertBefore(sp.firstChild,t);
    t.parentNode.removeChild(t);
  });
}
screens.forEach(function(s){
  deEmoji(s);
  new MutationObserver(function(){ deEmoji(s); }).observe(s,{childList:true,subtree:true});
});

qa('.note').forEach(function(nt){
  var b=nt.firstElementChild;
  if(b&&b.tagName==='B'&&/^\s*ちゅうい/.test(b.textContent)&&nt.firstChild===b){
    var hd2=D.createElement('div'); hd2.className='dui-notehd'; hd2.innerHTML=ic('warn')+'<span>ちゅうい：れいがい</span>';
    nt.replaceChild(hd2,b);
  }
  noteBoxes(nt);
});
// ---------- ルールの文：詰め込まない（2026-11-11 スマホ修正まとめ §0・§3） ----------
// 文言は変えず、区切り方だけ変える：話題ごとに小箱（<br>・「…」で区切る）／例は1行に1つ（「／」「。」で区切る）／
// 「（2グループ）」は行の右端の小さな色ラベル／矢印の前後に空白。
function plain(h){ return h.replace(/<rt>[\s\S]*?<\/rt>/g,'').replace(/<[^>]+>/g,'').replace(/&nbsp;/g,' ').trim(); }
function toLines(html){
  // 「（N グループ）と」で並べた組は行を分ける。文の終わり「。」と「／」でも分ける。sep＝前の行と「。」で区切った所
  var out=[];
  // 「／」はかっこの外のものだけ区切りにする（（読まれます／読めます）は1つのまま）
  // タグの中（<span class="v">よかった ／ よくなかった</span> 等）の「／」も区切らない＝タグを途中で切って壊さない
  var d=0, t=0, buf='';
  html.split(/(<[^>]+>)/).forEach(function(seg){
    if(seg.charAt(0)==='<'){
      if(/^<\//.test(seg)) t=Math.max(0,t-1); else if(!/^<(br|img|wbr)\b|\/>$/i.test(seg)) t++;
      buf+=seg; return;
    }
    for(var i=0;i<seg.length;i++){
      var c=seg[i];
      if(c==='（'||c==='(') d++; else if((c==='）'||c===')')&&d>0) d--;
      buf+=(c==='／'&&d===0&&t===0)?'\u0001':c;
    }
  });
  buf.replace(/(グループ）)\s*と\s*/g,'$1\u0001').replace(/。\s*/g,'。\u0002').replace(/\s*\u0001\s*/g,'\u0001')
    .split(/([\u0001\u0002])/).forEach(function(x,i,arr){
      if(x==='\u0001'||x==='\u0002') return;
      var t=x.replace(/^\s+|\s+$/g,''); if(!plain(t)) return;
      out.push({h:t, sep:i>1&&arr[i-1]==='\u0002'});
    });
  return out;
}
function lineHTML(o){
  var h=o.h.replace(/\s*→\s*/g,' → '), tag='';
  var m=h.match(/（([123])グループ）\s*。?\s*$/);
  if(m){ tag='<span class="dui-gtag dui-bg'+m[1]+'">'+m[1]+'</span>'; h=h.slice(0,m.index); }
  // 例の行＝矢印の左右がどちらも短い（14字以内）。説明つきの長い行はふつうに折り返す
  var p=plain(h), sides=p.split(' → '), ex=sides.length===2&&sides[0].length<=14&&sides[1].length<=14;
  if(ex){
    // 例の行：折り返すなら矢印の所だけ（例の途中では折り返さない）
    var k=h.indexOf(' → ');
    h='<span class="dui-nw">'+h.slice(0,k)+'</span> → <span class="dui-nw">'+h.slice(k+3)+'</span>';
  }
  return '<div class="dui-nl'+(ex?' ex':'')+'"><span class="dui-nt">'+h+'</span>'+tag+'</div>';
}
function noteBoxes(nt){
  var hd=nt.querySelector(':scope > .dui-notehd'); if(hd) nt.removeChild(hd);
  var html=nt.innerHTML.replace(/\s*…\s*/g,'<br>');
  var topics=html.split(/<br\s*\/?>/i).map(function(x){return x.trim();}).filter(function(x){return plain(x);});
  var boxes=topics.map(function(t){
    var head='';
    var m=t.match(/^<b>([\s\S]*?)[：:]\s*<\/b>\s*/);
    if(m){ head='<div class="dui-nbh">'+m[1]+'</div>'; t=t.slice(m[0].length); }
    var lines=toLines(t), body='', prevEx=false;
    lines.forEach(function(o,i){
      var l=lineHTML(o), isEx=/class="dui-nl ex"/.test(l);
      if(o.sep&&isEx&&prevEx&&i>0) l=l.replace('class="dui-nl ex"','class="dui-nl ex sep"');
      body+=l; prevEx=isEx;
    });
    return '<div class="dui-nbox">'+head+body+'</div>';
  });
  // 説明の1文だけの箱のすぐ後に、例だけの箱が続く時は1つにまとめて、説明を見出しにする（L7-1「い段でも 2グループ…」）
  for(var i=boxes.length-2;i>=0;i--){
    var a=boxes[i], b=boxes[i+1];
    var aOne=/^<div class="dui-nbox"><div class="dui-nl"><span class="dui-nt">([\s\S]*?)<\/span><\/div><\/div>$/.exec(a);
    var bAllEx=!/dui-nbh/.test(b)&&!/class="dui-nl"(?! ex)/.test(b.replace(/class="dui-nl ex[^"]*"/g,''));
    if(aOne&&bAllEx) boxes.splice(i,2,b.replace('<div class="dui-nbox">','<div class="dui-nbox"><div class="dui-nbh">'+aOne[1]+'</div>'));
  }
  nt.innerHTML=boxes.join('');
  if(hd) nt.insertBefore(hd,nt.firstChild);
  nt.classList.add('dui-notes');
}
// ルール画面の矢印は前後に空白（「みます → みる」）
(function(){
  var r=$('rule'); if(!r) return;
  var w=D.createTreeWalker(r,NodeFilter.SHOW_TEXT,null), n;
  while((n=w.nextNode())){ if(n.nodeValue.indexOf('→')>=0) n.nodeValue=n.nodeValue.replace(/[ 　]*→[ 　]*/g,' → '); }
})();
// カードの中の「／」でつないだ例も1行に1つ（L7・L8 の 2/3グループ カード、L16-2 の とくべつな ことば 等）
qa('#rule .ru > .big, #rule .ru1 > .big').forEach(function(el){
  if(el.innerHTML.indexOf('／')<0&&el.innerHTML.indexOf('→')<0) return;
  el.innerHTML=el.innerHTML.split(/<br\s*\/?>/i).map(function(seg){
    if(/／/.test(seg)) return toLines(seg).map(lineHTML).join('');
    return /→/.test(seg) ? lineHTML({h:seg.trim()}) : '<div>'+seg+'</div>';
  }).join('');
  el.classList.add('dui-lines');
});

// ---------- ② めくり ----------
(function(){
  var shuf=$('flipshuffle'), grid=$('flipgrid'); if(!shuf||!grid) return;
  shuf.innerHTML=ic('shuffle')+'<span>シャッフル</span>';
  var all=D.createElement('button'); all.type='button'; all.className='dui-flipall';
  shuf.parentNode.insertBefore(all,shuf.nextSibling);
  function allOpen(){ var c=qa('.fcard',grid); return c.length&&c.every(function(x){return x.classList.contains('flip');}); }
  function paint(){ all.innerHTML=ic('flipall')+'<span>'+(allOpen()?'ぜんぶ もどす':'ぜんぶ めくる')+'</span>'; }
  all.onclick=function(){ var open=!allOpen(); qa('.fcard',grid).forEach(function(c){ c.classList.toggle('flip',open); }); paint(); };
  grid.addEventListener('click',function(){ setTimeout(paint,0); });
  new MutationObserver(paint).observe(grid,{childList:true});
  paint();
  // カードの文字をカードの内側（余白を除く）に収まるまで縮める。Aa 130% でも働く
  function fitOne(face){
    var wrap=face.querySelector(':scope > .fitwrap');
    if(!wrap){
      wrap=D.createElement('span'); wrap.className='fitwrap';
      while(face.firstChild) wrap.appendChild(face.firstChild);
      face.appendChild(wrap);
    }
    wrap.style.transform='';
    var cs=getComputedStyle(face);
    var aw=face.clientWidth-parseFloat(cs.paddingLeft)-parseFloat(cs.paddingRight)-12;
    var ah=face.clientHeight-parseFloat(cs.paddingTop)-parseFloat(cs.paddingBottom)-6;
    var w=Math.max(wrap.offsetWidth,wrap.scrollWidth), h=Math.max(wrap.offsetHeight,wrap.scrollHeight);
    if(aw<=0||!w) return;                  // 非表示中（0px）はとばす
    var s=Math.min(aw/w, ah/h, 1);
    if(s<1) wrap.style.transform='scale('+s.toFixed(3)+')';
  }
  function fitAll(){ qa('.face',grid).forEach(fitOne); }
  function fitBtns(){
    [shuf,all].forEach(function(b){
      b.classList.remove('dui-icononly');
      var sp=b.querySelector('span'); if(!sp) return;
      b.setAttribute('aria-label',sp.textContent);
      // 文字が2行に割れる（高さが1行ぶんを超える）か、はみ出すならアイコンだけ
      if(sp.offsetHeight>parseFloat(getComputedStyle(sp).fontSize)*1.9||b.scrollWidth>b.clientWidth+1) b.classList.add('dui-icononly');
    });
  }
  relayouts.push(fitAll,fitBtns);
  new MutationObserver(function(){ relayout(); }).observe(grid,{childList:true});
  var _paint=paint; paint=function(){ _paint(); fitBtns(); };
  if('IntersectionObserver' in window){
    new IntersectionObserver(function(es){ if(es.some(function(e){return e.isIntersecting;})) relayout(); }).observe(grid);
  }
  window.addEventListener('orientationchange',relayout);
  // カードの並び（grid）の大きさが変わったら（表示された・Aa・回転・フォントの読み込み）やり直す＝取りこぼし防止
  if('ResizeObserver' in window) new ResizeObserver(function(){ relayout(); }).observe(grid);
  relayout();
})();

// ---------- ③ グループ分け ----------
(function(){
  var sortq=$('sortq'), fb=$('sortfb'), wrap=D.querySelector('#sort .sortwrap'), nextB=$('sortnext');
  if(!sortq||!fb||!wrap) return;
  var box=D.createElement('div'); box.className='dui-qbox';
  sortq.parentNode.insertBefore(box,sortq); box.appendChild(sortq); box.appendChild(fb);
  var ch=wrap.querySelector('.choices');
  if(ch) qa('button',ch).forEach(function(b){
    var m=b.textContent.trim().match(/^([123])グループ$/);
    if(m) b.innerHTML='<span class="dui-gn">'+m[1]+'</span><span class="dui-gs">グループ</span>';
  });
  if(nextB){
    nextB.classList.add('dui-nextbig'); nextB.innerHTML='つぎへ'+ic('fwd');
    if(ch) ch.parentNode.insertBefore(nextB,ch.nextSibling);
  }
  // 選択肢の文字が3行以上に細切れになるなら、1つずつ全幅で並べる（L29-1「させられます・こさせられます」を Aa 130% で 等）
  function fitChoices(){
    if(!ch) return;
    ch.classList.remove('dui-ch1');
    var bad=qa('button',ch).some(function(b){
      var t=b.querySelector('.opt-big'); if(!t||!t.offsetHeight) return false;   // 文字の選択肢（.opt-big）だけ見る
      var cs=getComputedStyle(t), lh=parseFloat(cs.lineHeight)||parseFloat(cs.fontSize)*1.2;
      return t.offsetHeight>lh*2.5;
    });
    if(bad) ch.classList.add('dui-ch1');
  }
  relayouts.push(fitChoices);
  var btns=wrap.querySelector('.sortbtns'), score=$('score');
  if(btns&&score){ btns.insertBefore(score,btns.firstChild); }
  var snd=$('sndtoggle');
  function paintSnd(){
    var on=true; try{ on=soundOn; }catch(e){}
    snd.innerHTML=ic(on?'spk':'spkoff'); snd.setAttribute('aria-label',on?'おと：オン（タップで けす）':'おと：オフ（タップで だす）');
  }
  if(snd){ snd.addEventListener('click',paintSnd); paintSnd(); }
  function onFb(){
    var ok=fb.classList.contains('ok'), ng=fb.classList.contains('ng');
    box.classList.toggle('ok',ok); box.classList.toggle('ng',ng);
    wrap.classList.toggle('dui-answered',ok||ng);
    var t=fb.firstChild;
    if(t&&t.nodeType===3&&/^\s*(⭕|❌|✅|✖)/.test(t.nodeValue)){
      t.nodeValue=t.nodeValue.replace(/^\s*(⭕|❌|✅|✖)️?\s*/,'');
      if(ng){ var v=D.createElement('span'); v.className='dui-verd'; v.textContent='ざんねん…'; fb.insertBefore(v,fb.firstChild); }
    }
    if(score&&!/^せいかい/.test(score.textContent)) score.textContent='せいかい '+score.textContent;
  }
  new MutationObserver(onFb).observe(fb,{attributes:true,attributeFilter:['class'],childList:true});
  if(score) new MutationObserver(function(){ if(!/^せいかい/.test(score.textContent)) score.textContent='せいかい '+score.textContent; }).observe(score,{childList:true});
  new MutationObserver(updProg).observe(sortq,{childList:true,characterData:true,subtree:true});
  onFb();
})();

// ---------- ④ リズム ----------
(function(){
  var rcard=$('rcard'), rsub=$('rsub'), area=$('rhythmarea'); if(!rcard) return;
  if(area){ area.setAttribute('role','button'); area.setAttribute('tabindex','0'); }
  function fix(){
    if(rcard.querySelector('.dui-done')) return;
    var arrow=rcard.querySelector('.arrow');
    if(arrow){ arrow.innerHTML=ic('down'); }
    else{
      rcard.innerHTML=rcard.innerHTML.replace(/\s*<span style="color:\s*var\(--accent\);?">→<\/span>\s*？/,'')
        +'<div class="arrow">'+ic('down')+'</div><span class="dui-q">？</span>';
    }
    var mk=D.createElement('i'); mk.className='dui-done'; mk.hidden=true; rcard.appendChild(mk);
    if(rsub){
      if(!rcard.querySelector('.dui-q')) { /* こたえ表示中 */
        var last=rsub.lastChild;
        if(last&&last.nodeType===3) last.nodeValue=last.nodeValue.replace(/つぎへ\s*→/,'タップで つぎへ');
      } else rsub.textContent='タップで こたえ';
    }
    updProg();
  }
  new MutationObserver(fix).observe(rcard,{childList:true});
  fix();
  var rplay=$('rplay');
  function paintPlay(){
    if(!rplay) return; var on=rplay.classList.contains('on');
    rplay.innerHTML=ic(on?'pause':'play')+'<span>'+(on?'とめる':'じどうで すすむ')+'</span>';
  }
  if(typeof window.rSetAuto==='function'){
    var _rs=window.rSetAuto; window.rSetAuto=function(on){ _rs(on); paintPlay(); };
  }
  paintPlay();
  qa('.rspd').forEach(function(b){
    b.textContent=b.textContent.replace(/\s+/g,'');
    b.addEventListener('click',function(){ qa('.rspd').forEach(function(x){ x.setAttribute('aria-pressed',x.classList.contains('on')?'true':'false'); }); });
    b.setAttribute('aria-pressed',b.classList.contains('on')?'true':'false');
  });
})();

// ---------- ヒント ON/OFF ボタン（👁/🙈 を外して文字だけに） ----------
qa('.hinttoggle').forEach(function(b){
  function strip(){ var t=b.textContent, u=t.replace(/^[\s️\u{1F441}\u{1F648}]+/u,''); if(t!==u) b.textContent=u; }
  new MutationObserver(strip).observe(b,{childList:true,characterData:true,subtree:true}); strip();
});

// ---------- 語の途中で折り返さない（2026-11-12） ----------
// 日本語はどの字の間でも折り返せるので、「い<ruby>形容詞</ruby>」が「い｜形容詞」と割れる。
// 空白・「、」「。」「・」の後と「（」「「」の前を語の切れ目とみなし、1語（ルビや色つきの語を含む）を <dui-w>（nowrap）で包む。
// 長すぎる語（10字超）は包まない＝はみ出さない。
var INL={RUBY:1,SPAN:1,B:1,I:1,S:1,EM:1,STRONG:1};
function wordWrap(el){
  if(!el||el.nodeType!==1||el.tagName==='DUI-W') return;
  if(el.closest('.fcard,.rcard,#sortq,#sortfb,.choices,button,script,style,svg,rt,table')) return;   // 表のマスは縮めたいので包まない
  // flex/grid の箱（.dui-nl 等）は子が1つずつ並ぶ箱なので、まとめずに中へだけ入る（まとめると縮まない塊になってはみ出す）
  var disp=getComputedStyle(el).display;
  // display:contents（.dui-onrow/.dui-onhd＝PCは表の3列・スマホは flex）も同じ扱い
  if(/flex|grid|contents/.test(disp)||el.classList.contains('dui-onhd')||el.classList.contains('dui-onrow')){ Array.prototype.slice.call(el.children).forEach(wordWrap); return; }
  var kids=Array.prototype.slice.call(el.childNodes), pieces=[];
  // 子を「かけら」に分ける：テキストは切れ目で分割、インラインの要素はそのまま1かけら、それ以外は区切り
  kids.forEach(function(n){
    if(n.nodeType===3){
      n.nodeValue.replace(/[^\s、。・（「『]+[、。・]?|[（「『][^\s、。・（「『]*[、。・]?|\s+|[、。・]/g,function(m){ pieces.push({t:m, node:null, src:n}); return m; });
    } else if(n.nodeType===1&&INL[n.tagName]&&!/\s/.test(n.textContent.replace(/\s+$/,''))&&!n.querySelector('br,div')){
      pieces.push({node:n});
    } else {
      pieces.push({brk:true, node:n});
    }
  });
  // かけらを語にまとめ直して、元の子と入れ替える
  var frag=D.createDocumentFragment(), word=[], len=0;
  function flush(){
    if(!word.length) return;
    if(len<=10&&(word.length>1||len>1)){
      if(frag.lastChild) frag.appendChild(D.createElement('wbr'));   // 語と語の間は必ず折り返せるように
      var sp=D.createElement('dui-w');   // 専用のタグ（h2 span 等の既存の指定に当たらないように）
      word.forEach(function(w){ sp.appendChild(w.node||D.createTextNode(w.t)); }); frag.appendChild(sp);
    } else word.forEach(function(w){ frag.appendChild(w.node||D.createTextNode(w.t)); });
    word=[]; len=0;
  }
  pieces.forEach(function(p){
    if(p.brk){ flush(); frag.appendChild(p.node); wordWrap(p.node); return; }
    if(p.t!=null){
      if(/^\s+$/.test(p.t)){ flush(); frag.appendChild(D.createTextNode(p.t)); return; }
      if(/^[（「『]/.test(p.t)) flush();
      word.push(p); len+=p.t.length;
      if(/[、。・]$/.test(p.t)) flush();
      return;
    }
    word.push(p); len+=plain(p.node.innerHTML).length;
  });
  flush();
  while(el.firstChild) el.removeChild(el.firstChild);
  el.appendChild(frag);
}
qa('.screen h2, .screen .hint, #rule').forEach(wordWrap);
qa('.dui-ttl-m').forEach(wordWrap);

// ---------- 初期表示 ----------
window.applyZoom();
syncTabs(curId());
updProg();
relayout();
})();
