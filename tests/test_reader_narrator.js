const assert=require('node:assert/strict');
const {voices,allowedVoice,createSynth}=require('../reader-narrator.js');
const {matchingVoices,narrationPassages}=require('../reader-audio.js');
assert(voices.length>=3);assert(voices.every(v=>v.neural && v.localService && allowedVoice(v)));
const microsoft={name:'Microsoft David',voiceURI:'Microsoft David Desktop',lang:'en-US',localService:true};
assert.equal(allowedVoice(microsoft),false);
assert.equal(allowedVoice({...microsoft,name:'Aria',voiceURI:'urn:microsoft:aria'}),false);
assert.equal(allowedVoice({...microsoft,name:'Aria',voiceURI:'urn:msft:aria'}),false);
assert.equal(matchingVoices([microsoft],'en').length,0);
assert.equal(matchingVoices([{...microsoft,name:'Aria',voiceURI:'urn:msft:aria'}],'en').length,0);
assert.deepEqual(narrationPassages(['One.','Two.']),['One. Two.']);
let instance,started=0,ended=0,cancelled=0,terminated=0,nativeSpoken=0;
class Worker {constructor(){instance=this;} postMessage(data){this.sent=data;} terminate(){terminated++;}}
class AudioContext {
 constructor(){this.destination={};} resume(){return Promise.resolve();} close(){}
 createBuffer(channels,length,rate){return {copyToChannel(){assert.equal(channels,1);assert(length>0);assert(rate>0);}};}
 createBufferSource(){this.source={connect(){},start(){started++;},stop(){cancelled++;}};return this.source;}
}
const synth=createSynth({native:{getVoices:()=>[microsoft],cancel(){},resume(){},speak(){nativeSpoken++;}},Worker,AudioContext});
assert.equal(synth.getVoices().some(v=>/Microsoft/.test(v.name)),false);
synth.resume();const utterance={text:'A quiet place to read.',voice:voices[0],rate:.95,onstart(){},onend(){ended++;},onerror(error){throw Error(error.error);}};
synth.speak(utterance);let first=instance;assert.equal(first.sent.voice,'af_heart');
synth.cancel();assert.equal(terminated,1,'Stop terminates in-progress neural work');
first.onmessage({data:{id:first.sent.id,type:'audio',samples:new Float32Array(24),sampleRate:24000}});
assert.equal(started,0,'late cancelled output cannot play');
synth.speak(utterance);
first.onerror();
assert.equal(terminated,1,'an old worker error cannot cancel the next narration');
instance.onmessage({data:{id:instance.sent.id,type:'audio',samples:new Float32Array(240),sampleRate:24000}});
assert.equal(started,1);assert.equal(nativeSpoken,0,'natural voice never routes to Microsoft/native speech');
synth.cancel();assert.equal(cancelled,1);assert.equal(ended,0);
synth.dispose();console.log('Natural narrator checks passed: Microsoft exclusion, voice catalog, local PCM playback, stop, and stale-result rejection.');
