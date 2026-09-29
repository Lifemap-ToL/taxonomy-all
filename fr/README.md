# French vernacular names

French combines the shared GBIF, Catalogue of Life, iNaturalist, and Wikidata inputs with INPN TAXREF v18 and v11, both configured in `sources.json`.

The INPN source adapter reads each French `TAXREF` row's `LB_NOM` and `NOM_VERN`, and each French `TAXVERN` row's `CD_NOM` scientific name and `LB_VERN`. It compares those scientific names directly with NCBI names and synonyms. It does not redirect names through `CD_REF`, so vernacular names attached to different TAXREF scientific names can remain associated with their distinct NCBI taxids. TAXREF `CD_NOM`/`CD_REF` values are INPN identifiers, not NCBI taxids.

`TAXONOMIC-VERNACULAR-FR-LATEST.txt` has four tab-separated columns: NCBI taxid, NCBI scientific name, vernacular name, and source IDs. Source IDs include the source version or snapshot date, for example `inpn_v11`, `inpn_v18`, `gbif_YYYY-MM-DD`, `col_YYYY-MM-DD`, `inat_YYYY-MM-DD`, and `wikidata_YYYY-MM-DD`. Multiple source IDs are comma-separated. There is one output file, with one row per unique taxid/vernacular-name pair.

INPN v11 is deliberately retained alongside v18 as a historical source. Some vernacular names present in v11 are absent from v18; keeping both helps preserve those names while making their age and provenance explicit. A v11 name is not thereby asserted to be current in v18.

## French vernacular names: counts by source

The current output contains 114,447 distinct vernacular labels associated with an NCBI taxid. Each label is counted once, ignoring case and repeated whitespace. A label is exclusive to a source when only that source is listed for it across the output; labels reported by multiple sources are counted in the final row.

| Attribution | Number of distinct names |
|---|---:|
| Catalogue of Life only (`col_2026-08-26`) | 10,130 |
| iNaturalist only (`inat_2026-09-01`) | 7,546 |
| INPN v18 only | 8,873 |
| INPN v11 only | 840 |
| GBIF only (`gbif_2023-08-28`) | 4,674 |
| Wikidata only (`wikidata_2026-09-28`) | 783 |
| Two or more sources | 81,601 |
| **Total** | **114,447** |

Retrieve or refresh the INPN archive separately:

```sh
python -m taxonomy_all download-language-sources fr
```

TAXREF v18.0 is listed as the current version on the PatriNat temporary download page. TAXREF data is released under an open license with attribution; preserve the version and cite it when distributing derived data. See the [TAXREF description and usage terms](https://taxref.mnhn.fr/taxref-web/about). The v11 archive is retained as a historical snapshot for vernacular-name coverage.

<!-- BEGIN AUTO-GENERATED BUILD SUMMARY -->
## Latest build summary (generated)

Build command: `python -m taxonomy_all build fr`.

The build read **834 970 French-language source records** and wrote **141 088 unique NCBI taxid/vernacular-name pairs** to `TAXONOMIC-VERNACULAR-FR-LATEST.txt`.

| Source snapshot | Input records | NCBI taxid links | Unmatched records |
|---|---:|---:|---:|
| `col_2026-08-26` | 88 314 | 77 227 | 11 247 |
| `gbif_2023-08-28` | 63 781 | 57 616 | 6 185 |
| `inat_2026-09-01` | 69 880 | 61 348 | 8 725 |
| `inpn_v11` | 211 940 | 80 623 | 131 640 |
| `inpn_v18` | 375 322 | 137 989 | 238 191 |
| `wikidata_2026-09-28` | 25 733 | 24 100 | 1 684 |
| **Total** | **834 970** | **438 903** | **397 672** |

`Input records` are vernacular-name rows read from a source. `NCBI taxid links` are successful source-record-to-NCBI-taxid associations written to `matched-sources.tsv`; one source record can produce links to multiple NCBI taxids. `Unmatched records` are source rows for which the build found no usable NCBI taxid. These columns are not mutually exclusive, so their totals need not add up to the number of input records.

### Files in this language folder

- `TAXONOMIC-VERNACULAR-FR-LATEST.txt` — backend TSV with four tab-separated columns and no header: NCBI taxid, current NCBI scientific name, vernacular name, and contributing source IDs.
- `matched-sources.tsv` — one row for each successful source-record-to-NCBI-taxid link, including source and scientific-name details.
- `unmatched.tsv` — source records that could not be assigned a usable NCBI taxid, with the reason.
- `build-summary.json` — machine-readable version of the counts above.
- `wikidata.tsv` — language-specific Wikidata input used by the build; retrieved separately with `download-wikidata`.
- `sources.json` and `sources/downloads/` — optional language-specific source configuration and downloaded files, when configured.
- `README.md` — this generated section is refreshed by each build; hand-written notes outside this section are preserved.
<!-- END AUTO-GENERATED BUILD SUMMARY -->
