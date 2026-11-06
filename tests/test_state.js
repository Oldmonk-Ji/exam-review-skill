const assert=require('node:assert/strict');
const prepare=require('../scripts/review_state.js');
const qs=[{id:'Q1',type:'mcq',options:['A','B']},{id:'Q3',type:'reveal',options:[]}];
const legacy={Q1:{c:'B',ok:false},Q3:{r:true},Old:{c:'A'}};
const notes={Q1:{bookmark:true},Q3:{text:'My saved draft',bookmark:true},Old:{text:'Ignore'}};
let state=prepare(legacy,notes,qs);
assert.equal(state.answers.Q1.c,'B');assert.equal(state.answers.Q3.r,true);
assert.equal(state.notes.Q3.text,'My saved draft');assert.equal(state.notes.Q1.bookmark,true);
assert.equal(state.answers.Old,undefined);assert.equal(state.notes.Old,undefined);
assert.equal(notes.Q3.text,'My saved draft'); // migration never mutates old notes
state.notes.Q3.text=7;state.notes.Q1.text={unexpected:true};
state=prepare(state,notes,qs);assert.equal(state.notes.Q3.text,'');assert.equal(state.notes.Q1.text,'');
state=prepare({answers:{},notes:{},exam:null},notes,qs);assert.equal(Object.keys(state.notes).length,0); // reset never resurrects legacy drafts
state=prepare({Q1:{c:'Z'}},notes,qs);assert.equal(state.answers.Q1,undefined);
state=prepare(null,notes,qs);assert.equal(state.notes.Q3.text,'My saved draft');
console.log('State migration, ID filtering, invalid choices, damaged drafts and reset isolation: PASS');
