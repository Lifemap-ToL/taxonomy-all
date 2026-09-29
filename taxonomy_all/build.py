from __future__ import annotations

import csv
import io
import json
import sys
import xml.etree.ElementTree as ET
import zipfile
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, TextIO

from .paths import EXTRACTED, DOWNLOADS, language_dir

# GBIF DwC-A files can contain fields larger than csv's 128 KiB default.
csv.field_size_limit(sys.maxsize)

GBIF_ARCHIVE = DOWNLOADS / "gbif" / "backbone.zip"
COL_ARCHIVE = DOWNLOADS / "col" / "xr_latest_dwca.zip"
INAT_ARCHIVE = DOWNLOADS / "inat" / "inaturalist-taxonomy.dwca.zip"


def _norm(value: str) -> str:
    return " ".join(value.split()).casefold()


def _header_map(fieldnames: list[str] | None) -> dict[str, str]:
    headers: dict[str, str] = {}
    for name in fieldnames or []:
        key = name.lstrip("\ufeff?").strip().casefold()
        headers[key] = name
        # ChecklistBank DwC-A exports use qualified Darwin Core terms such as
        # ``dwc:taxonID`` and ``dcterms:language`` in their header row.
        if ":" in key:
            headers[key.rsplit(":", 1)[-1]] = name
    return headers


def _get(row: dict[str, str], headers: dict[str, str], *names: str) -> str:
    for name in names:
        actual = headers.get(name.casefold())
        if actual:
            return (row.get(actual) or "").strip()
    return ""


def _open_zip_csv(archive: zipfile.ZipFile, member: str, delimiter: str) -> tuple[TextIO, csv.DictReader]:
    text = io.TextIOWrapper(archive.open(member), encoding="utf-8-sig", errors="replace", newline="")
    reader = csv.DictReader(text, delimiter=delimiter)
    return text, reader


@dataclass(frozen=True)
class VernacularRecord:
    source: str
    source_id: str
    scientific_name: str
    name: str
    direct_ncbi: str = ""


@dataclass
class NCBIIndex:
    scientific: dict[str, str]
    names: dict[str, set[str]]
    merged: dict[str, str]

    @classmethod
    def load(cls) -> "NCBIIndex":
        directory = EXTRACTED / "ncbi"
        scientific: dict[str, str] = {}
        names: dict[str, set[str]] = defaultdict(set)
        with (directory / "names.dmp").open(encoding="utf-8", errors="replace") as source:
            for line in source:
                parts = [part.strip() for part in line.split("|")]
                if len(parts) < 4:
                    continue
                taxid, name, name_class = parts[0], parts[1], parts[3]
                if not taxid or not name:
                    continue
                names[_norm(name)].add(taxid)
                if name_class == "scientific name":
                    scientific[taxid] = name
        merged: dict[str, str] = {}
        merged_file = directory / "merged.dmp"
        if merged_file.exists():
            with merged_file.open(encoding="utf-8", errors="replace") as source:
                for line in source:
                    parts = [part.strip() for part in line.split("|")]
                    if len(parts) >= 2 and parts[0] and parts[1]:
                        merged[parts[0]] = parts[1]
        return cls(scientific=scientific, names=dict(names), merged=merged)

    def current_taxid(self, taxid: str) -> str:
        current = str(taxid).strip()
        seen: set[str] = set()
        while current in self.merged and current not in seen:
            seen.add(current)
            current = self.merged[current]
        return current

    def resolve(self, name: str) -> set[str]:
        return {self.current_taxid(taxid) for taxid in self.names.get(_norm(name), set())}


def _language_matches(value: str, language: str, aliases: set[str] | None = None) -> bool:
    value = value.strip().casefold().replace("_", "-")
    code = language.casefold()
    defaults = {
        "es": {"spa", "spanish", "castilian"},
        "fr": {"fra", "fre", "french"},
    }
    accepted = {code, *defaults.get(code, set()), *(alias.casefold() for alias in aliases or set())}
    return value in accepted or any(value.startswith(f"{alias}-") for alias in accepted)


def _archive_source_label(prefix: str, archive_path: Path) -> str:
    """Identify a source archive by its own publication/export date."""
    try:
        with zipfile.ZipFile(archive_path) as archive:
            metadata = next((name for name in archive.namelist() if Path(name).name.casefold() == "eml.xml"), None)
            if metadata:
                root = ET.fromstring(archive.read(metadata))
                for element in root.iter():
                    if element.tag.rsplit("}", 1)[-1].casefold() in {"pubdate", "datestamp"}:
                        value = (element.text or "").strip()
                        if len(value) >= 10 and value[4:5] == "-" and value[7:8] == "-":
                            return f"{prefix}_{value[:10]}"
    except (OSError, zipfile.BadZipFile, ET.ParseError):
        pass
    return f"{prefix}_{datetime.fromtimestamp(archive_path.stat().st_mtime).date().isoformat()}"


def _wikidata_source_label(path: Path) -> str:
    metadata_path = path.with_name("wikidata-metadata.json")
    if metadata_path.exists():
        try:
            queried_at = str(json.loads(metadata_path.read_text(encoding="utf-8")).get("queried_at", ""))
            if len(queried_at) >= 10:
                return f"wikidata_{queried_at[:10]}"
        except (OSError, json.JSONDecodeError):
            pass
    return f"wikidata_{datetime.fromtimestamp(path.stat().st_mtime).date().isoformat()}"


def _wd_fields(path: Path, source_label: str = "wikidata") -> Iterable[VernacularRecord]:
    for row in _wikidata_rows(path):
        taxon_uri = row.get("taxon", "").strip("<>")
        taxon_id = taxon_uri.rstrip("/").rsplit("/", 1)[-1]
        yield VernacularRecord(
            source=source_label,
            source_id=taxon_id,
            scientific_name=row.get("scientificName", ""),
            name=row.get("vernacularName", ""),
            direct_ncbi=row.get("ncbiTaxid", ""),
        )


def _wikidata_rows(path: Path) -> Iterable[dict[str, str]]:
    """Read either a TSV export or the SPARQL XML response used by older runs."""
    with path.open("rb") as source:
        prefix = source.read(256).lstrip()
    if prefix.startswith(b"<?xml") or prefix.startswith(b"<sparql"):
        root = ET.parse(path).getroot()

        def local_name(tag: str) -> str:
            return tag.rsplit("}", 1)[-1]

        for result in root.iter():
            if local_name(result.tag) != "result":
                continue
            row: dict[str, str] = {}
            for binding in result:
                if local_name(binding.tag) != "binding":
                    continue
                name = binding.attrib.get("name", "")
                value = next((child.text or "" for child in binding), "")
                if name:
                    row[name] = value
            yield row
        return

    with path.open(encoding="utf-8-sig", errors="replace", newline="") as source:
        reader = csv.DictReader(source, delimiter="\t")
        headers = _header_map(reader.fieldnames)
        for row in reader:
            yield {key: value or "" for key, value in row.items() if key}


def _dwca_vernacular_records(
    path: Path,
    language: str,
    source_label: str,
    source_name: str,
    language_aliases: set[str] | None = None,
) -> list[VernacularRecord]:
    records: list[VernacularRecord] = []
    with zipfile.ZipFile(path) as archive:
        members = {Path(info.filename).name.casefold(): info.filename for info in archive.infolist() if not info.is_dir()}
        vernacular_member = next((name for base, name in members.items() if base == "vernacularname.tsv"), None)
        taxon_member = next((name for base, name in members.items() if base == "taxon.tsv"), None)
        if not vernacular_member or not taxon_member:
            raise RuntimeError(f"{source_name} archive is missing Taxon.tsv or VernacularName.tsv")

        vernaculars: dict[str, list[str]] = defaultdict(list)
        text, reader = _open_zip_csv(archive, vernacular_member, "\t")
        with text:
            headers = _header_map(reader.fieldnames)
            for row in reader:
                if not _language_matches(_get(row, headers, "language"), language, language_aliases):
                    continue
                taxon_id = _get(row, headers, "taxonid")
                vernacular = _get(row, headers, "vernacularname")
                if taxon_id and vernacular:
                    vernaculars[taxon_id].append(vernacular)

        taxon_info: dict[str, str] = {}
        text, reader = _open_zip_csv(archive, taxon_member, "\t")
        with text:
            headers = _header_map(reader.fieldnames)
            for row in reader:
                taxon_id = _get(row, headers, "taxonid")
                scientific = _get(row, headers, "canonicalname")
                if not scientific:
                    genus = _get(row, headers, "genericname")
                    specific = _get(row, headers, "specificepithet")
                    infraspecific = _get(row, headers, "infraspecificepithet")
                    if genus:
                        scientific = " ".join(part for part in (genus, specific) if part)
                        if infraspecific:
                            rank_marker = {
                                "subspecies": "subsp.",
                                "variety": "var.",
                                "form": "f.",
                            }.get(_get(row, headers, "taxonrank").casefold())
                            scientific = " ".join(
                                part for part in (scientific, rank_marker or "", infraspecific) if part
                            )
                    else:
                        scientific = _get(row, headers, "scientificname")
                if taxon_id:
                    taxon_info[taxon_id] = scientific
        for taxon_id, names in vernaculars.items():
            scientific = taxon_info.get(taxon_id, "")
            if not scientific:
                continue
            for vernacular in names:
                records.append(VernacularRecord(source_label, taxon_id, scientific, vernacular))
    return records


def _gbif_records(
    path: Path,
    language: str,
    language_aliases: set[str] | None = None,
    source_label: str = "gbif",
) -> list[VernacularRecord]:
    return _dwca_vernacular_records(path, language, source_label, "GBIF", language_aliases)


def _col_records(
    path: Path,
    language: str,
    language_aliases: set[str] | None = None,
    source_label: str = "col",
) -> list[VernacularRecord]:
    return _dwca_vernacular_records(path, language, source_label, "Catalogue of Life", language_aliases)


def _inat_records(
    path: Path,
    language: str,
    language_aliases: set[str] | None = None,
    source_label: str = "inat",
) -> list[VernacularRecord]:
    records: list[VernacularRecord] = []
    with zipfile.ZipFile(path) as archive:
        members = [info.filename for info in archive.infolist() if not info.is_dir()]
        taxa_member = next((name for name in members if Path(name).name.casefold() == "taxa.csv"), None)
        vernacular_members = [
            name for name in members
            if "vernacular" in Path(name).name.casefold() and name.casefold().endswith((".csv", ".txt"))
        ]
        if not taxa_member or not vernacular_members:
            raise RuntimeError("iNaturalist archive is missing taxa.csv or vernacular-name files")

        names_by_id: dict[str, list[str]] = defaultdict(list)
        for member in vernacular_members:
            delimiter = "\t" if member.casefold().endswith(".txt") else ","
            text, reader = _open_zip_csv(archive, member, delimiter)
            with text:
                headers = _header_map(reader.fieldnames)
                for row in reader:
                    if not _language_matches(_get(row, headers, "language"), language, language_aliases):
                        continue
                    taxon_id = _get(row, headers, "id", "taxon_id", "taxonid")
                    vernacular = _get(row, headers, "vernacularname", "vernacular_name")
                    if taxon_id and vernacular:
                        names_by_id[taxon_id].append(vernacular)

        text, reader = _open_zip_csv(archive, taxa_member, ",")
        with text:
            headers = _header_map(reader.fieldnames)
            for row in reader:
                taxon_id = _get(row, headers, "id", "taxonid")
                if taxon_id not in names_by_id:
                    continue
                scientific = _get(row, headers, "scientificname", "name")
                if not scientific:
                    continue
                for vernacular in names_by_id[taxon_id]:
                    records.append(VernacularRecord(source_label, taxon_id, scientific, vernacular))
    return records


def _language_specific_records(language: str, lang_dir: Path) -> list[VernacularRecord]:
    config_path = lang_dir / "sources.json"
    if not config_path.exists():
        return []
    config = json.loads(config_path.read_text(encoding="utf-8"))
    records: list[VernacularRecord] = []
    for source in config.get("sources", []):
        if not source.get("enabled", True):
            continue
        source_path = lang_dir / source["file"]
        if not source_path.exists():
            raise FileNotFoundError(
                f"Configured source {source['id']!r} is missing: {source_path}. "
                f"Run `python -m taxonomy_all download-language-sources {language}` first."
            )
        source_type = source["type"]
        if source_type == "inpn_taxref":
            from .sources.inpn import read_taxref_vernaculars

            records.extend(read_taxref_vernaculars(
                source_path,
                source.get("vernacular_language_codes", []),
                source_label=source.get("source_label", source["id"]),
            ))
        else:
            raise ValueError(f"Unsupported language-specific source type {source_type!r} in {config_path}")
    return records


def _language_aliases(lang_dir: Path) -> set[str]:
    config_path = lang_dir / "sources.json"
    if not config_path.exists():
        return set()
    config = json.loads(config_path.read_text(encoding="utf-8"))
    return {str(alias).strip().casefold() for alias in config.get("language_codes", []) if str(alias).strip()}


def _write_tsv(path: Path, header: list[str], rows: Iterable[Iterable[str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as output:
        writer = csv.writer(output, delimiter="\t", lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)


_README_START = "<!-- BEGIN AUTO-GENERATED BUILD SUMMARY -->"
_README_END = "<!-- END AUTO-GENERATED BUILD SUMMARY -->"


def _update_language_readme(lang_dir: Path, summary: dict[str, object]) -> None:
    language = str(summary.get("language", lang_dir.name))
    language_name = {"fr": "French", "es": "Spanish"}.get(language, language.upper())
    output_file = str(summary["backend_tsv"])
    source_records = summary.get("source_records_by_source", {})
    matched_links = summary.get("matched_source_records_by_source", {})
    unmatched_records = summary.get("unmatched_records_by_source", {})
    source_ids = sorted(set(source_records) | set(matched_links) | set(unmatched_records))

    def count(mapping: object, source: str) -> int:
        if not isinstance(mapping, dict):
            return 0
        value = mapping.get(source, 0)
        return int(value) if isinstance(value, (int, float)) else 0

    def format_count(value: int) -> str:
        # Use an unambiguous thousands separator that works across locales.
        return f"{value:,}".replace(",", "\u202f")

    total_records = int(summary.get("source_records", 0))
    total_links = int(summary.get("matched_source_records", 0))
    total_unmatched = int(summary.get("unmatched_records", 0))
    total_pairs = int(summary.get("unique_taxid_name_pairs", 0))
    source_rows = [
        f"| `{source}` | {format_count(count(source_records, source))} | {format_count(count(matched_links, source))} | {format_count(count(unmatched_records, source))} |"
        for source in source_ids
    ]
    source_rows.append(f"| **Total** | **{format_count(total_records)}** | **{format_count(total_links)}** | **{format_count(total_unmatched)}** |")

    generated = "\n".join([
        _README_START,
        "## Latest build summary (generated)",
        "",
        f"Build command: `python -m taxonomy_all build {language}`.",
        "",
        f"The build read **{format_count(total_records)} {language_name}-language source records** and wrote **{format_count(total_pairs)} unique NCBI taxid/vernacular-name pairs** to `{output_file}`.",
        "",
        "| Source snapshot | Input records | NCBI taxid links | Unmatched records |",
        "|---|---:|---:|---:|",
        *source_rows,
        "",
        "`Input records` are vernacular-name rows read from a source. `NCBI taxid links` count successful source-record-to-NCBI-taxid associations; one source record can link to multiple NCBI taxids. `Unmatched records` are source rows for which the build found no usable NCBI taxid. These columns are not mutually exclusive, so their totals need not add up to the number of input records.",
        "",
        "### Files tracked in Git",
        "",
        f"- `{output_file}` — backend TSV with four tab-separated columns and no header: NCBI taxid, current NCBI scientific name, vernacular name, and contributing source IDs.",
        "- `build-summary.json` — machine-readable version of the counts above.",
        "- `sources.json` — optional language-specific source configuration.",
        "- `README.md` — this generated section is refreshed by each build; hand-written notes outside this section are preserved.",
        "",
        "### Local files excluded from Git",
        "",
        "- `unmatched.tsv` — source records that could not be assigned a usable NCBI taxid, with the reason; available locally for review after a build.",
        f"- `wikidata.tsv` — language-specific input created by `download-wikidata {language}` before the build.",
        "- `sources/downloads/` — configured language-specific source archives retrieved by `download-language-sources`.",
        _README_END,
    ])

    readme = lang_dir / "README.md"
    existing = readme.read_text(encoding="utf-8") if readme.exists() else ""
    has_start, has_end = _README_START in existing, _README_END in existing
    if has_start != has_end:
        raise ValueError(f"README has only one generated-section marker: {readme}")
    if has_start:
        start = existing.index(_README_START)
        end = existing.index(_README_END, start) + len(_README_END)
        updated = existing[:start].rstrip() + "\n\n" + generated + "\n" + existing[end:].lstrip("\n")
    else:
        updated = existing.rstrip() + ("\n\n" if existing.strip() else "") + generated + "\n"
    readme.write_text(updated, encoding="utf-8")


def build_language(language: str) -> None:
    code = language.strip().lower()
    lang_dir = language_dir(code)
    shared_ncbi = EXTRACTED / "ncbi"
    wikidata_file = lang_dir / "wikidata.tsv"
    required = [
        shared_ncbi / "names.dmp",
        shared_ncbi / "nodes.dmp",
        GBIF_ARCHIVE,
        COL_ARCHIVE,
        INAT_ARCHIVE,
        wikidata_file,
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing source files; download them first:\n  " + "\n  ".join(missing))
    lang_dir.mkdir(parents=True, exist_ok=True)

    print("Loading NCBI names and synonyms...")
    ncbi = NCBIIndex.load()
    print("Loading Wikidata vernacular names...")
    gbif_source = _archive_source_label("gbif", GBIF_ARCHIVE)
    col_source = _archive_source_label("col", COL_ARCHIVE)
    inat_source = _archive_source_label("inat", INAT_ARCHIVE)
    wikidata_source = _wikidata_source_label(wikidata_file)
    language_aliases = _language_aliases(lang_dir)
    print(f"Reading GBIF vernacular names for {code}...")
    gbif_records = _gbif_records(GBIF_ARCHIVE, code, language_aliases, gbif_source)
    print(f"Reading Catalogue of Life vernacular names for {code}...")
    col_records = _col_records(COL_ARCHIVE, code, language_aliases, col_source)
    print(f"Reading iNaturalist vernacular names for {code}...")
    inat_records = _inat_records(INAT_ARCHIVE, code, language_aliases, inat_source)
    wd_records = list(_wd_fields(wikidata_file, wikidata_source))
    language_records = _language_specific_records(code, lang_dir)
    records = [*gbif_records, *col_records, *inat_records, *wd_records, *language_records]
    print(f"Matching {len(records):,} source records to NCBI...")

    matched_link_count = 0
    matched_links_by_source: Counter[str] = Counter()
    unmatched: list[tuple[str, str, str, str, str]] = []
    final_names: dict[tuple[str, str], str] = {}
    final_sources: dict[tuple[str, str], set[str]] = defaultdict(set)
    for record in records:
        if not record.name:
            continue
        name_candidates = ncbi.resolve(record.scientific_name) if record.scientific_name else set()
        id_candidate = ncbi.current_taxid(record.direct_ncbi) if record.source.startswith("wikidata_") and record.direct_ncbi else ""
        candidates = set(name_candidates)
        if id_candidate in ncbi.scientific:
            candidates.add(id_candidate)

        if candidates:
            for taxid in sorted(candidates):
                canonical = ncbi.scientific.get(taxid)
                if not canonical:
                    unmatched.append((record.source, record.source_id, record.scientific_name, record.name, "NCBI taxid is not present in names.dmp"))
                    continue
                matched_link_count += 1
                matched_links_by_source[record.source] += 1
                key = (taxid, _norm(record.name))
                final_sources[key].add(record.source)
                current = final_names.get(key)
                if current is None or sum(char.isupper() for char in record.name) > sum(char.isupper() for char in current):
                    final_names[key] = record.name
        else:
            unmatched.append((record.source, record.source_id, record.scientific_name, record.name, "no exact NCBI scientific-name or synonym match"))

    output_code = code.upper()
    output_file = lang_dir / f"TAXONOMIC-VERNACULAR-{output_code}-LATEST.txt"
    with output_file.open("w", encoding="utf-8", newline="") as output:
        writer = csv.writer(output, delimiter="\t", lineterminator="\n")
        for key, name in sorted(final_names.items()):
            taxid, _ = key
            writer.writerow((taxid, ncbi.scientific[taxid], name, ",".join(sorted(final_sources[key]))))
    _write_tsv(lang_dir / "unmatched.tsv", ["source", "source_taxon_id", "source_scientific_name", "vernacular_name", "reason"], sorted(unmatched))
    summary = {
        "language": code,
        "source_records": len(records),
        "source_records_by_source": dict(sorted(Counter(record.source for record in records).items())),
        "matched_source_records": matched_link_count,
        "matched_source_records_by_source": dict(sorted(matched_links_by_source.items())),
        "unique_taxid_name_pairs": len(final_names),
        "unmatched_records": len(unmatched),
        "unmatched_records_by_source": dict(sorted(Counter(row[0] for row in unmatched).items())),
        "backend_tsv": output_file.name,
    }
    (lang_dir / "build-summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    _update_language_readme(lang_dir, summary)
    print(json.dumps(summary, indent=2))
