(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  if (root) root.ReaderTranslation = api;
})(typeof globalThis === 'undefined' ? this : globalThis, function () {
  'use strict';
  function languageTag(tag) {return ({arb:'ar',eng:'en',amh:'am',orm:'om',som:'so',lin:'ln'})[tag] || tag;}
  function createController({Translator, onProgress, onResult}) {
    let context=null, generation=0, translator=null, abort=null;
    function cancel() {
      generation+=1;abort?.abort();abort=null;
      try{translator?.destroy();}catch{} translator=null;
    }
    function setContext(next) {if(context?.key!==next?.key)cancel();context=next;}
    async function run() {
      cancel();const token=generation;const selected=context;
      if(!selected)return;
      if(!selected.allowed){onProgress('The recorded text terms do not establish permission for this preview.',false);return;}
      if(!Translator?.availability || !Translator?.create){onProgress('On-device translation is not supported in this browser. The sourced English reference remains available.',false);return;}
      const parts=selected.units.map(unit=>({number:unit.number ?? unit.unit_order ?? null,
        text:[unit.text,...(unit.continuations || []).map(item=>item.text)].filter(Boolean).join(' ')}));
      if(parts.length>250 || parts.reduce((n,p)=>n+p.text.length,0)>60000){onProgress('This chapter exceeds the preview limit. Use the sourced English reference.',false);return;}
      const options={sourceLanguage:languageTag(selected.language),targetLanguage:'en'};
      const active=()=>token===generation;
      try {
        onProgress('Checking this language pair on your device…',true);
        const availability=await Translator.availability(options);
        if(!active())return;
        if(availability==='unavailable'){onProgress('This device does not support translation from this language. No English wording has been invented. Use the sourced reference.',false);return;}
        abort=new AbortController();
        const created=await Translator.create({...options,signal:abort.signal,monitor(monitor){
          monitor.addEventListener('downloadprogress',event=>{if(active())onProgress(`Downloading on-device translation support · ${Math.round(event.loaded*100)}%`,true);});
        }});
        if(!active()){created.destroy();return;}translator=created;
        const verses=[];
        for(const [index,part] of parts.entries()) {
          if(!active())return;
          onProgress(`Unreviewed machine preview · ${index+1} of ${parts.length} source units…`,true);
          const text=part.text ? await translator.translate(part.text,{signal:abort.signal}) : '';
          if(!active())return;
          if(typeof text!=='string')throw Error('Translation returned an invalid result.');
          verses.push({number:part.number,text});
        }
        if(active()) {onResult({key:selected.key,language:'English machine preview',language_tag:'en',
          chapter:{chapter:selected.chapter,verses},verification_status:'Unreviewed machine-generated study preview; may be wrong. Not published Scripture or a verified translation.'});
          onProgress('Unreviewed machine preview complete. Compare it with the source and a qualified translation.',false);}
      } catch(error) {if(active())onProgress('The preview could not complete. The original text and sourced English reference are unchanged.',false);}
      finally {if(active()){try{translator?.destroy();}catch{}translator=null;abort=null;}}
    }
    return {setContext,run,cancel,dispose:cancel};
  }
  return {languageTag,createController};
});
