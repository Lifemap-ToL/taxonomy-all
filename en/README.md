# English vernacular names

English uses the shared vernacular sources and also enables NCBI `names.dmp` entries with the `common name` name class, configured in `sources.json`. These NCBI names already have taxids, so they are attached directly to those taxids. The source ID in the output is `ncbi_taxdump_<download-date>`.

NCBI's dump does not provide a language tag for each common name. This source uses the `common name` class for English as an NCBI-provided English-name input; names from Catalogue of Life, GBIF, iNaturalist, and Wikidata can add further English names.
