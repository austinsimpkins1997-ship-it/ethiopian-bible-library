const assert=require('node:assert/strict');
const {createController}=require('../reader-translation.js');
(async()=>{
 const messages=[],results=[];
 let createCalls=0,destroyCalls=0;
 const Translator={availability:async()=> 'available',create:async()=>{createCalls++;return {
  translate:async text=>'English: '+text,destroy(){destroyCalls++;},
 };}};
 const controller=createController({Translator,onProgress:(message,busy)=>messages.push({message,busy}),onResult:value=>results.push(value)});
 const context={key:'a:1',language:'arb',chapter:1,allowed:true,units:[{number:1,text:'First',continuations:[{text:'tail'}]}]};
 controller.setContext(context);assert.equal(createCalls,0,'no automatic model download');
 await controller.run();assert.equal(results.length,1);assert.equal(results[0].chapter.verses[0].text,'English: First tail');
 assert.match(results[0].verification_status,/Unreviewed/);assert.equal(destroyCalls,1);
 controller.setContext({...context,key:'blocked',allowed:false});await controller.run();assert.equal(createCalls,1,'unknown/limited derivative permission must hold preview');
 let release;
 Translator.availability=()=>new Promise(resolve=>{release=resolve;});
 controller.setContext({...context,key:'delayed'});const pending=controller.run();controller.cancel();release('available');await pending;
 assert.equal(results.length,1,'cancelled work must not publish late output');
 Translator.availability=async()=> 'unavailable';await controller.run();assert.equal(createCalls,1);
 assert.match(messages.at(-1).message,/does not support/);
 controller.dispose();console.log('Translation checks passed: explicit start, rights boundary, labels, cancellation, unsupported language and preserved source order.');
})().catch(error=>{console.error(error);process.exitCode=1;});
