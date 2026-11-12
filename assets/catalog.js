/* SCG日本語ドリル カタログ（ドリル一覧）
   ★ドリルを足すときは drills に1行足す（ready:false＝じゅんびちゅう）。並び順＝課一覧の順＝「つぎの課」の順。
   ポータル(index.html)と各ドリルの共通UI(drill-ui.js)の両方がここを読む。sw.js は network-first（最新が出る）。 */
window.SCG_CATALOG={
  textbooks:[
    {id:'tsunagu', label:'つなぐにほんご', ready:true},
  ],
  drills:[
    {tb:'tsunagu', lesson:'L7', label:'<ruby>辞書形<rt>じしょけい</rt></ruby>', file:'tsunagu/L7-1.html', ready:true},
    {tb:'tsunagu', lesson:'L7', label:'ない<ruby>形<rt>けい</rt></ruby>', file:'tsunagu/L7-2.html', ready:true},
    {tb:'tsunagu', lesson:'L7', label:'い・な<ruby>形容詞<rt>けいようし</rt></ruby>・<ruby>名詞<rt>めいし</rt></ruby>（〜くない・〜じゃない）', file:'tsunagu/L7-3.html', ready:true},
    {tb:'tsunagu', lesson:'L8', label:'た<ruby>形<rt>けい</rt></ruby>', file:'tsunagu/L8-1_ta.html', ready:true},
    {tb:'tsunagu', lesson:'L8', label:'なかった', file:'tsunagu/L8-1_nakatta.html', ready:true},
    {tb:'tsunagu', lesson:'L8', label:'い・な<ruby>形容詞<rt>けいようし</rt></ruby>・<ruby>名詞<rt>めいし</rt></ruby>の<ruby>過去<rt>かこ</rt></ruby>（<ruby>普通形<rt>ふつうけい</rt></ruby>）', file:'tsunagu/L8-2_keiyou.html', ready:true},
    {tb:'tsunagu', lesson:'L8', label:'<ruby>普通形<rt>ふつうけい</rt></ruby>まとめ', file:'tsunagu/L8-2_matome.html', ready:true},
    {tb:'tsunagu', lesson:'L9', label:'て<ruby>形<rt>けい</rt></ruby>', file:'tsunagu/L9.html', ready:true},
    {tb:'tsunagu', lesson:'L10', label:'い・な<ruby>形容詞<rt>けいようし</rt></ruby>の て<ruby>形<rt>けい</rt></ruby>', file:'tsunagu/L10-2_keiyou.html', ready:true},
    {tb:'tsunagu', lesson:'L13', label:'いこう<ruby>形<rt>けい</rt></ruby>（〜(よ)う）', file:'tsunagu/L13-3_ikou.html', ready:true},
    {tb:'tsunagu', lesson:'L14', label:'じょうけん<ruby>形<rt>けい</rt></ruby>（〜ば）', file:'tsunagu/L14-2_jouken.html', ready:true},
    {tb:'tsunagu', lesson:'L14', label:'なければ', file:'tsunagu/L14-2_nakereba.html', ready:true},
    {tb:'tsunagu', lesson:'L15', label:'い・な<ruby>形容詞<rt>けいようし</rt></ruby>・<ruby>名詞<rt>めいし</rt></ruby>の じょうけん<ruby>形<rt>けい</rt></ruby>', file:'tsunagu/L15-1_jouken_keiyou.html', ready:true},
    {tb:'tsunagu', lesson:'L15', label:'くなければ・じゃなければ', file:'tsunagu/L15-1_nakereba_keiyou.html', ready:true},
    {tb:'tsunagu', lesson:'L16', label:'そんけいご（とくべつな ことば）', file:'tsunagu/L16-1_sonkei.html', ready:true},
    {tb:'tsunagu', lesson:'L16', label:'そんけい（お〜になります）', file:'tsunagu/L16-2_sonkei_oninaru.html', ready:true},
    {tb:'tsunagu', lesson:'L16', label:'けんじょうご（とくべつな ことば）', file:'tsunagu/L16-3_kenjou.html', ready:true},
    {tb:'tsunagu', lesson:'L16', label:'けんじょう（お〜します）', file:'tsunagu/L16-4_kenjou_osuru.html', ready:true},
    {tb:'tsunagu', lesson:'L19', label:'かのう<ruby>形<rt>けい</rt></ruby>（できる いいかた）', file:'tsunagu/L19-1_kanou.html', ready:true},
    {tb:'tsunagu', lesson:'L19', label:'うけみ<ruby>形<rt>けい</rt></ruby>（〜される）', file:'tsunagu/L19-3_ukemi.html', ready:true},
    {tb:'tsunagu', lesson:'L23', label:'めいれい<ruby>形<rt>けい</rt></ruby>（まて！・にげろ！）', file:'tsunagu/L23-1_meirei.html', ready:true},
    {tb:'tsunagu', lesson:'L24', label:'そんけい（〜れる・〜られる）', file:'tsunagu/L24-1_sonkei_reru.html', ready:true},
    {tb:'tsunagu', lesson:'L27', label:'しえき<ruby>形<rt>けい</rt></ruby>（〜させます）', file:'tsunagu/L27-3_shieki.html', ready:true},
    {tb:'tsunagu', lesson:'L29', label:'しえきうけみ<ruby>形<rt>けい</rt></ruby>（〜させられます）', file:'tsunagu/L29-1_shiekiukemi.html', ready:true},
  ],
  // ===== JLPT（ホーム「ドリル」→ レベル → 文法・語彙）。ready:false＝じゅんびちゅう =====
  jlpt:[
    {id:'n1', label:'N1', ready:true, items:[
      {label:'<ruby>文法<rt>ぶんぽう</rt></ruby>', count:'<ruby>全<rt>ぜん</rt></ruby> 270<ruby>問<rt>もん</rt></ruby>', file:'jlpt/N1_bunpou.html', ready:true},
      {label:'<ruby>語彙<rt>ごい</rt></ruby>', ready:false},
    ]},
    {id:'n2', label:'N2', ready:true, items:[
      {label:'<ruby>文法<rt>ぶんぽう</rt></ruby>', count:'<ruby>全<rt>ぜん</rt></ruby> 208<ruby>問<rt>もん</rt></ruby>', file:'jlpt/N2_bunpou.html', ready:true},
      {label:'<ruby>語彙<rt>ごい</rt></ruby>', ready:false},
    ]},
    {id:'n3', label:'N3', ready:true, items:[
      {label:'<ruby>文法<rt>ぶんぽう</rt></ruby>', count:'<ruby>全<rt>ぜん</rt></ruby> 149<ruby>問<rt>もん</rt></ruby>', file:'jlpt/N3_bunpou.html', ready:true},
      {label:'<ruby>語彙<rt>ごい</rt></ruby>', count:'<ruby>全<rt>ぜん</rt></ruby> 1830<ruby>語<rt>ご</rt></ruby>', file:'jlpt/N3_goi.html', ready:true},
    ]},
    {id:'n4', label:'N4', ready:true, items:[
      {label:'<ruby>文法<rt>ぶんぽう</rt></ruby>', count:'<ruby>全<rt>ぜん</rt></ruby> 139<ruby>問<rt>もん</rt></ruby>', file:'jlpt/N4_bunpou.html', ready:true},
      {label:'<ruby>語彙<rt>ごい</rt></ruby>', count:'<ruby>全<rt>ぜん</rt></ruby> 622<ruby>語<rt>ご</rt></ruby>', file:'jlpt/N4_goi.html', ready:true},
    ]},
  ]
};
