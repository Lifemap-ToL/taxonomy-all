from __future__ import annotations

import argparse

from .build import build_language
from .download import download_language_sources, download_shared
from .wikidata import download_wikidata


def main() -> None:
    parser = argparse.ArgumentParser(prog="taxonomy_all")
    subparsers = parser.add_subparsers(dest="command", required=True)

    shared_parser = subparsers.add_parser(
        "download-shared", help="download shared NCBI, GBIF, Catalogue of Life, and iNaturalist sources"
    )
    shared_parser.add_argument("--force", action="store_true", help="replace existing downloads")

    language_sources_parser = subparsers.add_parser(
        "download-language-sources", help="download optional sources configured for one language"
    )
    language_sources_parser.add_argument("language", help="ISO 639-1 language code, e.g. fr")
    language_sources_parser.add_argument("--force", action="store_true", help="replace existing downloads")

    wikidata_parser = subparsers.add_parser("download-wikidata", help="download a language-specific Wikidata extract")
    wikidata_parser.add_argument("language", help="ISO 639-1 language code, e.g. es")
    wikidata_parser.add_argument("--force", action="store_true", help="replace existing extract")

    build_parser = subparsers.add_parser("build", help="build the backend-ready vernacular file")
    build_parser.add_argument("language", help="ISO 639-1 language code, e.g. es")

    args = parser.parse_args()
    if args.command == "download-shared":
        download_shared(force=args.force)
    elif args.command == "download-language-sources":
        download_language_sources(args.language, force=args.force)
    elif args.command == "download-wikidata":
        download_wikidata(args.language, force=args.force)
    elif args.command == "build":
        build_language(args.language)


if __name__ == "__main__":
    main()
