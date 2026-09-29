from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Iterator

if TYPE_CHECKING:
    from ..build import VernacularRecord


def read_ncbi_names(
    names_path: Path,
    name_classes: list[str],
    source_label: str = "ncbi_taxdump",
) -> Iterator[VernacularRecord]:
    """Read selected NCBI names.dmp entries as direct-taxid vernacular names."""
    # Import here because build.py owns the shared record type.
    from ..build import VernacularRecord

    wanted_classes = {name_class.strip().casefold() for name_class in name_classes}
    with names_path.open(encoding="utf-8", errors="replace") as source:
        for line in source:
            parts = [part.strip() for part in line.split("|")]
            if len(parts) < 4:
                continue
            taxid, name, name_class = parts[0], parts[1], parts[3].casefold()
            if not taxid or not name or name_class not in wanted_classes:
                continue
            yield VernacularRecord(
                source=source_label,
                source_id=f"taxid={taxid};name_class={name_class}",
                scientific_name="",
                name=name,
                direct_ncbi=taxid,
            )
