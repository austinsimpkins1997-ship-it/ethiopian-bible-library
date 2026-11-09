# Charles 1902 Jubilees English witness — intake audit

## Identification

R. H. Charles, *The Book of Jubilees, or The Little Genesis*, London: A. & C. Black, 1902. The Internet Archive item identifies the work as translated from Ethiopic, reports 384 scanned pages, and records Tesseract 5.0.0 OCR. See source record `SRC-042` (Google Books), `SRC-043` (Commons scan and territorial notice), and `SRC-044` (Internet Archive item) in the catalogue.

## Local capture integrity

- Captured OCR file: `source-captures/jubilees-charles-1902/bookofjubileesor00char_djvu.txt` (sibling project folder, outside `site/`)
- Bytes: 953,770
- SHA-256: `491e1726cdca207a4bc3a8b6877faed30cb43ba247246354567d43dfd84e35c5`
- Captured text is preserved for research; this audit does not establish that it is complete, accurate, or legally redistributable worldwide.

## Quality review

A spot inspection of the raw OCR shows chapter/page headers such as `CHAPTER I. 10-17`, running page numbers, and Charles's explanatory notes interleaved with the translated text. The file contains 149 `CHAPTER` occurrences and 91 line-start chapter-like page headers; these are OCR/page-layout indicators, not a validated count of scripture boundaries. OCR has substitutions, broken words, and damaged characters. This is insufficient to separate scripture from apparatus or to establish reliable chapter/verse segmentation. No reader JSON has been generated from it.

## Release decision

Keep the Charles English witness as an unbundled research lead. Before adding reader text, compare all 50 chapters and verse sequence against the scanned pages, separate translator text from notes/apparatus, resolve OCR errors, retain printed pagination and numbering, and obtain a jurisdiction-aware reuse determination. “Public domain” marks on a scan do not alone establish worldwide reuse rights. The public site links to the bibliographic/scan evidence but does not expose this raw OCR capture.
