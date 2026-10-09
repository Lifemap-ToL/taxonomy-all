# Lifemap multilingual vernacular taxonomy

This directory contains language-independent source retrieval and matching tools, with language-specific inputs and outputs in folders such as `es/`, `fr/`, `de/`, and `el/`.

## What this repository does

It combines global and language-specific sources to attach vernacular names to NCBI Taxonomy IDs.

**Shared sources:** NCBI Taxonomy provides the target taxids, scientific names, synonyms, and merged taxids. GBIF Backbone, Catalogue of Life Extended Release, and iNaturalist provide global vernacular names. Wikidata is queried separately for each language and can provide vernacular names, scientific names, and direct NCBI taxids.

**Language-specific sources:** A language can add a useful regional or national source in its `sources.json`. English enables NCBI taxdump's `common name` entries and excludes GBIF because its Backbone snapshot contains French names tagged as English; French uses INPN TAXREF v18. Other languages can use only the shared sources or configure additional sources.

**Matching:** Source scientific names are matched against NCBI scientific names and synonyms after case and whitespace normalization. Every matching NCBI taxid is retained, including multiple taxids for one scientific name. Wikidata's direct NCBI taxid adds a link when the name match did not already provide that link. Duplicate taxid/name pairs are combined, with their source IDs recorded in the output. Names without an NCBI match are reported locally in `unmatched.tsv`.

The final file for each language has four tab-separated columns: NCBI taxid, NCBI scientific name, vernacular name, and source IDs.

## Usage

Run commands from this repository's directory. Shared data is downloaded once and reused for all languages.

| Command | What it does |
|---|---|
| `python -m taxonomy_all download-shared` | Downloads and prepares the shared NCBI, GBIF, Catalogue of Life, and iNaturalist data. |
| `python -m taxonomy_all download-wikidata <language>` | Runs the Wikidata query for a language, for example `es`, and saves its input locally. |
| `python -m taxonomy_all download-language-sources <language>` | Downloads optional configured sources, such as French INPN archives. For English, it checks that the shared NCBI taxdump is ready. |
| `python -m taxonomy_all build <language>` | Builds the final vernacular TSV and build summary, refreshes that language's README, and writes a local unmatched report. |

Existing downloads are reused. Add `--force` to a download command to replace its existing files.

### Example: Spanish

```sh
python -m taxonomy_all download-shared
python -m taxonomy_all download-wikidata es
python -m taxonomy_all build es
```

### Example: Greek

```sh
python -m taxonomy_all download-shared
python -m taxonomy_all download-wikidata el
python -m taxonomy_all build el
```

### Example: French

```sh
python -m taxonomy_all download-shared
python -m taxonomy_all download-wikidata fr
python -m taxonomy_all download-language-sources fr
python -m taxonomy_all build fr
```

### Example: English

```sh
python -m taxonomy_all download-shared
python -m taxonomy_all download-wikidata en
python -m taxonomy_all download-language-sources en
python -m taxonomy_all build en
```

For another language, replace `es` or `fr` with its language code. If it needs an additional source, configure it in that language's `sources.json`.

## Sources

- [NCBI Taxonomy dump](https://ftp.ncbi.nlm.nih.gov/pub/taxonomy/taxdump.tar.gz) — target taxonomy and synonyms; English also uses its `common name` entries.
- [GBIF Backbone](https://hosted-datasets.gbif.org/datasets/backbone/current/backbone.zip) — global taxonomy and vernacular names; the downloaded snapshot is dated 2023-08-28 and is distributed under [CC BY 4.0](https://doi.org/10.15468/39omei).
- [Catalogue of Life Extended Release](https://download.checklistbank.org/col/xr_latest_dwca.zip) — global taxonomy and vernacular names, including names integrated from additional sources.
- [iNaturalist taxonomy archive](https://www.inaturalist.org/taxa/inaturalist-taxonomy.dwca.zip) — taxonomy and vernacular names.
- [Wikidata Query Service](https://query.wikidata.org/sparql) — scientific names (P225), vernacular names, and NCBI taxids (P685).
- [INPN TAXREF v18](https://geonature.fr/data/inpn/taxonomie/TAXREF_v18_2025.zip) — French taxonomic and vernacular names. See [TAXREF terms and attribution](https://taxref.mnhn.fr/taxref-web/about).

## License and attribution

There is no `LICENSE` file, so no reuse license has been selected for the code. The combined data also has no single license declared here: each source dataset keeps its provider's terms. See the links above for source-specific licensing and attribution. Source IDs help identify provenance but do not replace provider attribution requirements.

## Repository contents

After a build, its language folder contains the final output, source configuration, build summary, and language README. The README in each language folder is refreshed by its build.

### Tracked in Git

The repository tracks the scripts, documentation, language source configurations and summaries, and final language TSVs.

### Local build files

Source downloads, language-specific Wikidata extracts, and `unmatched.tsv` are generated or downloaded locally and excluded from Git. They can be recreated with the commands above.
