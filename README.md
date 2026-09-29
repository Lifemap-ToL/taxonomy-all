# Lifemap multilingual vernacular taxonomy

This directory contains language-independent source retrieval and matching tools, with language-specific inputs and outputs in folders such as `es/`, `fr/`, and `de/`.

## Separation of responsibilities

- `shared/downloads/` and `shared/extracted/` contain source files shared by every language. They are downloaded once and reused by all language builds.
- `<language>/wikidata.tsv` is a language-specific Wikidata extract created by `download-wikidata <language>`; it is a local build input and is excluded from Git.
- `<language>/sources.json` lists optional sources that apply only to that language.
- Optional source archives are downloaded under `<language>/sources/downloads/`; they are local build inputs and are excluded from Git. The configuration in `sources.json` is tracked.
- `<language>/README.md` documents that language's sources and files; each build refreshes its generated summary section while preserving hand-written notes.
- `<language>/TAXONOMIC-VERNACULAR-<LANG>-LATEST.txt` is the output: NCBI taxid, NCBI scientific name, vernacular name, and contributing source IDs (tab-separated, one name per row). Source IDs identify the source snapshot/version (for example `gbif_YYYY-MM-DD`, `col_YYYY-MM-DD`, `inat_YYYY-MM-DD`, `wikidata_YYYY-MM-DD`, or `inpn_v11`/`inpn_v18`) and are comma-separated when multiple sources supplied the same taxid/name pair.
- The build writes `unmatched.tsv`, listing source rows that could not be linked to an NCBI taxid. This report is tracked in Git.

## What to keep in Git

Track the scripts, this README, each language's `README.md`, `sources.json`, `build-summary.json`, `unmatched.tsv`, and the final `TAXONOMIC-VERNACULAR-<LANG>-LATEST.txt` output. The final files are the deliverables needed by Lifemap and preserve the source snapshot IDs used for each name.

Keep shared downloads and extracted datasets, language-specific downloads, Wikidata extracts, and comparison reports out of Git. These are inputs or local analysis files; the download and build commands can recreate the inputs. `.gitignore` is set up for this split.

The tools use only the Python standard library.

## First Spanish build

Run these separately from inside `taxonomy-all/` so source retrieval is decoupled from processing:

```sh
python -m taxonomy_all download-shared
python -m taxonomy_all download-wikidata es
python -m taxonomy_all build es
```

## Shared and language-specific sources

Every language uses the same shared NCBI, GBIF, Catalogue of Life, and iNaturalist downloads. Some languages may also have a useful regional or national species source. Those sources belong to that language's folder and are listed in its `sources.json`; they are downloaded separately and added to the common build alongside the shared sources and Wikidata records.

For example, French uses INPN TAXREF because it is a relevant French biodiversity source. The `fr/sources.json` entries configure TAXREF v18 and the older v11 archive as separate sources, including URLs, local paths, archive types, and French language codes. v11 is intentionally retained as a historical source because it contains vernacular names absent from newer releases; its names remain visibly attributed to `inpn_v11`. Run the French pipeline from inside `taxonomy-all/` with:

```sh
python -m taxonomy_all download-shared
python -m taxonomy_all download-wikidata fr
python -m taxonomy_all download-language-sources fr
python -m taxonomy_all build fr
```

`download-language-sources fr` retrieves only the optional sources configured for French; it does not download the shared datasets. If a language has no optional sources configured, that command reports this and the build uses its regular sources. Downloading and processing are separate steps so the same shared archives can be reused for every language.

To add an optional source for another language, put its configuration in that language's `sources.json`. If its file format is already supported, the configuration can select the existing adapter. A new format needs a source adapter under `taxonomy_all/sources/` and a corresponding source type in the build. This keeps the language-specific retrieval/parsing isolated while the shared NCBI matching and output logic remains common.

`download-shared` downloads and extracts the NCBI `names.dmp`, `nodes.dmp`, and `merged.dmp`, and downloads the GBIF backbone, Catalogue of Life Extended Release Darwin Core Archive, and iNaturalist taxonomy Darwin Core Archive. These are global datasets reused across language builds. GBIF's backbone is about 926 MB compressed and Catalogue of Life's extended archive is about 654 MB; ensure there is enough disk space. GBIF's published `current` backbone archive was last updated in August 2023, so Catalogue of Life supplies a more recently updated global checklist and vernacular-name source. CoL's Extended Release is used to maximize coverage by integrating additional sources.

Each downloader skips an existing non-empty file. Pass `--force` to replace source downloads. The source archives are snapshots: keep the original archives and note their download dates when preserving a reproducible release.

Wikidata is extracted separately for each language via a saved SPARQL query. The result includes the vernacular name, scientific name, and any available NCBI taxid. Wikidata scientific names are matched to NCBI like other sources; a linked NCBI taxid adds an association only when it gives an additional taxid. GBIF and iNaturalist cross-references are not used to transfer names between sources. The public Wikidata Query Service may time out on broad queries; if it does, rerun the extraction later or split the query. Wikidata recommends dumps rather than WDQS for very large extracts.

## Matching policy

1. NCBI `names.dmp` is the target taxonomy. Scientific names and synonyms are indexed by taxid; `merged.dmp` redirects obsolete taxids.
2. For every source record, match its scientific name exactly (case- and whitespace-normalized) against NCBI names. Keep the vernacular name for every matching taxid. No accepted-name fallback or GBIF/iNaturalist crosswalk is used.
3. Wikidata also supplies NCBI taxids. Those add an association only when the same Wikidata item’s scientific-name match did not already supply that taxid.
4. Records with no matching scientific name and no Wikidata NCBI taxid go to `unmatched.tsv`.
5. Deduplicate only at the end by NCBI taxid and vernacular name (case-insensitive), combining source IDs for that pair. The same vernacular name can therefore appear under multiple taxids.

The build records GBIF, Catalogue of Life, and iNaturalist archive publication/export dates from their metadata, the Wikidata query date, and explicit versions for configured regional sources such as INPN. Before publishing a generated file, review source coverage, unmatched records, and applicable source attribution/licensing.

## Adding a language

Use the same shared downloads and commands with another ISO 639-1 language code, for example:

```sh
python -m taxonomy_all download-wikidata de
python -m taxonomy_all build de
```

The source language filters accept the configured two-letter code and any aliases listed in that language's `sources.json`. An additional language may use only the shared sources or add one or more optional sources in its own `sources.json`. Source formats not yet supported can be added as adapters under `taxonomy_all/sources/`.

## Sources

- NCBI Taxonomy dump: <https://ftp.ncbi.nlm.nih.gov/pub/taxonomy/taxdump.tar.gz>
- GBIF Backbone Darwin Core Archive: <https://hosted-datasets.gbif.org/datasets/backbone/current/backbone.zip> (GBIF Backbone Taxonomy, DOI [10.15468/39omei](https://doi.org/10.15468/39omei), CC BY 4.0; the published `current` archive was last updated 2023-08-28)
- Catalogue of Life latest monthly Extended Release Darwin Core Archive: <https://download.checklistbank.org/col/xr_latest_dwca.zip> (current and archived releases are available from [Catalogue of Life downloads](https://www.catalogueoflife.org/data/download); source names include language metadata and are matched by scientific name like other sources)
- iNaturalist Taxonomy Darwin Core Archive: <https://www.inaturalist.org/taxa/inaturalist-taxonomy.dwca.zip> (updated monthly; see [iNaturalist datasets](https://www.inaturalist.org/pages/developers#datasets))
- INPN TAXREF v18.0: <https://geonature.fr/data/inpn/taxonomie/TAXREF_v18_2025.zip> (the current TAXREF release is listed by [PatriNat](https://www.patrinat.fr/fr/page-temporaire-de-telechargement-des-referentiels-de-donnees-lies-linpn-7353); cite TAXREF and its open license as described on [TAXREF-Web](https://taxref.mnhn.fr/taxref-web/about))
- INPN TAXREF v11.0 (historical archive): <https://geonature.fr/data/inpn/taxonomie/TAXREF_INPN_v11.zip>; retained for vernacular names that may no longer appear in newer releases.
- Wikidata Query Service: <https://query.wikidata.org/sparql>; scientific names use Wikidata property P225 and direct NCBI taxids use property P685.
