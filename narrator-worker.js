/* Local neural narration; network requests download code/weights, never reader text. */
const MODEL = 'onnx-community/Kokoro-82M-v1.0-ONNX';
const MODEL_REVISION = '1939ad2a8e416c0acfeecc08a694d14ef25f2231';
const VOICE_REVISION = 'f3ff3571791e39611d31c381e3a41a3af07b4987';
const LIBRARY = 'https://esm.sh/kokoro-js@1.2.1?deps=@huggingface/transformers@3.8.1,phonemizer@1.2.1';
const TRANSFORMERS = 'https://esm.sh/@huggingface/transformers@3.8.1';
const WASM = 'https://cdn.jsdelivr.net/npm/onnxruntime-web@1.22.0-dev.20250409-89f8206ba4/dist/';
const VOICES = new Set(['af_heart', 'af_bella', 'bf_emma', 'bm_george']);
let enginePromise = null;
let busy = false;
const originalFetch = self.fetch.bind(self);
self.fetch = (input, options) => {
  const value = typeof input === 'string' ? input : input.url;
  const rewritten = value.replace('https://huggingface.co/hexgrad/Kokoro-82M/resolve/main/voices/',
    `https://huggingface.co/hexgrad/Kokoro-82M/resolve/${VOICE_REVISION}/voices/`);
  return originalFetch(rewritten === value ? input : new Request(rewritten, input instanceof Request ? input : undefined), options);
};

self.onmessage = async event => {
  const {id, text, voice, speed} = event.data || {};
  if (busy || !Number.isInteger(id) || typeof text !== 'string' || text.length > 2200 || !VOICES.has(voice)) {
    self.postMessage({id, type:'error', error:'Invalid or overlapping narration request.'}); return;
  }
  busy = true;
  let lastProgress='', lastTime=0;
  const progress = message => {
    const now=Date.now();
    if(message===lastProgress || (message.startsWith('Loading voice files') && now-lastTime<180))return;
    lastProgress=message;lastTime=now;self.postMessage({id, type:'progress', message});
  };
  try {
    if (!enginePromise) {
      progress('Loading natural voices. First use downloads a ~93 MB model plus support files…');
      enginePromise = (async () => {
        const [{KokoroTTS}, {env, StyleTextToSpeech2Model, AutoTokenizer}] = await Promise.all([
          import(LIBRARY), import(TRANSFORMERS),
        ]);
        env.allowLocalModels = false;
        env.backends.onnx.wasm.numThreads = 1;
        env.backends.onnx.wasm.proxy = false;
        env.backends.onnx.wasm.wasmPaths = WASM;
        const options = {revision:MODEL_REVISION, progress_callback:event => {
          if (event.status === 'progress' && Number.isFinite(event.progress))
            progress(`Loading voice files · ${event.file || 'model'} · ${Math.round(event.progress)}%`);
        }};
        const [model, tokenizer] = await Promise.all([
          StyleTextToSpeech2Model.from_pretrained(MODEL, {...options, dtype:'q8', device:'wasm'}),
          AutoTokenizer.from_pretrained(MODEL, options),
        ]);
        return new KokoroTTS(model, tokenizer);
      })();
    }
    const engine = await enginePromise;
    progress('Preparing the next spoken passage…');
    const audio = await engine.generate(text, {voice, speed:Math.max(.7,Math.min(1.3,Number(speed)||.95))});
    const samples = new Float32Array(audio.audio);
    if (!samples.length || samples.length > 24000 * 120 || !samples.every(Number.isFinite))
      throw new Error('The voice returned invalid audio.');
    self.postMessage({id, type:'audio', samples, sampleRate:audio.sampling_rate || 24000}, [samples.buffer]);
  } catch (error) {
    enginePromise = null;
    self.postMessage({id, type:'error', error:String(error?.message || error).slice(0,250)});
  } finally {busy = false;}
};
