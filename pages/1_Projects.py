from __future__ import annotations

import hashlib
import html
import re

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.risk_engine import HISTORICAL_DATA_PATH, load_historical_projects
from src.ui import apply_shared_styles, render_page_header


PAGE_CSS = """
<style>
    .projects-filter-title, .projects-section-title { color: #102A43; font-weight: 700; }
    .projects-filter-title { font-size: 0.9rem; letter-spacing: 0.025em; margin: 1rem 0 0.35rem; text-transform: uppercase; }
    .projects-section-title { font-size: 1.15rem; margin: 1.4rem 0 0.6rem; }
    .projects-detail-panel { background: #FFFFFF; border: 1px solid #D9DEE5; border-left: 4px solid #17365D; border-radius: 5px; padding: 1rem 1.1rem; }
    .projects-detail-name { color: #102A43; font-size: 1.1rem; font-weight: 700; line-height: 1.4; margin: 0 0 0.85rem; }
    .projects-detail-grid { display: grid; gap: 0.75rem 1.25rem; grid-template-columns: repeat(3, minmax(0, 1fr)); }
    .projects-detail-label { color: #66727F; display: block; font-size: 0.72rem; font-weight: 700; letter-spacing: 0.04em; margin-bottom: 0.2rem; text-transform: uppercase; }
    .projects-detail-value { color: #1F2933; display: block; font-size: 0.9rem; line-height: 1.45; overflow-wrap: anywhere; }
    .projects-metric-card { background: #FFFFFF; border: 1px solid #D9DEE5; border-top: 3px solid #17365D; border-radius: 5px; box-sizing: border-box; min-height: 105px; padding: 0.8rem 0.9rem; }
    .projects-metric-label { color: #66727F; font-size: 0.74rem; font-weight: 700; letter-spacing: 0.03em; margin: 0; text-transform: uppercase; }
    .projects-metric-value { color: #17365D; font-size: 1.2rem; font-weight: 750; line-height: 1.3; margin: 0.42rem 0 0; overflow-wrap: anywhere; }
    .projects-source { border-top: 1px solid #D9DEE5; color: #66727F; font-size: 0.82rem; margin-top: 1.25rem; padding-top: 0.7rem; }
    [data-testid="stDataFrame"], [data-testid="stVerticalBlockBorderWrapper"] { background: #FFFFFF !important; border-color: #D9DEE5 !important; box-shadow: none !important; }
    [data-testid="stSelectbox"] div[role="group"], div[data-baseweb="select"] > div, .stTextInput input { background: #FFFFFF !important; border-color: #D9DEE5 !important; color: #1F2933 !important; }
    [data-testid="stSelectbox"] input, div[data-baseweb="select"] input, div[data-baseweb="select"] span, .stTextInput input { color: #1F2933 !important; -webkit-text-fill-color: #1F2933 !important; }
    [data-testid="stSelectbox"] button svg, div[data-baseweb="select"] svg { color: #17365D !important; fill: #17365D !important; }
    [data-testid="stSelectbox"] label p, .stSelectbox label p, .stTextInput label p { color: #1F2933 !important; font-weight: 650; }
    div[role="listbox"], div[role="option"] { background: #FFFFFF !important; color: #1F2933 !important; }
    div[role="option"]:hover, div[role="option"][aria-selected="true"] { background: #F2F4F7 !important; color: #102A43 !important; }
    @media (max-width: 900px) { .projects-detail-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
</style>
"""


@st.cache_data(show_spinner=False)
def _load_history(historical_file_modified_ns: int) -> pd.DataFrame:
    del historical_file_modified_ns
    return load_historical_projects()


def _month_label(report_month: str) -> str:
    return pd.Period(report_month, freq="M").strftime("%B %Y")


def _safe(value: object) -> str:
    if value is None or pd.isna(value) or not str(value).strip():
        return "Not available"
    return html.escape(str(value))


def _format_crore(value: object) -> str:
    if value is None or pd.isna(value):
        return "Not available"
    return f"₹{float(value):,.2f} crore"


def _format_percentage(value: object) -> str:
    if value is None or pd.isna(value):
        return "Not available"
    return f"{float(value):,.2f}".rstrip("0").rstrip(".") + "%"


def _render_detail_panel(project: pd.Series) -> None:
    details = [
        ("Project ID", project["project_id"]),
        ("Agency", project["agency"]),
        ("Ministry", project["ministry"]),
        ("Sector", project["sector"]),
        ("State", project["state"]),
    ]
    items = "".join(
        f'<div><span class="projects-detail-label">{html.escape(label)}</span>'
        f'<span class="projects-detail-value">{_safe(value)}</span></div>'
        for label, value in details
    )
    st.html(
        f'<section class="projects-detail-panel">'
        f'<p class="projects-detail-name">{_safe(project["project_name"])}</p>'
        f'<div class="projects-detail-grid">{items}</div></section>'
    )


def _render_metric(label: str, value: str) -> None:
    st.html(
        f'<div class="projects-metric-card">'
        f'<p class="projects-metric-label">{html.escape(label)}</p>'
        f'<p class="projects-metric-value">{html.escape(value)}</p></div>'
    )


def _chart_layout(y_title: str) -> dict[str, object]:
    return {
        "height": 300,
        "margin": {"l": 35, "r": 20, "t": 20, "b": 45},
        "paper_bgcolor": "#FFFFFF",
        "plot_bgcolor": "#FFFFFF",
        "font": {"family": "Segoe UI, Arial, sans-serif", "color": "#1F2933"},
        "showlegend": False,
        "yaxis": {"title": y_title, "gridcolor": "#E7EAF0", "rangemode": "tozero", "zeroline": False},
        "xaxis": {"type": "category"},
    }


apply_shared_styles()
st.html(PAGE_CSS)
render_page_header("Projects", "Explore reported project information and monthly history.")

try:
    history = _load_history(HISTORICAL_DATA_PATH.stat().st_mtime_ns)
except (FileNotFoundError, ValueError) as exc:
    st.error(f"Historical project data could not be loaded: {exc}")
    st.stop()

available_months = sorted(history["report_month"].dropna().unique().tolist())
if not available_months:
    st.warning("No historical project records are currently available.")
    st.stop()

st.markdown('<p class="projects-filter-title">Filters</p>', unsafe_allow_html=True)
with st.container(border=True):
    month_column, ministry_column = st.columns([1, 2])
    with month_column:
        selected_month = st.selectbox("Report Month", available_months, index=len(available_months) - 1, format_func=_month_label)

    month_projects = history.loc[history["report_month"].eq(selected_month)].copy()
    month_ministries = sorted(month_projects["ministry"].dropna().unique().tolist())
    with ministry_column:
        selected_ministry = st.selectbox("Ministry", ["All Ministries", *month_ministries])

    ministry_context = month_projects
    if selected_ministry != "All Ministries":
        ministry_context = ministry_context.loc[ministry_context["ministry"].eq(selected_ministry)]

    sector_column, search_column = st.columns([1, 2])
    context_sectors = sorted(ministry_context["sector"].dropna().unique().tolist())
    with sector_column:
        selected_sector = st.selectbox("Sector", ["All Sectors", *context_sectors])
    with search_column:
        project_search = st.text_input("Project Search", placeholder="Project ID or project name").strip()

filtered_projects = ministry_context.copy()
if selected_sector != "All Sectors":
    filtered_projects = filtered_projects.loc[filtered_projects["sector"].eq(selected_sector)]
if project_search:
    search_pattern = re.escape(project_search)
    matches = filtered_projects["project_id"].astype("string").str.contains(search_pattern, case=False, na=False) | filtered_projects["project_name"].astype("string").str.contains(search_pattern, case=False, na=False)
    filtered_projects = filtered_projects.loc[matches]

filtered_projects = (
    filtered_projects.drop_duplicates(subset=["project_id"], keep="first")
    .assign(_project_name_order=lambda frame: frame["project_name"].astype("string").str.casefold())
    .sort_values(["_project_name_order", "project_id"], kind="stable")
    .reset_index(drop=True)
)

st.markdown('<p class="projects-section-title">Project List</p>', unsafe_allow_html=True)
if filtered_projects.empty:
    st.info("No projects match the selected filters.")
    st.stop()

table_data = pd.DataFrame({
    "Project ID": filtered_projects["project_id"],
    "Project Name": filtered_projects["project_name"],
    "Ministry": filtered_projects["ministry"],
    "Sector": filtered_projects["sector"],
    "State": filtered_projects["state"],
    "Agency": filtered_projects["agency"],
})
styled_table = table_data.style.set_properties(
    **{
        "background-color": "#FFFFFF",
        "color": "#1F2933",
        "border-color": "#D9DEE5",
    }
)
st.caption(f"Showing {len(table_data):,} project(s). Select a row for details.")
filter_signature = "|".join([selected_month, selected_ministry, selected_sector, project_search.casefold()])
table_key = "projects_table_" + hashlib.sha1(filter_signature.encode("utf-8")).hexdigest()[:12]
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
        "State": st.column_config.TextColumn(width="medium"),
        "Agency": st.column_config.TextColumn(width="large"),
    },
)

selected_rows = table_event.selection.rows
if not selected_rows:
    st.info("Select a project row to view Project Details.")
    st.stop()

selected_project = filtered_projects.iloc[selected_rows[0]]
selected_project_id = str(selected_project["project_id"])

st.markdown('<p class="projects-section-title">Project Overview</p>', unsafe_allow_html=True)
_render_detail_panel(selected_project)

st.markdown('<p class="projects-section-title">Financial Details</p>', unsafe_allow_html=True)
original_cost = selected_project["original_cost_cr"]
expenditure = selected_project["cumulative_expenditure_cr"]
revised_cost = selected_project["revised_cost_cr"] if bool(selected_project["revised_cost_available"]) else None
financial_ratio = float(expenditure) / float(original_cost) * 100 if pd.notna(expenditure) and pd.notna(original_cost) and float(original_cost) > 0 else None
financial_columns = st.columns(4)
with financial_columns[0]:
    _render_metric("Original Cost", _format_crore(original_cost))
with financial_columns[1]:
    _render_metric("Latest Revised Cost", _format_crore(revised_cost))
with financial_columns[2]:
    _render_metric("Cumulative Expenditure", _format_crore(expenditure))
with financial_columns[3]:
    _render_metric("Financial Expenditure Ratio", _format_percentage(financial_ratio))

st.markdown('<p class="projects-section-title">Schedule & Physical Progress</p>', unsafe_allow_html=True)
schedule_values = [
    ("Approval Date", _safe(selected_project["approval_date"])),
    ("Start Date", _safe(selected_project["start_date"])),
    ("Original Target DoC", _safe(selected_project["original_target_doc"])),
    ("Revised DoC", _safe(selected_project["revised_doc"])),
    ("Physical Progress", _format_percentage(selected_project["physical_progress_pct"])),
]
schedule_columns = st.columns(5)
for column, (label, value) in zip(schedule_columns, schedule_values, strict=True):
    with column:
        _render_metric(label, value)

project_history = history.loc[history["project_id"].astype("string").eq(selected_project_id)].copy()
project_history = project_history.sort_values("report_month", kind="stable")

st.markdown('<p class="projects-section-title">Monthly History</p>', unsafe_allow_html=True)
history_table = pd.DataFrame({
    "Report Month": project_history["report_month"].map(_month_label),
    "Original Cost": project_history["original_cost_cr"].map(_format_crore),
    "Revised Cost": project_history.apply(lambda row: _format_crore(row["revised_cost_cr"]) if bool(row["revised_cost_available"]) else "Not available", axis=1),
    "Cumulative Expenditure": project_history["cumulative_expenditure_cr"].map(_format_crore),
    "Physical Progress": project_history["physical_progress_pct"].map(_format_percentage),
    "Revised DoC": project_history["revised_doc"].map(_safe),
    "Source Report": project_history["source_report"].map(_safe),
})
styled_history = history_table.style.set_properties(
    **{
        "background-color": "#FFFFFF",
        "color": "#1F2933",
        "border-color": "#D9DEE5",
    }
)
st.dataframe(styled_history, hide_index=True, use_container_width=True)

expenditure_history = project_history.dropna(subset=["cumulative_expenditure_cr"])
progress_history = project_history.dropna(subset=["physical_progress_pct"])
trend_columns = st.columns(2)
with trend_columns[0]:
    st.markdown('<p class="projects-section-title">Cumulative Expenditure Trend</p>', unsafe_allow_html=True)
    if len(expenditure_history) >= 2:
        expenditure_figure = go.Figure(go.Scatter(
            x=expenditure_history["report_month"].map(_month_label),
            y=expenditure_history["cumulative_expenditure_cr"],
            mode="lines+markers",
            line={"color": "#17365D", "width": 2},
            marker={"color": "#D99024", "size": 7},
            hovertemplate="%{x}<br>₹%{y:,.2f} crore<extra></extra>",
        ))
        expenditure_figure.update_layout(**_chart_layout("₹ crore"))
        st.plotly_chart(expenditure_figure, use_container_width=True)
    else:
        st.caption("A trend requires at least two reported expenditure observations.")

with trend_columns[1]:
    st.markdown('<p class="projects-section-title">Physical Progress Trend</p>', unsafe_allow_html=True)
    if len(progress_history) >= 2:
        progress_figure = go.Figure(go.Scatter(
            x=progress_history["report_month"].map(_month_label),
            y=progress_history["physical_progress_pct"],
            mode="lines+markers",
            line={"color": "#17365D", "width": 2},
            marker={"color": "#D99024", "size": 7},
            hovertemplate="%{x}<br>%{y:,.2f}%<extra></extra>",
        ))
        progress_figure.update_layout(**_chart_layout("Reported progress (%)"))
        st.plotly_chart(progress_figure, use_container_width=True)
    else:
        st.caption("A trend requires at least two reported progress observations.")

st.markdown(
    f'<p class="projects-source"><strong>Source:</strong> {_safe(selected_project["source_report"])}</p>',
    unsafe_allow_html=True,
)
