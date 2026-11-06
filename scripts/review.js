/* Offline practice state. Timed practice is a study aid, not secure exam software. */
(function () {
  'use strict';
  var config = window.REVIEW_CONFIG, key = config.storage;
  var qs = Array.from(document.querySelectorAll('.q')), state, timer;
  function empty() { return {answers: Object.create(null), notes: Object.create(null), exam: null}; }
  var raw=null, legacyNotes=null;
  try { raw=JSON.parse(localStorage.getItem(key)); } catch(e) {}
  try { legacyNotes=JSON.parse(localStorage.getItem('notes_'+key.slice('ai_review_'.length))); } catch(e) {}
  state=window.prepareReviewState(raw,legacyNotes,qs.map(function(q){return {id:q.dataset.id,type:q.dataset.type,options:Array.from(q.querySelectorAll('.opt')).map(function(o){return o.dataset.opt;})};}));
  function save() { try { localStorage.setItem(key, JSON.stringify(state)); } catch (e) { document.getElementById('timer') && (document.getElementById('timer').textContent = '浏览器无法保存进度；刷新将丢失本次记录'); } }
  function active() { return !!state.exam; }
  function note(q) { var id=q.dataset.id; if (!state.notes[id] || typeof state.notes[id] !== 'object') state.notes[id]={}; return state.notes[id]; }
  function answer(q) { return state.answers[q.dataset.id] || {}; }
  function paint(q) {
    var a=answer(q), n=note(q), choice=a.c;
    var valid=Array.from(q.querySelectorAll('.opt')).some(function(o){return o.dataset.opt===choice;});
    if (!valid) choice=null;
    q.querySelectorAll('.opt').forEach(function(o){
      o.disabled=!!choice; o.classList.remove('correct','wrong','selected');
      if(choice && active()) o.classList.toggle('selected',o.dataset.opt===choice);
      if(choice && !active()) {o.classList.toggle('correct',o.dataset.opt===q.dataset.answer);o.classList.toggle('wrong',o.dataset.opt===choice && choice!==q.dataset.answer);}
    });
    q.classList.toggle('bookmarked',!!n.bookmark);
    q.querySelector('.sol').classList.toggle('hidden',active() || !(choice || a.r));
    var b=q.querySelector('.rev-btn');if(b)b.textContent=a.r?'收起答案解析 ▴':'点击显示答案解析 ▾';
    var ta=q.querySelector('textarea');if(ta && ta.value!==(n.text||''))ta.value=typeof n.text==='string'?n.text:'';
  }
  function filter() {
    if(!qs.length)return;
    var term=document.getElementById('search').value.toLowerCase(), difficulty=document.getElementById('difficulty').value, mode=document.getElementById('mode').value, shown=0;
    qs.forEach(function(q){
      var a=answer(q), n=note(q);
      // Searching hidden solutions would reveal whether an answer term is present.
      var hay=q.querySelector('.qtext').textContent+' '+q.querySelector('.q-top').textContent+' '+(q.querySelector('.opts')||{textContent:''}).textContent;
      var match=(!term||hay.toLowerCase().includes(term))&&(!difficulty||q.querySelector('.q-top').textContent.includes(difficulty));
      if(mode==='wrong')match=match&&!active()&&!!a.c&&a.c!==q.dataset.answer;
      if(mode==='bookmarked')match=match&&!!n.bookmark;
      if(mode==='unanswered')match=match&&!(a.c||a.r||(n.text||'').trim());
      q.hidden=!match;if(match)shown++;
    });document.getElementById('filter-count').textContent='当前显示 '+shown+' / '+qs.length+' 题';
  }
  function stats() {
    if(!qs.length){document.querySelector('.prog').hidden=true;document.querySelectorAll('.side-n,.side-b,.side-hint').forEach(function(e){e.hidden=true;});return;}
    var done=0, fs=document.getElementById('final-stats');fs.replaceChildren();
    var h=document.createElement('h3');h.textContent='学习记录 · 查看解析不等于掌握';fs.appendChild(h);
    config.sections.forEach(function(section){
      var items=qs.filter(function(q){return q.dataset.sec===section[0];}), d=0, objective=0, correct=0;
      items.forEach(function(q){var a=answer(q);if(q.dataset.type==='reveal'){if(a.r)d++;}else if(a.c){d++;objective++;if(a.c===q.dataset.answer)correct++;}});done+=d;
      var side=document.querySelector('.side-item[data-ch="'+section[0]+'"]');
      if(side){side.querySelector('.side-n').textContent=items.length?d+'/'+items.length:'';side.querySelector('.side-b i').style.width=(items.length?100*d/items.length:0)+'%';side.classList.toggle('done',items.length>0&&d===items.length);}
      if(!items.length)return;
      var row=document.createElement('div');row.className='fs-row';row.textContent=section[1]+'：'+d+'/'+items.length+' 已作答 / 查看解析'+(objective?' · 客观题正确率 '+Math.round(100*correct/objective)+'% ('+correct+'/'+objective+')':'');fs.appendChild(row);
    });
    document.getElementById('head-progress').textContent='进度 '+done+'/'+qs.length;
    document.querySelector('#head-bar i').style.width=100*done/qs.length+'%';
  }
  function refresh(){document.body.classList.toggle('exam-active',active());qs.forEach(paint);stats();filter();}
  qs.forEach(function(q){
    q.querySelectorAll('.opt').forEach(function(o){o.addEventListener('click',function(){if(answer(q).c)return;state.answers[q.dataset.id]={c:o.dataset.opt};save();refresh();});});
    var reveal=q.querySelector('.rev-btn');if(reveal)reveal.addEventListener('click',function(){if(active())return;state.answers[q.dataset.id]={r:!answer(q).r};save();refresh();});
    q.querySelector('.bookmark').addEventListener('click',function(){note(q).bookmark=!note(q).bookmark;save();refresh();});
    var ta=q.querySelector('textarea');if(ta)ta.addEventListener('input',function(){note(q).text=ta.value;save();filter();});
  });
  function examUI(){
    if(!qs.length)return;
    document.getElementById('exam-mode').hidden=active()||!config.examMinutes;
    document.getElementById('finish-exam').hidden=!active();
    document.getElementById('mode').disabled=active();
    if(active())document.getElementById('mode').value='all';
  }
  function end(message){clearInterval(timer);state.exam=null;save();examUI();refresh();document.getElementById('timer').textContent=message;}
  function tick(){if(!active())return;var seconds=Math.max(0,Math.ceil((state.exam.deadline-Date.now())/1000));if(!seconds){end('计时已结束，答案保留；可查看解析。');return;}document.getElementById('timer').textContent='剩余 '+Math.floor(seconds/60)+':'+String(seconds%60).padStart(2,'0');}
  if(qs.length){
    ['search','difficulty','mode'].forEach(function(id){document.getElementById(id).addEventListener('input',filter);});
    document.querySelector('.reset').addEventListener('click',function(){if(active())return;if(!confirm('确定重置全部作答、简答草稿和收藏？此操作无法撤销。'))return;state=empty();save();refresh();});
    document.getElementById('exam-mode').addEventListener('click',function(){
      if(!config.examMinutes||active())return;
      if(!confirm('开始 '+config.examMinutes+' 分钟闭卷练习？将清除本题库已有作答和简答草稿，保留收藏；刷新后计时继续。答案仍存在离线文件中，不适用于正式考试。'))return;
      state.answers=Object.create(null);Object.keys(state.notes).forEach(function(id){state.notes[id]={bookmark:!!state.notes[id].bookmark};});
      state.exam={deadline:Date.now()+config.examMinutes*60000};save();examUI();refresh();tick();timer=setInterval(tick,1000);
    });
    document.getElementById('finish-exam').addEventListener('click',function(){if(confirm('结束闭卷练习并显示已作答题的解析？'))end('练习已结束；可查看解析。');});
  }
  examUI();refresh();if(active()){tick();if(active())timer=setInterval(tick,1000);}
  document.getElementById('theme-btn').addEventListener('click',function(){var root=document.documentElement, current=root.dataset.theme||'auto', next=current==='auto'?'light':current==='light'?'dark':'auto';if(next==='auto')delete root.dataset.theme;else root.dataset.theme=next;this.textContent='主题:'+{auto:'自动',light:'浅色',dark:'深色'}[next];});
  document.addEventListener('DOMContentLoaded',function(){
    var errors=[];
    if(window.renderMathInElement)renderMathInElement(document.body,{delimiters:[{left:'$$',right:'$$',display:true},{left:'$',right:'$',display:false}],throwOnError:false,errorCallback:function(message){errors.push(String(message));}});
    var missing=qs.filter(function(q){return !q.querySelector('.sol-body').textContent.trim()||(q.dataset.type!=='reveal'&&!Array.from(q.querySelectorAll('.opt')).some(function(o){return o.dataset.opt===q.dataset.answer;}));}).map(function(q){return q.dataset.id;});
    var result={questions:qs.length,mcq:qs.filter(function(q){return q.dataset.type==='mcq';}).length,tf:qs.filter(function(q){return q.dataset.type==='tf';}).length,reveal:qs.filter(function(q){return q.dataset.type==='reveal';}).length,katexLoaded:!!window.katex,katexNodes:document.querySelectorAll('.katex').length,katexErrors:Math.max(errors.length,document.querySelectorAll('.katex-error').length),missingAnswers:missing};
    var sc=document.getElementById('selfcheck');sc.textContent=JSON.stringify(result);sc.hidden=!!window.katex&&!result.katexErrors&&!missing.length;
    window.reviewSelfcheck=result;
  });
})();
