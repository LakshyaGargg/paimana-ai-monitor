from __future__ import annotations

import hashlib
import html
import re

import pandas as pd
import streamlit as st

from src.risk_engine import (
    HISTORICAL_DATA_PATH,
    REVIEW_PRIORITY_DISCLAIMER,
    generate_monitoring_indicators,
    generate_review_priorities,
    load_historical_projects,
)
from src.ui import apply_shared_styles, render_page_header


PAGE_CSS = """
<style>
    .risk-context-note {
        background: #F2F4F7;
        border-left: 3px solid #D99024;
        color: #495765;
        font-size: 0.9rem;
        line-height: 1.5;
        margin: 1.1rem 0 1.25rem;
        padding: 0.75rem 0.9rem;
    }

    .risk-section-title {
        color: #102A43;
        font-size: 1.15rem;
        font-weight: 700;
        margin: 1.45rem 0 0.7rem;
    }

    .risk-filter-title {
        color: #17365D;
        font-size: 0.92rem;
        font-weight: 700;
        letter-spacing: 0.025em;
        margin: 0 0 0.35rem;
        text-transform: uppercase;
    }

    .risk-summary-card {
        background: #FFFFFF;
        border: 1px solid #D9DEE5;
        border-top: 3px solid #17365D;
        border-radius: 5px;
        min-height: 92px;
        padding: 0.85rem 1rem;
    }

    .risk-summary-label {
        color: #66727F;
        font-size: 0.79rem;
        font-weight: 650;
        letter-spacing: 0.035em;
        margin: 0;
        text-transform: uppercase;
    }

    .risk-summary-value {
        color: #17365D;
        font-size: 1.7rem;
        font-weight: 750;
        line-height: 1.15;
        margin: 0.45rem 0 0;
    }

    .risk-detail-panel {
        background: #FFFFFF;
        border: 1px solid #D9DEE5;
        border-left: 4px solid #17365D;
        border-radius: 5px;
        margin-bottom: 0.8rem;
        padding: 1rem 1.1rem;
    }

    .risk-detail-name {
        color: #102A43;
        font-size: 1.1rem;
        font-weight: 700;
        line-height: 1.4;
        margin: 0 0 0.85rem;
    }

    .risk-detail-grid {
        display: grid;
        gap: 0.75rem 1.25rem;
        grid-template-columns: repeat(3, minmax(0, 1fr));
    }

    .risk-detail-item {
        min-width: 0;
    }

    .risk-detail-label {
        color: #66727F;
        display: block;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.04em;
        margin-bottom: 0.2rem;
        text-transform: uppercase;
    }

    .risk-detail-value {
        color: #1F2933;
        display: block;
        font-size: 0.88rem;
        line-height: 1.45;
        overflow-wrap: anywhere;
    }

    .risk-priority {
        border: 1px solid #D9DEE5;
        border-radius: 3px;
        display: inline-block;
        font-size: 0.78rem;
        font-weight: 750;
        letter-spacing: 0.04em;
        margin-left: 0.35rem;
        padding: 0.15rem 0.5rem;
    }

    .risk-priority-high {
        background: #FFFFFF;
        border-color: #17365D;
        color: #102A43;
    }

    .risk-priority-medium {
        background: #FFF9EF;
        border-color: #D99024;
        color: #70450B;
    }

    .risk-priority-normal {
        background: #F2F4F7;
        color: #495765;
    }

    .risk-priority-explanation {
        border-top: 1px solid #E7EAF0;
        color: #1F2933;
        font-size: 0.92rem;
        line-height: 1.55;
        margin: 0.9rem 0 0;
        padding-top: 0.8rem;
    }

    .risk-indicator-card {
        background: #FFFFFF;
        border: 1px solid #D9DEE5;
        border-left: 3px solid #17365D;
        border-radius: 5px;
        margin-bottom: 0.85rem;
        padding: 1rem 1.05rem;
    }

    .risk-indicator-header {
        align-items: flex-start;
        display: flex;
        gap: 1rem;
        justify-content: space-between;
    }

    .risk-indicator-title {
        color: #102A43;
        font-size: 1rem;
        font-weight: 700;
        line-height: 1.4;
        margin: 0;
    }

    .risk-indicator-category {
        background: #F2F4F7;
        border: 1px solid #D9DEE5;
        border-radius: 3px;
        color: #17365D;
        display: inline-block;
        font-size: 0.72rem;
        font-weight: 650;
        margin-top: 0.4rem;
        padding: 0.16rem 0.45rem;
    }

    .risk-indicator-code {
        background: #FFFFFF;
        border: 1px solid #D9DEE5;
        border-radius: 3px;
        color: #66727F;
        font-family: "Segoe UI", Arial, sans-serif;
        font-size: 0.76rem;
        font-weight: 650;
        letter-spacing: 0.025em;
        margin: 0;
        padding: 0.2rem 0.45rem;
        white-space: nowrap;
    }

    .risk-indicator-explanation {
        color: #1F2933;
        font-size: 0.9rem;
        line-height: 1.55;
        margin: 0.8rem 0 0;
    }

    .risk-evidence-grid {
        background: #F7F8FA;
        border: 1px solid #E4E8ED;
        display: grid;
        gap: 0;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        margin-top: 0.9rem;
    }

    .risk-evidence-item {
        border-right: 1px solid #E4E8ED;
        min-width: 0;
        padding: 0.7rem 0.8rem;
    }

    .risk-evidence-item:last-child {
        border-right: 0;
    }

    .risk-evidence-label {
        color: #66727F;
        font-size: 0.76rem;
        font-weight: 650;
        margin: 0 0 0.2rem;
        text-transform: uppercase;
    }

    .risk-evidence-value {
        color: #1F2933;
        font-size: 0.9rem;
        margin: 0;
        overflow-wrap: anywhere;
    }

    [data-testid="stDataFrame"] {
        background: #FFFFFF !important;
        border: 1px solid #D9DEE5;
        border-radius: 4px;
    }

    [data-testid="stVerticalBlockBorderWrapper"] {
        background: #FFFFFF !important;
        border-color: #D9DEE5 !important;
        box-shadow: none !important;
        color: #1F2933 !important;
    }

    [data-testid="stSelectbox"] div[role="group"],
    div[data-baseweb="select"] > div {
        background: #FFFFFF !important;
        border-color: #D9DEE5 !important;
        border-radius: 3px;
        color: #1F2933 !important;
    }

    [data-testid="stSelectbox"] input,
    div[data-baseweb="select"] input,
    div[data-baseweb="select"] span {
        color: #1F2933 !important;
        -webkit-text-fill-color: #1F2933 !important;
    }

    [data-testid="stSelectbox"] button svg,
    div[data-baseweb="select"] svg {
        fill: #17365D !important;
        color: #17365D !important;
    }

    [data-testid="stTextInput"] input,
    .stTextInput input {
        background: #FFFFFF !important;
        border-color: #D9DEE5 !important;
        color: #1F2933 !important;
        -webkit-text-fill-color: #1F2933 !important;
    }

    [data-testid="stSelectbox"] label p,
    [data-testid="stTextInput"] label p,
    .stSelectbox label p,
    .stTextInput label p {
        color: #1F2933 !important;
        font-weight: 650;
    }

    div[role="listbox"] {
        background: #FFFFFF !important;
        border: 1px solid #D9DEE5 !important;
    }

    div[role="option"] {
        background: #FFFFFF !important;
        color: #1F2933 !important;
    }

    div[role="option"]:hover,
    div[role="option"][aria-selected="true"] {
        background: #F2F4F7 !important;
        color: #102A43 !important;
    }

    @media (max-width: 760px) {
        .risk-detail-grid {
            grid-template-columns: repeat(2, minmax(0, 1fr));
        }

        .risk-evidence-grid {
            grid-template-columns: repeat(2, minmax(0, 1fr));
        }

        .risk-evidence-item:nth-child(2) {
            border-right: 0;
        }

        .risk-evidence-item:nth-child(-n+2) {
            border-bottom: 1px solid #E4E8ED;
        }
    }
</style>
"""

INDICATOR_LABELS = {
    "COST_REVIEW": "Cost Review",
    "SCHEDULE_REVIEW": "Schedule Review",
    "PROGRESS_STAGNATION_REVIEW": "Progress Stagnation",
    "EXPENDITURE_PROGRESS_REVIEW": "Expenditure-Progress Review",
    "REVISED_COST_UNAVAILABLE": "Revised Cost Unavailable",
    "REVISED_DOC_UNAVAILABLE": "Revised DoC Unavailable",
    "PHYSICAL_PROGRESS_UNAVAILABLE": "Physical Progress Unavailable",
}

INDICATOR_CATEGORY_OPTIONS = [
    "All Categories",
    "Cost Review",
    "Schedule Review",
    "Progress Review",
    "Expenditure-Progress Review",
    "Data Quality Review",
]

PRIORITY_ORDER = {"HIGH": 0, "MEDIUM": 1, "NORMAL": 2}


@st.cache_data(show_spinner=False)
def _load_monitoring_data(
    historical_file_modified_ns: int,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    del historical_file_modified_ns
    history = load_historical_projects()
    indicators = generate_monitoring_indicators(history)
    priorities = generate_review_priorities(history, indicators)
    return history, indicators, priorities


def _month_label(report_month: str) -> str:
    return pd.Period(report_month, freq="M").strftime("%B %Y")


def _humanize_indicator_list(value: object) -> str:
    if value is None or pd.isna(value) or not str(value).strip():
        return "None"
    codes = [code.strip() for code in str(value).split(",") if code.strip()]
    return ", ".join(INDICATOR_LABELS.get(code, code) for code in codes)


def _safe(value: object) -> str:
    if value is None or pd.isna(value):
        return "Not available"
    return html.escape(str(value))


def _format_number(value: object) -> str:
    rendered = f"{float(value):,.2f}".rstrip("0").rstrip(".")
    return rendered


def _format_evidence_value(indicator: pd.Series, field: str) -> str:
    value = indicator[field]
    if value is None or pd.isna(value):
        return "Not available"

    code = indicator["indicator_code"]
    if code in {"COST_REVIEW", "EXPENDITURE_PROGRESS_REVIEW"}:
        formatted = f"₹{_format_number(value)} crore"
        if code == "COST_REVIEW" and field == "change_value":
            percentage = indicator.get("change_percent")
            if percentage is not None and pd.notna(percentage):
                formatted += f" ({_format_number(percentage)}%)"
        return formatted
    if code == "PROGRESS_STAGNATION_REVIEW":
        suffix = " percentage points" if field == "change_value" else "%"
        return f"{_format_number(value)}{suffix}"
    if code == "SCHEDULE_REVIEW" and field == "change_value":
        return f"{int(value)} month(s)"
    return str(value)


def _render_summary_card(label: str, value: int) -> None:
    st.markdown(
        f"""
        <div class="risk-summary-card">
            <p class="risk-summary-label">{html.escape(label)}</p>
            <p class="risk-summary-value">{value:,}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


apply_shared_styles()
st.html(PAGE_CSS)
render_page_header(
    "Risk & Alerts",
    "Rule-based monitoring indicators derived from reported PAIMANA project data.",
)

st.markdown(
    f"""
    <div class="risk-context-note">
        {html.escape(REVIEW_PRIORITY_DISCLAIMER)} Monitoring indicators are
        screening signals based on reported data; they are not predictions.
    </div>
    """,
    unsafe_allow_html=True,
)

try:
    history, indicators, priorities = _load_monitoring_data(
        HISTORICAL_DATA_PATH.stat().st_mtime_ns
    )
except (FileNotFoundError, ValueError) as exc:
    st.error(f"Monitoring data could not be loaded: {exc}")
    st.stop()

available_months = sorted(priorities["report_month"].dropna().unique().tolist())
if not available_months:
    st.warning("No monitoring records are currently available.")
    st.stop()

st.markdown('<p class="risk-filter-title">Filters</p>', unsafe_allow_html=True)
with st.container(border=True):
    month_column, ministry_column, priority_column = st.columns([1, 1.7, 1.15])
    with month_column:
        selected_month = st.selectbox(
            "Report Month",
            available_months,
            index=len(available_months) - 1,
            format_func=_month_label,
        )

    month_ministries = sorted(
        priorities.loc[
            priorities["report_month"].eq(selected_month), "ministry"
        ].dropna().unique().tolist()
    )
    with ministry_column:
        selected_ministry = st.selectbox(
            "Ministry", ["All Ministries", *month_ministries]
        )
    with priority_column:
        selected_priority = st.selectbox(
            "Review Priority", ["All Priorities", "HIGH", "MEDIUM", "NORMAL"]
        )

    category_column, search_column = st.columns([1.25, 1.75])
    with category_column:
        selected_category = st.selectbox(
            "Indicator Category", INDICATOR_CATEGORY_OPTIONS
        )
    with search_column:
        project_search = st.text_input(
            "Project Search", placeholder="Project ID or project name"
        ).strip()

context_projects = priorities.loc[priorities["report_month"].eq(selected_month)].copy()
if selected_ministry != "All Ministries":
    context_projects = context_projects.loc[
        context_projects["ministry"].eq(selected_ministry)
    ]
if project_search:
    search_pattern = re.escape(project_search)
    search_matches = context_projects["project_id"].astype("string").str.contains(
        search_pattern, case=False, na=False
    ) | context_projects["project_name"].astype("string").str.contains(
        search_pattern, case=False, na=False
    )
    context_projects = context_projects.loc[search_matches]

if selected_category != "All Categories":
    category_project_ids = set(
        indicators.loc[
            indicators["report_month"].eq(selected_month)
            & indicators["indicator_category"].eq(selected_category),
            "project_id",
        ].astype("string")
    )
    context_projects = context_projects.loc[
        context_projects["project_id"].astype("string").isin(category_project_ids)
    ]

summary_counts = context_projects["review_priority"].value_counts()
summary_columns = st.columns(4)
with summary_columns[0]:
    _render_summary_card("Projects Monitored", len(context_projects))
with summary_columns[1]:
    _render_summary_card("HIGH Priority", int(summary_counts.get("HIGH", 0)))
with summary_columns[2]:
    _render_summary_card("MEDIUM Priority", int(summary_counts.get("MEDIUM", 0)))
with summary_columns[3]:
    _render_summary_card("NORMAL Priority", int(summary_counts.get("NORMAL", 0)))

st.caption(
    "Summary cards reflect Report Month, Ministry, Indicator Category, and Project "
    "Search. Review Priority narrows the table only."
)

filtered_projects = context_projects.copy()
if selected_priority != "All Priorities":
    filtered_projects = filtered_projects.loc[
        filtered_projects["review_priority"].eq(selected_priority)
    ]

filtered_projects["_priority_order"] = filtered_projects["review_priority"].map(
    PRIORITY_ORDER
)
filtered_projects["_project_name_order"] = filtered_projects[
    "project_name"
].astype("string").str.casefold()
filtered_projects = filtered_projects.sort_values(
    ["_priority_order", "_project_name_order", "project_id"], kind="stable"
).reset_index(drop=True)

st.markdown(
    '<p class="risk-section-title">Projects for Monitoring Review</p>',
    unsafe_allow_html=True,
)
st.caption(
    "Select a row to inspect its monitoring indicators. NORMAL means no substantive "
    "indicator triggered under the current prototype rules; it does not mean safe."
)

if filtered_projects.empty:
    st.info("No monitoring records match the selected filters.")
    st.stop()

table_data = pd.DataFrame(
    {
        "Project ID": filtered_projects["project_id"],
        "Project Name": filtered_projects["project_name"],
        "Ministry": filtered_projects["ministry"],
        "Sector": filtered_projects["sector"],
        "Review Priority": filtered_projects["review_priority"],
        "Substantive Indicators": filtered_projects[
            "triggered_substantive_indicators"
        ].map(_humanize_indicator_list),
        "Data Quality Indicators": filtered_projects[
            "triggered_data_quality_indicators"
        ].map(_humanize_indicator_list),
    }
)
styled_table = table_data.style.set_properties(
    **{
        "background-color": "#FFFFFF",
        "color": "#1F2933",
        "border-color": "#D9DEE5",
    }
)

st.caption(f"Showing {len(table_data):,} project-month record(s).")
filter_signature = "|".join(
    [
        selected_month,
        selected_ministry,
        selected_priority,
        selected_category,
        project_search.casefold(),
    ]
)
table_key = "risk_project_table_" + hashlib.sha1(
    filter_signature.encode("utf-8")
).hexdigest()[:12]
table_event = st.dataframe(
    styled_table,
    hide_index=True,
    use_container_width=True,
    on_select="rerun",
    selection_mode="single-row",
    key=table_key,
    column_config={
        "Project ID": st.column_config.TextColumn(width="small"),
        "Project Name": st.column_config.TextColumn(width="large"),
        "Ministry": st.column_config.TextColumn(width="medium"),
        "Sector": st.column_config.TextColumn(width="medium"),
        "Review Priority": st.column_config.TextColumn(width="small"),
        "Substantive Indicators": st.column_config.TextColumn(width="large"),
        "Data Quality Indicators": st.column_config.TextColumn(width="large"),
    },
)

selected_rows = table_event.selection.rows
if not selected_rows:
    st.info("Select a project row to view Monitoring Review Details.")
    st.stop()

selected_project = filtered_projects.iloc[selected_rows[0]]
project_id = str(selected_project["project_id"])
project_month = selected_project["report_month"]
priority_class = str(selected_project["review_priority"]).lower()

st.markdown(
    '<p class="risk-section-title">Monitoring Review Details</p>',
    unsafe_allow_html=True,
)
st.markdown(
    f"""
    <section class="risk-detail-panel">
        <p class="risk-detail-name">{_safe(selected_project['project_name'])}</p>
        <div class="risk-detail-grid">
            <div class="risk-detail-item">
                <span class="risk-detail-label">Project ID</span>
                <span class="risk-detail-value">{_safe(project_id)}</span>
            </div>
            <div class="risk-detail-item">
                <span class="risk-detail-label">Ministry</span>
                <span class="risk-detail-value">{_safe(selected_project['ministry'])}</span>
            </div>
            <div class="risk-detail-item">
                <span class="risk-detail-label">Sector</span>
                <span class="risk-detail-value">{_safe(selected_project['sector'])}</span>
            </div>
            <div class="risk-detail-item">
                <span class="risk-detail-label">Report Month</span>
                <span class="risk-detail-value">{_safe(_month_label(project_month))}</span>
            </div>
            <div class="risk-detail-item">
                <span class="risk-detail-label">Source Report</span>
                <span class="risk-detail-value">{_safe(selected_project['source_report'])}</span>
            </div>
            <div class="risk-detail-item">
                <span class="risk-detail-label">Review Priority</span>
                <span class="risk-priority risk-priority-{priority_class}">
                    {_safe(selected_project['review_priority'])}
                </span>
            </div>
        </div>
        <p class="risk-priority-explanation">
            {_safe(selected_project['priority_explanation'])}
        </p>
    </section>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    '<p class="risk-section-title">Triggered Monitoring Indicators</p>',
    unsafe_allow_html=True,
)
project_indicators = indicators.loc[
    indicators["report_month"].eq(project_month)
    & indicators["project_id"].astype("string").eq(project_id)
].copy()
indicator_order = {code: index for index, code in enumerate(INDICATOR_LABELS)}
project_indicators["_indicator_order"] = project_indicators["indicator_code"].map(
    indicator_order
)
project_indicators = project_indicators.sort_values(
    "_indicator_order", kind="stable"
)

if project_indicators.empty:
    st.info(
        "No substantive monitoring indicators triggered under the current prototype "
        "rules for this reporting snapshot."
    )
else:
    for _, indicator in project_indicators.iterrows():
        evidence = [
            ("Previous Value", _format_evidence_value(indicator, "previous_value")),
            ("Current Value", _format_evidence_value(indicator, "current_value")),
            ("Change Value", _format_evidence_value(indicator, "change_value")),
            ("Source Report", indicator["source_report"]),
        ]
        evidence_html = "".join(
            f"""
            <div class="risk-evidence-item">
                <p class="risk-evidence-label">{html.escape(label)}</p>
                <p class="risk-evidence-value">{_safe(value)}</p>
            </div>
            """
            for label, value in evidence
        )
        st.markdown(
            f"""
            <section class="risk-indicator-card">
                <div class="risk-indicator-header">
                    <div>
                        <p class="risk-indicator-title">{_safe(indicator['indicator_title'])}</p>
                        <span class="risk-indicator-category">
                            {_safe(indicator['indicator_category'])}
                        </span>
                    </div>
                    <p class="risk-indicator-code">{_safe(indicator['indicator_code'])}</p>
                </div>
                <p class="risk-indicator-explanation">{_safe(indicator['explanation'])}</p>
                <div class="risk-evidence-grid">{evidence_html}</div>
            </section>
            """,
            unsafe_allow_html=True,
        )
