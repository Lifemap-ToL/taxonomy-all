from __future__ import annotations

import csv
from datetime import datetime, timezone
import io
import json
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

from .paths import language_dir

QUERY_TEMPLATE = """
SELECT ?taxon ?vernacularName ?scientificName ?ncbiTaxid WHERE {
  ?taxon wdt:P1843 ?vernacularName .
  FILTER(LANG(?vernacularName) = \"{language}\")
  OPTIONAL { ?taxon wdt:P225 ?scientificName . }
  OPTIONAL { ?taxon wdt:P685 ?ncbiTaxid . }
}
""".strip()


def _write_query_metadata(path: Path, queried_at: str) -> None:
    metadata_path = path.with_name("wikidata-metadata.json")
    metadata_path.write_text(
        json.dumps({"queried_at": queried_at, "query_language": path.parent.name}, indent=2) + "\n",
        encoding="utf-8",
    )


def _normalize_sparql_result(payload: bytes) -> bytes:
    """Return a tab-separated result table from common SPARQL response formats."""
    start = payload.lstrip()
    if start.startswith(b"<?xml") or start.startswith(b"<sparql"):
        root = ET.fromstring(payload)

        def local_name(tag: str) -> str:
            return tag.rsplit("}", 1)[-1]

        variables: list[str] = []
        for element in root.iter():
            if local_name(element.tag) == "variable":
                variable = element.attrib.get("name", "")
                if variable:
                    variables.append(variable)
        output = io.StringIO(newline="")
        writer = csv.writer(output, delimiter="\t", lineterminator="\n")
        writer.writerow(variables)
        for result in root.iter():
            if local_name(result.tag) != "result":
                continue
            values: dict[str, str] = {}
            for binding in result:
                if local_name(binding.tag) != "binding":
                    continue
                value = next((child.text or "" for child in binding), "")
                values[binding.attrib.get("name", "")] = value
            writer.writerow([values.get(variable, "") for variable in variables])
        return output.getvalue().encode("utf-8")

    if start.startswith(b"{"):
        document = json.loads(payload)
        variables = document.get("head", {}).get("vars", [])
        bindings = document.get("results", {}).get("bindings", [])
        output = io.StringIO(newline="")
        writer = csv.writer(output, delimiter="\t", lineterminator="\n")
        writer.writerow(variables)
        for binding in bindings:
            writer.writerow([binding.get(variable, {}).get("value", "") for variable in variables])
        return output.getvalue().encode("utf-8")

    first_line = start.splitlines()[0] if start else b""
    if b"taxon" in first_line and b"vernacularName" in first_line:
        return payload
    raise RuntimeError("Wikidata returned neither SPARQL XML/JSON nor the expected TSV result")


def download_wikidata(language: str, force: bool = False) -> Path:
    code = language.strip().lower()
    destination = language_dir(code) / "wikidata.tsv"
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and destination.stat().st_size and not force:
        existing_mtime = datetime.fromtimestamp(destination.stat().st_mtime, timezone.utc)
        existing = destination.read_bytes()
        try:
            normalized = _normalize_sparql_result(existing)
        except (ET.ParseError, json.JSONDecodeError, RuntimeError):
            normalized = b""
        if normalized:
            if normalized != existing:
                destination.write_bytes(normalized)
                print(f"Converted existing Wikidata response to TSV: {destination}")
            else:
                print(f"Using existing {destination}; pass --force to refresh it")
            metadata_path = destination.with_name("wikidata-metadata.json")
            if not metadata_path.exists():
                _write_query_metadata(destination, existing_mtime.isoformat(timespec="seconds"))
            return destination

    query = QUERY_TEMPLATE.replace("{language}", code)
    url = "https://query.wikidata.org/sparql?" + urllib.parse.urlencode({"query": query, "format": "text/tab-separated-values"})
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "text/tab-separated-values",
            "User-Agent": "LifemapTaxonomyBuilder/1.0 (Wikidata vernacular-name extraction)",
        },
    )
    temporary = destination.with_suffix(".tsv.part")
    print(f"Querying Wikidata for language {code}")
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            payload = response.read()
        if not payload:
            raise RuntimeError("Wikidata returned an empty result")
        temporary.write_bytes(_normalize_sparql_result(payload))
        temporary.replace(destination)
        _write_query_metadata(destination, datetime.now(timezone.utc).isoformat(timespec="seconds"))
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
    print(f"Saved {destination}")
    return destination
