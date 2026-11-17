const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const {buildParallelRows}=require('../reader-alignment.js');
const root=path.resolve(__dirname,'..');
const archive=JSON.parse(fs.readFileSync(path.join(root,'archive.json'),'utf8'));
const records=[];
for (const reader of archive.readers.filter(r=>r.parallel_translation)) {
  const source=reader.chapters;
  const companion=reader.parallel_translation.chapters;
  if(reader.parallel_translation.comparison_policy==='independent_chapters') {
    assert(source.length>0 && companion.length>0);
    for(const chapter of [...source,...companion])assert((chapter.units || chapter.verses || []).some(u=>u.text?.trim()),reader.reader_id+' nonempty independent chapter');
    records.push({reader_id:reader.reader_id,title:reader.title,comparison_policy:'independent_chapters',
      source_pages:source.length,english_chapters:companion.length,chapters:0,paired_rows:null});
    continue;
  }
  assert.equal(source.length,companion.length,reader.reader_id+' chapter counts');
  let sourceOnly=0,englishOnly=0,paired=0;
  for (const chapter of source) {
    const other=companion.find(c=>c.chapter===chapter.chapter);
    assert(other,reader.reader_id+' missing companion chapter '+chapter.chapter);
    const units=chapter.units || chapter.verses || [];
    const verses=other.verses || [];
    assert(units.some(u=>u.text?.trim()),reader.reader_id+' empty source chapter');
    assert(verses.some(u=>u.text?.trim()),reader.reader_id+' empty companion chapter');
    const rows=buildParallelRows(units,verses);
    assert.deepEqual(rows.filter(r=>r.source).map(r=>r.source),units,'source order and every source unit retained');
    assert.equal(rows.filter(r=>r.english).length,verses.length,'every companion unit retained');
    for(const verse of verses) assert.equal(rows.filter(r=>r.english===verse).length,1,'companion unit appears once');
    sourceOnly+=rows.filter(r=>r.source&&!r.english).length;
    englishOnly+=rows.filter(r=>r.english&&!r.source).length;
    paired+=rows.filter(r=>r.source&&r.english).length;
  }
  records.push({reader_id:reader.reader_id,title:reader.title,chapters:source.length,paired_rows:paired,source_only_rows:sourceOnly,english_only_rows:englishOnly});
}
for (const name of ['genesis','exodus','leviticus','numbers','deuteronomy','joshua','judges','ruth','psalms','amos','joel','obadiah','jonah','nahum','zephaniah','haggai','habakkuk','malachi','sirach','samuel-i','samuel-ii','kings-i','kings-ii'])
  assert(records.some(r=>r.reader_id.startsWith(name+'-')),name+' parallel package');
const report={scope:'Technical display coverage only; chapter_pairs counts label-navigation comparisons, not verified alignment. Independent comparisons have no inferred paired rows.',books:records.length,independent_comparisons:records.filter(r=>r.comparison_policy==='independent_chapters').length,chapter_pairs:records.reduce((n,r)=>n+r.chapters,0),records};
fs.mkdirSync(path.join(root,'tmp'),{recursive:true});
fs.writeFileSync(path.join(root,'tmp','parallel-coverage-2026-11-15.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify(report));
