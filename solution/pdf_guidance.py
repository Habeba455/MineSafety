from pathlib import Path
import json
import re

import pymupdf


MARKER = "## MSHA Handbook Interpretation"


def find_project_root():
    here = Path(__file__).resolve()

    candidates = [
        Path("/workspace"),
        here.parents[1],
        Path.cwd(),
    ]

    for candidate in candidates:
        if (
            (candidate / "data" / "MSHA_Citation_Handbook.pdf").exists()
            or (
                candidate
                / "environment"
                / "data"
                / "MSHA_Citation_Handbook.pdf"
            ).exists()
        ):
            return candidate

    raise FileNotFoundError("Cannot locate MSHA handbook")


def run():
    root = find_project_root()

    pdf_candidates = [
        root / "data" / "MSHA_Citation_Handbook.pdf",
        root / "environment" / "data" / "MSHA_Citation_Handbook.pdf",
    ]

    pdf_path = next(
        (path for path in pdf_candidates if path.exists()),
        None,
    )

    if pdf_path is None:
        raise FileNotFoundError("MSHA PDF not found")

    with pymupdf.open(pdf_path) as document:
        page_count = len(document)

        if page_count < 102:
            raise ValueError("MSHA handbook is incomplete")

        page_14 = document[13].get_text()
        page_15 = document[14].get_text()
        page_102 = document[101].get_text()

    combined = " ".join(
        (page_14 + page_15 + page_102).split()
    ).lower()

    required_terms = [
        "significant and substantial",
        "reasonably likely",
    ]

    for term in required_terms:
        if term not in combined:
            raise ValueError(
                f"Missing handbook concept: {term}"
            )

    if not re.search(
        r"s&s|significant and substantial",
        combined,
        flags=re.IGNORECASE,
    ):
        raise ValueError("S&S classification guidance missing")

    output_candidates = [
        root / "output",
        Path("/workspace/output"),
    ]

    output_dir = next(
        (
            path
            for path in output_candidates
            if (path / "recommendation.md").exists()
        ),
        None,
    )

    if output_dir is None:
        raise FileNotFoundError(
            "Run the mining analysis before PDF integration"
        )

    memo_path = output_dir / "recommendation.md"
    memo = memo_path.read_text(encoding="utf-8")

    # Prevent duplicated text on repeated runs.
    if MARKER in memo:
        memo = memo.split(MARKER)[0].rstrip()

    handbook_section = """
## MSHA Handbook Interpretation

The analysis interprets Significant and Substantial (S&S)
violations using the *MSHA Citation and Order Writing Handbook*,
November 2025, Handbook PH25-I-2.

The handbook addresses S&S classifications in its discussion
of citation Item 10C (PDF pages 14–15) and provides further
guidance and examples on PDF page 102.

These passages relate S&S evaluations to the likelihood and
seriousness of potential injury or illness. Accordingly,
the analysis treats the recorded S&S designation as a
regulatory severity signal distinct from a simple count
of all violations.

The handbook is used to interpret existing S&S flags,
not to independently reclassify citations. It does not
establish that every historical citation was evaluated
under identical November 2025 procedures.

A higher S&S screening signal supports prioritizing
independent review; it does not prove that a mine is
currently unsafe or noncompliant.
""".strip()

    memo_path.write_text(
        memo + "\n\n" + handbook_section + "\n",
        encoding="utf-8",
    )

    quality_path = (
        output_dir / "analysis" / "data_quality.json"
    )

    if quality_path.exists():
        quality = json.loads(
            quality_path.read_text(encoding="utf-8")
        )

        quality["msha_handbook"] = {
            "title": "Citation and Order Writing Handbook",
            "handbook_number": "PH25-I-2",
            "publication_date": "November 2025",
            "total_pdf_pages": page_count,
            "guidance_pdf_pages": [14, 15, 102],
            "ss_guidance_verified": True,
            "use": "Interpretation of recorded S&S flags",
            "historical_limitation": (
                "The November 2025 handbook is not "
                "assumed to govern earlier citations "
                "in identical form."
            ),
        }

        quality_path.write_text(
            json.dumps(
                quality,
                indent=2,
                ensure_ascii=False,
            ) + "\n",
            encoding="utf-8",
        )

    print("MSHA PDF integration completed")
    print("PDF pages:", page_count)
    print("S&S guidance pages: 14, 15, 102")
    print("Recommendation memo updated")
    print("Data quality metadata updated")


if __name__ == "__main__":
    run()
