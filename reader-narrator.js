(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  if (root) root.ReaderNarrator = api;
})(typeof globalThis === 'undefined' ? this : globalThis, function () {
  'use strict';
  const voices = [
    {id:'af_heart', name:'Heart · natural American English', lang:'en-US'},
    {id:'af_bella', name:'Bella · natural American English', lang:'en-US'},
    {id:'bf_emma', name:'Emma · natural British English', lang:'en-GB'},
    {id:'bm_george', name:'George · natural British English', lang:'en-GB'},
  ].map(voice=>({...voice, voiceURI:'kokoro:'+voice.id, localService:true, neural:true}));
  function allowedVoice(voice) {
    return !/microsoft|\b(?:sapi|msft)\b/i.test(String(voice?.name || '')+' '+String(voice?.voiceURI || ''));
  }
  function createSynth({native, Worker, AudioContext, workerURL = 'narrator-worker.js'}) {
    let worker = null, context = null, source = null, inflight = false, sequence = 0, current = null;
    let timer = null;
    const supported = Boolean(Worker && AudioContext);
    function cancel() {
      sequence += 1; current = null;
      clearTimeout(timer); timer = null;
      if (source) {source.onended=null; try{source.stop();}catch{} source=null;}
      if (inflight && worker) {worker.terminate();worker=null;}
      inflight = false;
      native?.cancel?.();
    }
    function resume() {
      if (supported) {context ||= new AudioContext(); context.resume().catch(()=>{});}
      native?.resume?.();
    }
    function fail(message) {
      const utterance=current;cancel();utterance?.onerror?.({error:message});
    }
    function speak(utterance) {
      if (!allowedVoice(utterance.voice)) {utterance.onerror?.({error:'Microsoft voices are disabled.'});return;}
      if (!utterance.voice?.neural) {native?.speak(utterance);return;}
      if (!supported) {utterance.onerror?.({error:'Natural narration is unavailable in this browser.'});return;}
      const id=++sequence;current=utterance;inflight=true;
      if (!worker) {
        worker=new Worker(workerURL,{type:'module'});
        const activeWorker=worker;
        worker.onerror=()=>{if(worker===activeWorker && current)fail('Natural voice files could not load. Check the connection and try again.');};
        worker.onmessage=event=>{
          const data=event.data || {};
          if(data.id!==sequence || !current)return;
          if(data.type==='progress'){current.onprogress?.(data.message);return;}
          if(data.type==='error'){fail(data.error);return;}
          if(data.type!=='audio')return;
          clearTimeout(timer);timer=null;inflight=false;
          try {
            const buffer=context.createBuffer(1,data.samples.length,data.sampleRate);
            buffer.copyToChannel(data.samples,0);
            source=context.createBufferSource();source.buffer=buffer;source.connect(context.destination);
            source.onended=()=>{if(data.id===sequence){source=null;const done=current;current=null;done?.onend?.();}};
            source.start();current.onstart?.();
          } catch(error){fail('Audio playback could not start.');}
        };
      }
      timer=setTimeout(()=>fail('Voice preparation timed out. Press Play to retry or choose another voice.'),180000);
      utterance.onprogress?.('Loading the selected natural voice…');
      worker.postMessage({id,text:utterance.text,voice:utterance.voice.id,speed:utterance.rate});
    }
    return {
      getVoices:()=>[...(supported?voices:[]),...(native?.getVoices?.() || []).filter(allowedVoice)],
      speak,cancel,resume,
      addEventListener:(...args)=>native?.addEventListener?.(...args),
      removeEventListener:(...args)=>native?.removeEventListener?.(...args),
      dispose(){cancel();worker?.terminate();worker=null;context?.close?.();},
    };
  }
  return {voices,allowedVoice,createSynth};
});
