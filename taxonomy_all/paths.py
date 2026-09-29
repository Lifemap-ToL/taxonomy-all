from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHARED = ROOT / "shared"
DOWNLOADS = SHARED / "downloads"
EXTRACTED = SHARED / "extracted"


def language_dir(language: str) -> Path:
    code = language.strip().lower()
    if len(code) != 2 or not code.isalpha():
        raise ValueError(f"Expected a two-letter language code, got {language!r}")
    return ROOT / code
