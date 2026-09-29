from __future__ import annotations

import csv
import io
import re
import zipfile
from pathlib import Path


def read_taxref_vernaculars(
    archive_path: Path,
    language_codes: list[str],
    source_label: str = "inpn",
) -> list[VernacularRecord]:
    """Read vernacular names against the scientific name on each TAXREF row."""
    # Imported at call time to avoid a module-level cycle: build.py owns the
    # shared record type used by every source adapter.
    from ..build import VernacularRecord, _get, _header_map

    with zipfile.ZipFile(archive_path) as archive:
        files = [info.filename for info in archive.infolist() if not info.is_dir()]
        taxref_member = next(
            (name for name in files if re.fullmatch(r"taxrefv\d+\.txt", Path(name).name, flags=re.IGNORECASE)),
            None,
        )
        taxvern_member = next(
            (name for name in files if re.fullmatch(r"taxvernv\d+\.txt", Path(name).name, flags=re.IGNORECASE)),
            None,
        )
        if not taxref_member or not taxvern_member:
            raise RuntimeError("INPN TAXREF archive must contain TAXREFv*.txt and TAXVERNv*.txt")

        taxref_text = io.TextIOWrapper(archive.open(taxref_member), encoding="utf-8-sig", errors="replace", newline="")
        with taxref_text:
            reader = csv.DictReader(taxref_text, delimiter="\t")
            headers = _header_map(reader.fieldnames)
            name_by_nom: dict[str, str] = {}
            ref_by_nom: dict[str, str] = {}
            taxref_vernaculars: list[VernacularRecord] = []
            read_taxref_vocabulary = bool({code.casefold() for code in language_codes} & {"fra", "fre"})
            for row in reader:
                cd_nom = _get(row, headers, "cd_nom")
                cd_ref = _get(row, headers, "cd_ref")
                if not cd_nom:
                    continue
                scientific = _get(row, headers, "lb_nom", "nom_complet", "nom_valide")
                if not scientific:
                    continue
                name_by_nom[cd_nom] = scientific
                cd_ref = cd_ref or cd_nom
                ref_by_nom[cd_nom] = cd_ref
                if read_taxref_vocabulary:
                    for vernacular in (name.strip() for name in _get(row, headers, "nom_vern").split(",")):
                        if vernacular:
                            taxref_vernaculars.append(
                                VernacularRecord(
                                    source=source_label,
                                    source_id=f"CD_NOM={cd_nom};CD_REF={cd_ref};field=NOM_VERN",
                                    scientific_name=scientific,
                                    name=vernacular,
                                )
                            )

        wanted_languages = {code.casefold() for code in language_codes}
        records: list[VernacularRecord] = taxref_vernaculars
        taxvern_text = io.TextIOWrapper(archive.open(taxvern_member), encoding="utf-8-sig", errors="replace", newline="")
        with taxvern_text:
            reader = csv.DictReader(taxvern_text, delimiter="\t")
            headers = _header_map(reader.fieldnames)
            for row in reader:
                iso_code = _get(row, headers, "iso639_3", "iso639-3").casefold()
                if iso_code not in wanted_languages:
                    continue
                cd_nom = _get(row, headers, "cd_nom")
                cd_ref = _get(row, headers, "cd_ref") or ref_by_nom.get(cd_nom, cd_nom)
                scientific = name_by_nom.get(cd_nom)
                if not scientific:
                    continue
                vernacular_field = _get(row, headers, "lb_vern", "nom_vern")
                for vernacular in (name.strip() for name in vernacular_field.split(",")):
                    if not vernacular:
                        continue
                    records.append(
                        VernacularRecord(
                            source=source_label,
                            source_id=f"CD_NOM={cd_nom};CD_REF={cd_ref};CD_VERN={_get(row, headers, 'cd_vern')}",
                            scientific_name=scientific,
                            name=vernacular,
                        )
                    )
        return records
