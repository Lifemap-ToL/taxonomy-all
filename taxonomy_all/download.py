from __future__ import annotations

import shutil
import tarfile
import urllib.request
import zipfile
import json
from pathlib import Path

from .paths import DOWNLOADS, EXTRACTED, language_dir

SOURCES = {
    "ncbi": "https://ftp.ncbi.nlm.nih.gov/pub/taxonomy/taxdump.tar.gz",
    "gbif": "https://hosted-datasets.gbif.org/datasets/backbone/current/backbone.zip",
    "col": "https://download.checklistbank.org/col/xr_latest_dwca.zip",
    "inat": "https://www.inaturalist.org/taxa/inaturalist-taxonomy.dwca.zip",
}


def _download(url: str, destination: Path, force: bool) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and destination.stat().st_size and not force:
        print(f"Using existing {destination}")
        return
    temporary = destination.with_suffix(destination.suffix + ".part")
    request = urllib.request.Request(url, headers={"User-Agent": "LifemapTaxonomyBuilder/1.0"})
    print(f"Downloading {url} -> {destination}")
    try:
        with urllib.request.urlopen(request, timeout=120) as response, temporary.open("wb") as output:
            shutil.copyfileobj(response, output, length=1024 * 1024)
        if temporary.stat().st_size == 0:
            raise RuntimeError(f"Downloaded an empty file from {url}")
        temporary.replace(destination)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def _extract_ncbi(archive: Path) -> None:
    destination = EXTRACTED / "ncbi"
    destination.mkdir(parents=True, exist_ok=True)
    wanted = {"names.dmp", "nodes.dmp", "merged.dmp"}
    with tarfile.open(archive, "r:gz") as tar:
        for member in tar.getmembers():
            name = Path(member.name).name
            if name in wanted and member.isfile():
                source = tar.extractfile(member)
                if source is None:
                    continue
                target = destination / name
                with source, target.open("wb") as output:
                    shutil.copyfileobj(source, output, length=1024 * 1024)
                print(f"Extracted {target}")
    missing = wanted - {path.name for path in destination.glob("*.dmp")}
    if missing:
        raise RuntimeError(f"NCBI taxdump is missing expected files: {', '.join(sorted(missing))}")


def download_shared(force: bool = False) -> None:
    paths = {
        "ncbi": DOWNLOADS / "ncbi" / "taxdump.tar.gz",
        "gbif": DOWNLOADS / "gbif" / "backbone.zip",
        "col": DOWNLOADS / "col" / "xr_latest_dwca.zip",
        "inat": DOWNLOADS / "inat" / "inaturalist-taxonomy.dwca.zip",
    }
    for source in ("ncbi", "gbif", "col", "inat"):
        _download(SOURCES[source], paths[source], force)
    _extract_ncbi(paths["ncbi"])
    for source in ("gbif", "col", "inat"):
        with zipfile.ZipFile(paths[source]) as archive:
            if not archive.namelist():
                raise RuntimeError(f"Downloaded archive has no members: {paths[source]}")
    print("Shared source downloads are ready. GBIF, Catalogue of Life, and iNaturalist archives are parsed directly during builds.")


def download_language_sources(language: str, force: bool = False) -> None:
    lang_dir = language_dir(language)
    config_path = lang_dir / "sources.json"
    if not config_path.exists():
        print(f"No optional language sources configured in {config_path}")
        return
    config = json.loads(config_path.read_text(encoding="utf-8"))
    sources = config.get("sources", [])
    for source in sources:
        if not source.get("enabled", True):
            continue
        source_id = source["id"]
        destination = lang_dir / source["file"]
        _download(source["url"], destination, force)
        if source.get("archive", "").casefold() == "zip":
            with zipfile.ZipFile(destination) as archive:
                if not archive.namelist():
                    raise RuntimeError(f"Downloaded source archive has no members: {destination}")
        print(f"Ready: {source_id} ({destination})")
