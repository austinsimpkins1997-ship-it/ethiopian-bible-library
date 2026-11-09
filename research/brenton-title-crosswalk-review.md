# Brenton English Septuagint: title-based discovery links

This review connects selected local Brenton USFM research readers to likely Church-list entries so a reader can discover parallel texts from the book cards. It does not identify Brenton's Greek-based English edition with an Ethiopian Orthodox Geʽez witness, establish equivalent contents or boundaries, or add canon-linked reader coverage.

## Evidence and method

- `SRC-029` is the Church's numbered 81-entry English list. Its grouped labels remain grouped.
- `SRC-142` identifies the locally retained Brenton USFM package and records its checksum. The package's `\id` codes and title headings are preserved in the reader records.
- `SRC-384` documents standard USFM book identifiers and Orthodox alternate names. It explicitly distinguishes 1 Samuel/2 Samuel codes `1SA`/`2SA` from 1 Kings/2 Kings codes `1KI`/`2KI`, which may be called Kings/Kingdoms I–IV in Orthodox books; it also identifies `DAG` as the longer Greek Septuagint Daniel.
- `SRC-038` records the provider's 1851/public-domain claim for Brenton's English translation. That claim is not a global legal determination and does not apply to other source layers.

The captured `2KI` member is `13-2KIeng-Brenton.usfm`. Its `\id` line contains only `2KI`, unlike the edition-labeled identifiers in the other parsed members. It is admitted as a Brenton research reader only when the package path, `\id 2KI`, `\toc3 4 Kings`, and `\mt1 KINGS IV.` all match. This explicit exception preserves the source's metadata anomaly; it does not independently prove textual identity or accuracy.

Only work-title/code candidates are surfaced. All are marked `uncertain` in the registry and remain research-only. Component links to grouped Church-list entries are labeled partial; ambiguous Esdras, Jeremiah-associated, and other grouped works remain unmapped.

## Candidate links

| Brenton USFM code | Brenton source heading | Church-list entry | Scope note |
| --- | --- | --- | --- |
| `1SA` | Kings I | I and II Samuel | One candidate component of a grouped entry; not the whole entry |
| `2SA` | Kings II | I and II Samuel | One candidate component of a grouped entry; not the whole entry |
| `1KI` | Kings III | I and II Kings | One candidate component of a grouped entry; not the whole entry |
| `2KI` | Kings IV | I and II Kings | One candidate component of a grouped entry; not the whole entry |
| `1CH` | Chronicles I | I Chronicles | Title/code candidate |
| `2CH` | Chronicles II | II Chronicles | Title/code candidate |
| `EZR` | Ezra and Nehemiah | Ezra and Nehemia | Similar grouped title; numbering, contents, and boundaries unverified |
| `PRO` | Proverbs | Proverbs | Title/code candidate |
| `ECC` | Ecclesiastes | Ecclesiastes | Title/code candidate |
| `SNG` | Song of Solomon | Song of Songs | Standard alternative title; text agreement unverified |
| `JER` | Jeremias | Jeremiah | Standard identifier/title form; order and extent unverified |
| `EZK` | Jezekiel | Ezekiel | Standard identifier/title form; text agreement unverified |
| `HOS` | Osee | Hosea | Standard identifier/title form; text agreement unverified |
| `JOL` | Joel | Joel | Title/code candidate; separate research witness |
| `AMO` | Amos | Amos | Title/code candidate; separate research witness |
| `OBA` | Obdias | Obadiah | Standard title form; text agreement unverified |
| `JON` | Jonas | Jonah | Standard title form; text agreement unverified |
| `MIC` | Michæas | Micah | Standard identifier/title form; text agreement unverified |
| `NAM` | Naum | Nahum | Standard identifier/title form; text agreement unverified |
| `HAB` | Ambacum | Habakkuk | Standard identifier/title form; text agreement unverified |
| `ZEP` | Sophonias | Zephaniah | Kept distinct from `ZEC`/Zechariah |
| `HAG` | Aggæus | Haggai | Standard identifier/title form; text agreement unverified |
| `ZEC` | Zacharias | Zechariah | Kept distinct from `ZEP`/Zephaniah |
| `MAL` | Malachias | Malachi | Standard identifier/title form; text agreement unverified |
| `DAG` | Daniel (Greek) | Daniel | Longer Greek Septuagint witness; additions and boundaries not compared |
| `JDT` | Judith | Judith | Title candidate; not a Geʽez/EOTC edition claim |
| `ESG` | Esther (Greek) | Esther | Greek Esther candidate; lettered labels retained |
| `1MA` | Maccabees I | I Maccabees | Title candidate; witness and boundaries unverified |
| `2MA` | Maccabees II | II and III Maccabees | Candidate for one member of a Church-list grouped entry |
| `3MA` | Maccabees III | II and III Maccabees | Candidate for one member of a Church-list grouped entry |

## Deliberately left unmapped

The Brenton `1ES` (Esdras I) member is not assigned to either Church-list Ezra entry: the archive has not established which local title, numbering system, or work crosswalk applies. `BAR`, `LJE`, and `LAM` are also not assigned to the Church's grouped Jeremiah entry because the 81-entry list does not enumerate those work boundaries. This keeps related names visible in the research catalogue without silently expanding or splitting the Church's list.

The source package structure and parser output are machine-checked, but no full manual collation against Brenton's printed edition, Greek witnesses, Geʽez texts, or current EOTC editions is claimed. See the linked source records for the exact statements and access points.
