# On-device narrator resources

The site offers synthetic English narration, not a human recording or a
reviewed Scripture pronunciation. Heart is the first choice; Bella, Emma and
George offer alternative American/British English readings. These are library
voice labels, not claims about a real person's identity.

Only an explicit Play starts downloading or synthesizing narration. Text and
generated PCM stay on the device. External hosts receive normal resource
requests (including network metadata); they do not receive the selected text
through this implementation. Playback depends on browser worker/WebAudio/WASM
support, available memory and external resource availability.

## Pinned resources

| Component | Version/revision | Source and terms |
|---|---|---|
| Kokoro JS | 1.2.1 | [library](https://github.com/hexgrad/kokoro/tree/main/kokoro.js), Apache-2.0 |
| Kokoro ONNX weights | 1939ad2a8e416c0acfeecc08a694d14ef25f2231 | [model repository](https://huggingface.co/onnx-community/Kokoro-82M-v1.0-ONNX/tree/1939ad2a8e416c0acfeecc08a694d14ef25f2231), Apache-2.0 |
| Kokoro voice files | f3ff3571791e39611d31c381e3a41a3af07b4987 | [voice repository](https://huggingface.co/hexgrad/Kokoro-82M/tree/f3ff3571791e39611d31c381e3a41a3af07b4987), Apache-2.0 |
| Transformers JS | 3.8.1 | [repository](https://github.com/huggingface/transformers.js/tree/3.8.1), Apache-2.0 |
| Phonemizer | 1.2.1 | [package](https://www.npmjs.com/package/phonemizer/v/1.2.1), Apache-2.0 |
| eSpeak NG phonemization code/data inside Phonemizer | upstream component | [source](https://github.com/espeak-ng/espeak-ng), GPL-3.0-or-later; separate from wrapper license |
| ONNX Runtime Web | 1.22.0-dev.20250409-89f8206ba4 | [source commit](https://github.com/microsoft/onnxruntime/tree/89f8206ba4), MIT |

The quantized model file is 92,361,116 bytes (about 93 MB decimal); JavaScript,
WASM, tokenizer and voice files add further downloads. First preparation can
take time, especially on phones. Subsequent reuse depends on browser caching;
offline narration is not guaranteed. The model is not shipped in the source
ZIP or service-worker shell.

Runtime modules load through esm.sh, WASM through cdn.jsdelivr.net, and model/
voice resources through huggingface.co. Versions and model revisions are pinned
in narrator-worker.js; this is not a signed supply-chain attestation. Local
copies of the relevant licenses are retained alongside this note.

Phonemizer's Apache license describes its wrapper; it does not replace the
embedded eSpeak NG component's GPL terms. See ESPEAK-NG-COPYING.txt, the
[Phonemizer source](https://github.com/xenova/phonemizer.js) and upstream eSpeak
source above. The site does not copy the compiled library into its ZIP or
relicense third-party components under the project's MIT license.

Microsoft **speech voices** are excluded by name/URI, including SAPI aliases.
ONNX Runtime is a permissively licensed inference dependency; using its
runtime does not select a Microsoft speech voice or send text to Microsoft.
Non-English narration uses only an available matching non-Microsoft local
device voice, with an explicit unavailable state when no such voice exists.

Stop terminates an in-progress model worker; changing chapter, language, voice
or speed invalidates pending playback. Pausing restarts the current passage
on Resume. No audio autoplays and no billing service or API key is configured.
