(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  if (root) root.ReaderAudio = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';

  const languageAliases = { eng: 'en', amh: 'am', arb: 'ar', orm: 'om', som: 'so', lin: 'ln' };
  function baseLanguage(tag) {
    const base = String(tag || '').toLowerCase().split('-')[0];
    return languageAliases[base] || base;
  }
  function matchingVoices(voices, language) {
    // Do not silently send reader text to network speech services.
    return voices.filter(voice => voice.localService === true
      && !/microsoft|\b(?:sapi|msft)\b/i.test(String(voice.name || '')+' '+String(voice.voiceURI || ''))
      && baseLanguage(voice.lang) === baseLanguage(language));
  }
  function splitText(text, limit = 220) {
    const words = String(text || '').replace(/\s+/gu, ' ').trim();
    let points = Array.from(words);
    const segments = [];
    while (points.length) {
      let end = Math.min(limit, points.length);
      if (end < points.length) {
        const space = points.slice(0, end).lastIndexOf(' ');
        if (space > limit / 2) end = space;
      }
      const segment = points.slice(0, end).join('').trim();
      if (segment) segments.push(segment);
      points = points.slice(end);
      while (points[0] === ' ') points.shift();
    }
    return segments;
  }
  function chapterSegments(chapter) {
    const units = Array.isArray(chapter?.units) ? chapter.units : chapter?.verses || [];
    return units.flatMap(unit => [unit.text, ...(unit.continuations || []).map(part => part.text)]
      .flatMap(text => splitText(text)));
  }
  function narrationPassages(segments) {
    const output=[];
    for(const segment of segments) {
      const last=output.length-1;
      if(last>=0 && output[last].length+segment.length+1<=500)output[last]+=' '+segment;
      else output.push(segment);
    }
    return output;
  }
  function createPlayer({ document, synth, Utterance }) {
    const byId = id => document.getElementById(id);
    const play = byId('reader-audio-play');
    if (!play) return null;
    const pause = byId('reader-audio-pause');
    const stopButton = byId('reader-audio-stop');
    const status = byId('reader-audio-status');
    const language = byId('reader-audio-language');
    const voiceSelect = byId('reader-audio-voice');
    const rate = byId('reader-audio-rate');
    const supported = Boolean(synth && Utterance && typeof synth.speak === 'function');
    let context = null;
    let key = null;
    let voices = [];
    let segments = [];
    let position = 0;
    let generation = 0;
    let playing = false;
    let paused = false;
    let selectedVoice = null;
    let preferredLanguage = null;
    let disposed = false;

    const option = (value, text) => {
      const node = document.createElement('option');
      node.value = value;
      node.textContent = text;
      return node;
    };
    function controls() {
      play.disabled = !supported || !context || !selectedVoice || !segments.length || playing;
      pause.disabled = !playing && !paused;
      pause.textContent = paused ? 'Resume' : 'Pause';
      stopButton.disabled = !playing && !paused;
    }
    function stop(message, reset = true) {
      generation += 1;
      playing = false;
      paused = false;
      if (reset) position = 0;
      if (supported) synth.cancel();
      if (message) status.textContent = message;
      controls();
    }
    function activeLayer() {
      return context?.layers.find(layer => layer.language_tag === language.value);
    }
    function refresh() {
      if (disposed) return;
      const priorVoice = voiceSelect.value;
      const layer = activeLayer();
      voices = supported ? matchingVoices(synth.getVoices(), language.value) : [];
      voiceSelect.replaceChildren(...voices.map((voice, index) => option(String(index), voice.name + ' · ' + voice.lang)));
      const priorIndex = Number(priorVoice);
      voiceSelect.value = voices[priorIndex] ? String(priorIndex) : '0';
      selectedVoice = voices[Number(voiceSelect.value)] || null;
      voiceSelect.disabled = !voices.length;
      segments = chapterSegments(layer?.chapter);
      if(selectedVoice?.neural)segments=narrationPassages(segments);
      if (!supported) {
        status.textContent = 'Read-aloud is not supported in this browser. The written text is still available below.';
      } else if (!context) {
        status.textContent = 'The selected chapter is opening…';
      } else if (!segments.length) {
        status.textContent = 'No text is available to read aloud in this chapter.';
      } else if (!selectedVoice) {
        status.textContent = 'No supported non-Microsoft local voice for ' + (layer?.language || language.value) + '. Choose English narration or another available text language.';
      } else if (!playing && !paused) {
        status.textContent = (layer?.language || language.value) + ' · ready when you are. Press Play to listen.';
      }
      controls();
    }
    function speakNext(token) {
      if (disposed || token !== generation || !playing) return;
      if (position >= segments.length) {
        playing = false;
        position = 0;
        status.textContent = 'Chapter finished. Choose the next chapter whenever you are ready.';
        controls();
        return;
      }
      // Neural voices are application choices, not native SpeechSynthesisVoice
      // objects. Keep their requests out of the browser's typed voice setter.
      const utterance = selectedVoice.neural ? {text:segments[position]} : new Utterance(segments[position]);
      utterance.lang = selectedVoice.lang;
      utterance.voice = selectedVoice;
      utterance.rate = Number(rate.value) || 1;
      utterance.onprogress = message => {if(token===generation && playing)status.textContent=message;};
      utterance.onstart = () => {
        if (token !== generation) return;
        status.textContent = 'Reading ' + (activeLayer()?.language || language.value) + ' · passage ' + (position + 1) + ' of ' + segments.length + '.';
      };
      utterance.onend = () => {
        if (token !== generation || !playing) return;
        position += 1;
        speakNext(token);
      };
      utterance.onerror = event => {
        if (token !== generation) return;
        stop('Read-aloud stopped (' + (event.error || 'device voice unavailable') + '). You can try again or keep reading below.');
      };
      try {
        synth.speak(utterance);
      } catch (error) {
        stop('The device voice could not start. Try again, or keep reading below.');
      }
    }
    function start(reset) {
      if (play.disabled && !paused) return;
      if (reset) position = 0;
      generation += 1;
      synth.cancel();
      // cancel() need not clear a synthesis engine's paused state.
      synth.resume();
      paused = false;
      playing = true;
      controls();
      speakNext(generation);
    }
    const onPlay = () => start(true);
    const onPause = () => {
      if (paused) {
        start(false);
      } else if (playing) {
        const currentPosition = position;
        stop(null, false);
        position = currentPosition;
        paused = true;
        status.textContent = 'Paused. Resume restarts the current short passage.';
        controls();
      }
    };
    const onStop = () => stop('Stopped. Press Play to start this chapter again.');
    const onLanguage = () => { preferredLanguage = language.value; stop(); refresh(); };
    const onVoice = () => { stop(); refresh(); status.textContent = 'Voice selected. Press Play when you are ready.'; };
    const onRate = () => stop('Speed changed. Press Play to start this chapter again.');
    const onVoices = () => { stop(); refresh(); };
    play.addEventListener('click', onPlay);
    pause.addEventListener('click', onPause);
    stopButton.addEventListener('click', onStop);
    language.addEventListener('change', onLanguage);
    voiceSelect.addEventListener('change', onVoice);
    rate.addEventListener('change', onRate);
    synth?.addEventListener?.('voiceschanged', onVoices);
    refresh();
    return {
      prepare(nextKey) {
        if (nextKey === key) return;
        stop();
        key = nextKey;
        context = null;
        selectedVoice = null;
        refresh();
      },
      setContext(next) {
        const previousLanguage = preferredLanguage;
        if (key !== next.key) stop();
        key = next.key;
        context = next;
        language.replaceChildren(...next.layers.map(layer => option(layer.language_tag, layer.language)));
        language.value = next.layers.some(layer => layer.language_tag === previousLanguage)
          ? previousLanguage : (next.layers.find(layer => baseLanguage(layer.language_tag) === 'en') || next.layers[0])?.language_tag || '';
        refresh();
      },
      stop,
      dispose() {
        stop();
        disposed = true;
        synth?.removeEventListener?.('voiceschanged', onVoices);
        play.removeEventListener('click', onPlay);
        pause.removeEventListener('click', onPause);
        stopButton.removeEventListener('click', onStop);
        language.removeEventListener('change', onLanguage);
        voiceSelect.removeEventListener('change', onVoice);
        rate.removeEventListener('change', onRate);
      },
    };
  }
  return { baseLanguage, matchingVoices, splitText, chapterSegments, narrationPassages, createPlayer };
});
