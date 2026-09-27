"""Load, clean, and validate the PAIMANA project source data."""

from pathlib import Path
import re
from typing import Any

import numpy as np
import pandas as pd
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CSV_PATH = PROJECT_ROOT / "data" / "MinistryWiseProjects_Report.csv"
CSV_HEADER_ROW = 2

SOURCE_TO_INTERNAL_COLUMNS = {
    "Sr.No.": "sr_no",
    "Line Ministry": "ministry",
    "Sector": "sector",
    "ProjectID": "project_id",
    "Project Name": "project_name",
    "Original Cost (in Cr)": "original_cost_cr",
    "Latest Revised Cost (in Cr)": "revised_cost_cr",
    "Expenditure (Cumm.) (in Cr)": "expenditure_cr",
}

BASE_COLUMNS = [
    "sr_no",
    "ministry",
    "sector",
    "project_id",
    "project_name",
    "original_cost_cr",
    "revised_cost_cr",
    "expenditure_cr",
]


class DataSchemaError(ValueError):
    """Raised when the source CSV no longer has the expected structure."""


def _normalize_header(value: object) -> str:
    """Collapse embedded line breaks and repeated whitespace in a header."""
    return re.sub(r"\s+", " ", str(value)).strip()


def _clean_text(series: pd.Series) -> pd.Series:
    """Trim and normalize text while retaining missing values as missing."""
    cleaned = series.astype("string").str.replace(r"\s+", " ", regex=True).str.strip()
    return cleaned.mask(cleaned.eq(""), pd.NA)


def _clean_numeric(series: pd.Series) -> pd.Series:
    """Parse financial text safely; malformed values become missing, never zero."""
    cleaned = series.astype("string").str.strip().str.replace(",", "", regex=False)
    cleaned = cleaned.mask(cleaned.eq(""), pd.NA)
    return pd.to_numeric(cleaned, errors="coerce").astype("Float64")


def _read_source(csv_path: Path) -> pd.DataFrame:
    """Read the inspected CSV layout and validate its required columns."""
    if not csv_path.is_file():
        raise FileNotFoundError(f"PAIMANA project CSV was not found: {csv_path}")

    source = pd.read_csv(
        csv_path,
        skiprows=CSV_HEADER_ROW,
        dtype="string",
        keep_default_na=False,
        encoding="utf-8-sig",
    )

    normalized_columns = [_normalize_header(column) for column in source.columns]
    duplicate_headers = sorted(
        {column for column in normalized_columns if normalized_columns.count(column) > 1}
    )
    if duplicate_headers:
        raise DataSchemaError(
            "The PAIMANA CSV contains duplicate columns after header normalization: "
            + ", ".join(duplicate_headers)
        )

    source.columns = normalized_columns
    missing_columns = sorted(set(SOURCE_TO_INTERNAL_COLUMNS) - set(source.columns))
    if missing_columns:
        raise DataSchemaError(
            "The PAIMANA CSV structure has changed. Missing required columns: "
            + ", ".join(missing_columns)
            + ". Available columns: "
            + ", ".join(source.columns)
        )

    return source[list(SOURCE_TO_INTERNAL_COLUMNS)].rename(
        columns=SOURCE_TO_INTERNAL_COLUMNS
    )


@st.cache_data(show_spinner=False)
def load_projects_data(csv_path: str | Path = DEFAULT_CSV_PATH) -> pd.DataFrame:
    """Return the cleaned PAIMANA project data with financial derived fields.

    Prototype revised-cost policy:
    The source uses zero extensively where a revised cost has not been reported.
    Therefore, zero, negative, blank, or malformed revised-cost values are marked
    unavailable. ``revised_cost_cr`` is missing for those rows, while
    ``revised_cost_raw`` preserves the source value for audit. The loader never
    substitutes original cost for unavailable revised cost.
    """
    source = _read_source(Path(csv_path))
    cleaned = pd.DataFrame(index=source.index)

    cleaned["sr_no"] = pd.to_numeric(source["sr_no"].str.strip(), errors="coerce").astype(
        "Int64"
    )
    cleaned["ministry"] = _clean_text(source["ministry"])
    cleaned["sector"] = _clean_text(source["sector"])
    cleaned["project_id"] = _clean_text(source["project_id"])
    cleaned["project_name"] = _clean_text(source["project_name"])
    cleaned["original_cost_cr"] = _clean_numeric(source["original_cost_cr"])

    cleaned["revised_cost_raw"] = source["revised_cost_cr"].astype("string").str.strip()
    revised_cost_numeric = _clean_numeric(source["revised_cost_cr"])
    cleaned["revised_cost_available"] = revised_cost_numeric.notna() & revised_cost_numeric.gt(0)
    cleaned["revised_cost_cr"] = revised_cost_numeric.where(
        cleaned["revised_cost_available"]
    )

    cleaned["expenditure_cr"] = _clean_numeric(source["expenditure_cr"])

    valid_original_cost = cleaned["original_cost_cr"].notna() & cleaned[
        "original_cost_cr"
    ].gt(0)
    valid_revised_cost = cleaned["revised_cost_available"]

    cleaned["expenditure_ratio_pct"] = np.nan
    cleaned.loc[valid_original_cost, "expenditure_ratio_pct"] = (
        cleaned.loc[valid_original_cost, "expenditure_cr"]
        / cleaned.loc[valid_original_cost, "original_cost_cr"]
        * 100
    )

    cleaned["cost_change_cr"] = np.nan
    cleaned.loc[valid_revised_cost, "cost_change_cr"] = (
        cleaned.loc[valid_revised_cost, "revised_cost_cr"]
        - cleaned.loc[valid_revised_cost, "original_cost_cr"]
    )

    cleaned["cost_change_pct"] = np.nan
    valid_cost_change_pct = valid_original_cost & valid_revised_cost
    cleaned.loc[valid_cost_change_pct, "cost_change_pct"] = (
        cleaned.loc[valid_cost_change_pct, "cost_change_cr"]
        / cleaned.loc[valid_cost_change_pct, "original_cost_cr"]
        * 100
    )

    return cleaned[
        BASE_COLUMNS
        + [
            "revised_cost_raw",
            "revised_cost_available",
            "expenditure_ratio_pct",
            "cost_change_cr",
            "cost_change_pct",
        ]
    ].reset_index(drop=True)


def summarize_data_quality(projects: pd.DataFrame) -> dict[str, Any]:
    """Return reusable record counts for loader and development verification."""
    project_ids = projects["project_id"]
    duplicate_rows = project_ids.notna() & project_ids.duplicated(keep=False)
    revised_cost_raw_numeric = _clean_numeric(projects["revised_cost_raw"])

    return {
        "total_loaded_rows": int(len(projects)),
        "unique_project_ids": int(project_ids.nunique(dropna=True)),
        "unique_ministries": int(projects["ministry"].nunique(dropna=True)),
        "unique_sectors": int(projects["sector"].nunique(dropna=True)),
        "duplicate_project_ids": int(project_ids.dropna().duplicated().sum()),
        "rows_with_duplicate_project_ids": int(duplicate_rows.sum()),
        "missing_project_id": int(project_ids.isna().sum()),
        "missing_ministry": int(projects["ministry"].isna().sum()),
        "missing_sector": int(projects["sector"].isna().sum()),
        "missing_project_name": int(projects["project_name"].isna().sum()),
        "missing_or_invalid_original_cost": int(
            (projects["original_cost_cr"].isna() | projects["original_cost_cr"].le(0)).sum()
        ),
        "available_revised_cost": int(projects["revised_cost_available"].sum()),
        "unavailable_revised_cost": int((~projects["revised_cost_available"]).sum()),
        "zero_or_negative_revised_cost": int(revised_cost_raw_numeric.le(0).sum()),
        "blank_or_malformed_revised_cost": int(revised_cost_raw_numeric.isna().sum()),
        "missing_or_invalid_expenditure": int(
            (projects["expenditure_cr"].isna() | projects["expenditure_cr"].lt(0)).sum()
        ),
        "zero_expenditure": int(projects["expenditure_cr"].eq(0).sum()),
        "expenditure_exceeds_original_cost": int(
            projects["expenditure_cr"].gt(projects["original_cost_cr"]).sum()
        ),
    }


def _run_development_check() -> None:
    """Print a concise terminal verification without changing the Streamlit UI."""
    projects = load_projects_data()
    print(f"Dataframe shape: {projects.shape}")
    print(f"Cleaned columns: {list(projects.columns)}")
    print(f"Total projects: {len(projects)}")
    print("\nFirst five cleaned rows:")
    print(projects.head().to_string(index=False))
    print("\nData-quality summary:")
    for name, value in summarize_data_quality(projects).items():
        print(f"  {name}: {value}")


if __name__ == "__main__":
    _run_development_check()
