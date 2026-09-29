# English vernacular names

English uses the shared vernacular sources and also enables NCBI `names.dmp` entries with the `common name` name class, configured in `sources.json`. These NCBI names already have taxids, so they are attached directly to those taxids. The source ID in the output is `ncbi_taxdump_<download-date>`.

NCBI's dump does not provide a language tag for each common name. This source uses the `common name` class for English as an NCBI-provided English-name input; names from Catalogue of Life, GBIF, iNaturalist, and Wikidata can add further English names.

<!-- BEGIN AUTO-GENERATED BUILD SUMMARY -->
## Latest build summary (generated)

Build command: `python -m taxonomy_all build en`.

The build read **1 322 492 English-language source records** and wrote **424 657 unique NCBI taxid/vernacular-name pairs** to `TAXONOMIC-VERNACULAR-EN-LATEST.txt`.

| Source snapshot | Input records | NCBI taxid links | Unmatched records |
|---|---:|---:|---:|
| `col_2026-08-26` | 375 996 | 296 931 | 80 176 |
| `gbif_2023-08-28` | 488 172 | 422 999 | 66 065 |
| `inat_2026-09-01` | 310 696 | 244 890 | 66 750 |
| `ncbi_taxdump_2026-09-28` | 13 850 | 13 850 | 0 |
| `wikidata_2026-09-29` | 133 778 | 117 835 | 16 437 |
| **Total** | **1 322 492** | **1 096 505** | **229 428** |

`Input records` are vernacular-name rows read from a source. `NCBI taxid links` count successful source-record-to-NCBI-taxid associations; one source record can link to multiple NCBI taxids. `Unmatched records` are source rows for which the build found no usable NCBI taxid. These columns are not mutually exclusive, so their totals need not add up to the number of input records.

### Files tracked in Git

- `TAXONOMIC-VERNACULAR-EN-LATEST.txt` — backend TSV with four tab-separated columns and no header: NCBI taxid, current NCBI scientific name, vernacular name, and contributing source IDs.
- `build-summary.json` — machine-readable version of the counts above.
- `sources.json` — optional language-specific source configuration.
- `README.md` — this generated section is refreshed by each build; hand-written notes outside this section are preserved.

### Local files excluded from Git

- `unmatched.tsv` — source records that could not be assigned a usable NCBI taxid, with the reason; available locally for review after a build.
- `wikidata.tsv` — language-specific input created by `download-wikidata en` before the build.
- `sources/downloads/` — configured language-specific source archives retrieved by `download-language-sources`.
<!-- END AUTO-GENERATED BUILD SUMMARY -->
