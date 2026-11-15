const assert = require('node:assert/strict');
const audio = require('../reader-audio.js');

assert.equal(audio.baseLanguage('eng'), 'en');
assert.equal(audio.baseLanguage('en-US'), 'en');
assert.equal(audio.baseLanguage('gez'), 'gez');
assert.deepEqual(audio.matchingVoices([
  {name:'Local',lang:'en-GB',localService:true},
  {name:'Cloud',lang:'en-US',localService:false},
  {name:'Unknown',lang:'en-US'},
  {name:'Other language',lang:'de-DE',localService:true},
], 'eng').map(v => v.name), ['Local']);
const long = 'Light travels. '.repeat(90);
const chunks = audio.splitText(long);
assert(chunks.length > 1);
assert(chunks.every(part => Array.from(part).length <= 220));
assert.equal(chunks.join(' '), long.trim());
assert.deepEqual(audio.chapterSegments({units:[{text:'First.'},{text:'Second.'}]}), ['First.', 'Second.']);
assert.deepEqual(audio.chapterSegments({verses:[{text:'Verse.', continuations:[{text:'Continued scripture.'}],
  notes:[{text:'Do not narrate the study note.'}]}]}), ['Verse.', 'Continued scripture.']);

class Element {
  constructor() { this.value=''; this.disabled=false; this.textContent=''; this.handlers=new Map(); this.children=[]; }
  addEventListener(name, fn) { this.handlers.set(name,fn); }
  removeEventListener(name) { this.handlers.delete(name); }
  replaceChildren(...items) { this.children=items; this.value=items[0]?.value || ''; }
  click() { if(!this.disabled) this.handlers.get('click')?.(); }
  change(value) { this.value=value; this.handlers.get('change')?.(); }
}
function fixture(voices, UtteranceType) {
  const ids=['play','pause','stop','status','language','voice','rate'];
  const elements=Object.fromEntries(ids.map(id=>['reader-audio-'+id,new Element()]));
  elements['reader-audio-rate'].value='1';
  const document={getElementById:id=>elements[id],createElement:()=>new Element()};
  let installed=voices;
  const spoken=[];
  const events=new Map();
  const synth={
    getVoices:()=>installed, cancel:()=>{}, resume:()=>{},
    speak:utterance=>{spoken.push(utterance);utterance.onstart?.();},
    addEventListener:(name,fn)=>events.set(name,fn),
    removeEventListener:name=>events.delete(name),
  };
  class Utterance { constructor(text) {this.text=text;} }
  const player=audio.createPlayer({document,synth,Utterance:UtteranceType || Utterance});
  return {elements,player,spoken,install:values=>{installed=values;events.get('voiceschanged')?.();}};
}
const local={name:'Local English',lang:'en-US',localService:true};
const context={key:'ruth:1:parallel',layers:[
  {language_tag:'gez',language:'Geʽez',chapter:{verses:[{text:'Source witness.'}]}},
  {language_tag:'en',language:'English',chapter:{verses:[{text:'First passage.'},{text:'Second passage.'}]}},
]};
{
  const f=fixture([local]);
  f.player.setContext(context);
  assert.equal(f.spoken.length,0,'opening the player must never start audio');
  assert.equal(f.elements['reader-audio-language'].value,'en');
  f.elements['reader-audio-play'].click();
  assert.equal(f.spoken[0].text,'First passage.');
  f.elements['reader-audio-pause'].click();
  const old=f.spoken[0];
  old.onend();
  assert.equal(f.spoken.length,1,'cancelled callbacks cannot advance the queue');
  f.elements['reader-audio-pause'].click();
  assert.equal(f.spoken[1].text,'First passage.','resume restarts only the current short passage');
  f.spoken[1].onend();
  assert.equal(f.spoken[2].text,'Second passage.');
  f.player.prepare('genesis:1:parallel');
  f.spoken[2].onend();
  assert.equal(f.spoken.length,3,'navigation cancels and invalidates old speech');
  assert(f.elements['reader-audio-play'].disabled);
}
{
  const f=fixture([{...local,localService:false}]);
  f.player.setContext(context);
  assert(f.elements['reader-audio-play'].disabled,'network voices are not silently used');
  f.install([local]);
  assert.equal(f.spoken.length,0,'asynchronous voice loading does not autoplay');
  assert(!f.elements['reader-audio-play'].disabled);
  f.elements['reader-audio-language'].change('gez');
  assert(f.elements['reader-audio-play'].disabled,'no unrelated-language fallback for Geʽez');
  f.elements['reader-audio-language'].change('en');
  f.elements['reader-audio-play'].click();
  f.spoken[0].onerror({error:'voice-unavailable'});
  assert.match(f.elements['reader-audio-status'].textContent,/voice-unavailable/);
  assert.equal(f.spoken.length,1,'errors do not trigger an uncontrolled retry');
  f.player.dispose();
}
{
  const f=fixture([local]);
  f.player.setContext({key:'ruth:1:gez',layers:[context.layers[0]]});
  assert(f.elements['reader-audio-play'].disabled);
  f.player.prepare(context.key);
  f.player.setContext(context);
  assert.equal(f.elements['reader-audio-language'].value,'en','returning to parallel chooses English unless an audio preference was explicitly set');
  assert(!f.elements['reader-audio-play'].disabled);
}
{
  const f=fixture([{name:'Local Amharic',lang:'am-ET',localService:true}]);
  f.player.setContext({key:'example:1:amh',layers:[{language_tag:'amh',language:'Amharic',chapter:{verses:[{text:'ሰላም'}]}}]});
  f.elements['reader-audio-play'].click();
  assert.equal(f.spoken[0].text,'ሰላም');
  assert.equal(f.spoken[0].lang,'am-ET','read the selected text with its matching language voice');
}
{
  class NativeUtterance {
    constructor(text) {this.text=text;}
    set voice(value) {if(value.neural)throw new TypeError('Expected a native SpeechSynthesisVoice');}
  }
  const f=fixture([{name:'Heart',lang:'en-US',localService:true,neural:true}],NativeUtterance);
  f.player.setContext(context);
  f.elements['reader-audio-play'].click();
  assert.equal(f.spoken.length,1,'neural requests must bypass the native typed voice field');
  assert.equal(f.spoken[0].text,'First passage. Second passage.');
  assert.equal(f.spoken[0].voice.neural,true);
  f.player.dispose();
}
console.log('Read-aloud checks passed: matching voices, no autoplay, exact text, neural/native boundary, pause/resume, cancellation, errors and unsupported languages.');
