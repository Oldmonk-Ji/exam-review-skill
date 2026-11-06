/* Normalize current state and migrate the previous renderer's two storage keys. */
(function(root){
  'use strict';
  function prepareReviewState(raw, legacyNotes, questions){
    function object(v){return v && typeof v==='object' && !Array.isArray(v);}
    var modern=object(raw)&&object(raw.answers)&&object(raw.notes);
    var answers=modern?raw.answers:(object(raw)?raw:{});
    var notes=modern?raw.notes:(object(legacyNotes)?legacyNotes:{});
    var result={version:2, answers:Object.create(null),notes:Object.create(null),exam:null};
    questions.forEach(function(q){
      var a=Object.prototype.hasOwnProperty.call(answers,q.id)&&answers[q.id];
      var n=Object.prototype.hasOwnProperty.call(notes,q.id)&&notes[q.id];
      if(object(a)){
        if(q.type==='reveal'&&a.r===true)result.answers[q.id]={r:true};
        else if(q.type!=='reveal'&&typeof a.c==='string'&&q.options.indexOf(a.c)!==-1)result.answers[q.id]={c:a.c};
      }
      if(object(n))result.notes[q.id]={text:typeof n.text==='string'?n.text:'',bookmark:n.bookmark===true};
    });
    if(modern&&object(raw.exam)&&Number.isFinite(raw.exam.deadline))result.exam={deadline:raw.exam.deadline};
    return result;
  }
  if(typeof module!=='undefined'&&module.exports)module.exports=prepareReviewState;
  else root.prepareReviewState=prepareReviewState;
})(typeof window!=='undefined'?window:globalThis);
