# French vernacular names

French combines the shared GBIF, Catalogue of Life, iNaturalist, and Wikidata inputs with INPN TAXREF v18, configured in `sources.json`.

The INPN source adapter reads each French `TAXREF` row's `LB_NOM` and `NOM_VERN`, and each French `TAXVERN` row's `CD_NOM` scientific name and `LB_VERN`. It compares those scientific names directly with NCBI names and synonyms. It does not redirect names through `CD_REF`, so vernacular names attached to different TAXREF scientific names can remain associated with their distinct NCBI taxids. TAXREF `CD_NOM`/`CD_REF` values are INPN identifiers, not NCBI taxids.

`TAXONOMIC-VERNACULAR-FR-LATEST.txt` has four tab-separated columns: NCBI taxid, NCBI scientific name, vernacular name, and source IDs. Source IDs include the source version or snapshot date, for example `inpn_v18`, `gbif_YYYY-MM-DD`, `col_YYYY-MM-DD`, `inat_YYYY-MM-DD`, and `wikidata_YYYY-MM-DD`. Multiple source IDs are comma-separated. There is one output file, with one row per unique taxid/vernacular-name pair.

## French vernacular names: counts by source

The current output contains 136,932 NCBI taxid/vernacular-name pairs. The table counts output rows by their sole source or, when several sources are listed, in the final row.

| Attribution | Output rows |
|---|---:|
| Catalogue of Life only (`col_2026-08-26`) | 11,536 |
| iNaturalist only (`inat_2026-09-01`) | 9,955 |
| INPN v18 only | 38,055 |
| GBIF only (`gbif_2023-08-28`) | 7,181 |
| Wikidata only (`wikidata_2026-09-28`) | 1,321 |
| Two or more sources | 68,884 |
| **Total** | **136,932** |

Retrieve or refresh the INPN archive separately:

```sh
python -m taxonomy_all download-language-sources fr
```

TAXREF v18.0 is listed as the current version on the PatriNat temporary download page. TAXREF data is released under an open license with attribution; preserve the version and cite it when distributing derived data. See the [TAXREF description and usage terms](https://taxref.mnhn.fr/taxref-web/about).

<!-- BEGIN AUTO-GENERATED BUILD SUMMARY -->
## Latest build summary (generated)

Build command: `python -m taxonomy_all build fr`.

The build read **623 030 French-language source records** and wrote **136 932 unique NCBI taxid/vernacular-name pairs** to `TAXONOMIC-VERNACULAR-FR-LATEST.txt`.

| Source snapshot | Input records | NCBI taxid links | Unmatched records |
|---|---:|---:|---:|
| `col_2026-08-26` | 88 314 | 77 227 | 11 247 |
| `gbif_2023-08-28` | 63 781 | 57 616 | 6 185 |
| `inat_2026-09-01` | 69 880 | 61 348 | 8 725 |
| `inpn_v18` | 375 322 | 137 989 | 238 191 |
| `wikidata_2026-09-28` | 25 733 | 24 100 | 1 684 |
| **Total** | **623 030** | **358 280** | **266 032** |

`Input records` are vernacular-name rows read from a source. `NCBI taxid links` count successful source-record-to-NCBI-taxid associations; one source record can link to multiple NCBI taxids. `Unmatched records` are source rows for which the build found no usable NCBI taxid. These columns are not mutually exclusive, so their totals need not add up to the number of input records.

### Files tracked in Git

- `TAXONOMIC-VERNACULAR-FR-LATEST.txt` — backend TSV with four tab-separated columns and no header: NCBI taxid, current NCBI scientific name, vernacular name, and contributing source IDs.
- `build-summary.json` — machine-readable version of the counts above.
- `sources.json` — optional language-specific source configuration.
- `README.md` — this generated section is refreshed by each build; hand-written notes outside this section are preserved.

### Local files excluded from Git

- `unmatched.tsv` — source records that could not be assigned a usable NCBI taxid, with the reason; available locally for review after a build.
- `wikidata.tsv` — language-specific input created by `download-wikidata fr` before the build.
- `sources/downloads/` — configured language-specific source archives retrieved by `download-language-sources`.
<!-- END AUTO-GENERATED BUILD SUMMARY -->
