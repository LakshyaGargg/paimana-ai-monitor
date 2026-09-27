import streamlit as st


__all__ = [
    "apply_shared_styles",
    "render_brand_header",
    "render_login_footer",
    "render_login_identity",
    "render_login_institutional_header",
    "render_page_header",
    "render_sidebar_account",
]


SHARED_CSS = """
<style>
    :root {
        --paimana-background: #F7F8FA;
        --paimana-surface: #FFFFFF;
        --paimana-secondary-surface: #F2F4F7;
        --paimana-primary: #17365D;
        --paimana-primary-dark: #102A43;
        --paimana-accent: #D99024;
        --paimana-text: #1F2933;
        --paimana-secondary-text: #66727F;
        --paimana-border: #D9DEE5;
        --paimana-sidebar-text: #F2F4F7;
        --paimana-sidebar-muted: #D5DEE8;
        --paimana-sidebar-hover: #173B60;
        --paimana-sidebar-selected: #1D466F;
    }

    .stApp {
        background: var(--paimana-background);
        color: var(--paimana-text);
    }

    html, body, .stApp {
        font-family: "Segoe UI", Arial, sans-serif;
    }

    [data-testid="stHeader"] {
        background: var(--paimana-background);
    }

    [data-testid="stSidebar"] {
        background: var(--paimana-primary-dark);
        border-right: 1px solid #244762;
    }

    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] button {
        color: var(--paimana-sidebar-text);
    }

    [data-testid="stSidebarNav"] header,
    [data-testid="stSidebarNav"] [data-testid="stNavSectionHeader"] {
        color: #FFFFFF;
        font-weight: 750;
        letter-spacing: 0.05em;
    }

    [data-testid="stSidebarNav"] a {
        border-left: 3px solid transparent;
        border-radius: 4px;
        color: var(--paimana-sidebar-muted);
        margin: 0.15rem 0.5rem;
        transition: background-color 120ms ease, border-color 120ms ease;
    }

    [data-testid="stSidebarNav"] a span,
    [data-testid="stSidebarNav"] a p {
        color: inherit !important;
    }

    [data-testid="stSidebarNav"] a:hover {
        background: var(--paimana-sidebar-hover);
        color: #FFFFFF;
    }

    [data-testid="stSidebarNav"] a[aria-current="page"] {
        background: var(--paimana-sidebar-selected);
        border-left-color: var(--paimana-accent);
        color: #FFFFFF;
        font-weight: 650;
    }

    [data-testid="stToolbarActions"],
    #MainMenu {
        display: none;
    }

    .block-container {
        max-width: 1180px;
        padding-top: 2.5rem;
        padding-bottom: 3rem;
    }

    .paimana-brand {
        border-left: 4px solid var(--paimana-accent);
        padding: 0.15rem 0 0.15rem 1.1rem;
        margin-bottom: 1.75rem;
    }

    .paimana-wordmark {
        color: var(--paimana-primary);
        font-size: 2rem;
        font-weight: 750;
        letter-spacing: 0.055em;
        line-height: 1.15;
        margin: 0;
    }

    .paimana-system-name {
        color: var(--paimana-text);
        font-size: 1.05rem;
        font-weight: 600;
        margin: 0.35rem 0 0.85rem;
    }

    .paimana-ministry {
        color: var(--paimana-secondary-text);
        font-size: 0.92rem;
        line-height: 1.55;
        margin: 0;
    }

    .page-heading {
        color: var(--paimana-primary-dark);
        font-size: 1.75rem;
        font-weight: 700;
        margin: 0 0 0.45rem;
    }

    .page-introduction {
        color: var(--paimana-secondary-text);
        font-size: 1rem;
        margin: 0;
    }

    .page-heading-rule {
        border: 0;
        border-top: 1px solid var(--paimana-border);
        margin: 1.25rem 0 0;
    }

    .login-institutional-header {
        background: var(--paimana-surface);
        border-bottom: 3px solid var(--paimana-primary);
        box-sizing: border-box;
        margin-left: calc(50% - 50vw);
        padding: 0.8rem max(2rem, calc((100vw - 1120px) / 2));
        width: 100vw;
    }

    .login-government {
        color: var(--paimana-primary-dark);
        font-size: 0.76rem;
        font-weight: 750;
        letter-spacing: 0.11em;
        margin: 0 0 0.32rem;
        text-transform: uppercase;
    }

    .login-ministry {
        color: var(--paimana-text);
        font-size: 0.9rem;
        font-weight: 650;
        line-height: 1.45;
        margin: 0;
    }

    .login-identity {
        margin: 1.55rem auto 1.3rem;
        text-align: center;
    }

    .login-wordmark {
        color: var(--paimana-primary);
        font-size: 1.9rem;
        font-weight: 750;
        letter-spacing: 0.08em;
        line-height: 1.15;
        margin: 0;
    }

    .login-system-name {
        color: var(--paimana-text);
        font-size: 1rem;
        font-weight: 600;
        margin: 0.38rem 0 0;
    }

    .login-title {
        color: var(--paimana-primary-dark);
        font-size: 1.25rem;
        font-weight: 700;
        margin: 0 0 1.15rem;
        text-align: center;
    }

    [data-testid="stVerticalBlockBorderWrapper"] {
        background: var(--paimana-surface);
        border-color: var(--paimana-border) !important;
        border-radius: 5px;
        box-shadow: 0 4px 14px rgba(67, 53, 38, 0.07);
    }

    [data-testid="stVerticalBlockBorderWrapper"] > div {
        padding: 0.2rem 0.35rem;
    }

    .stTextInput input {
        background: #ffffff;
        border: 1px solid var(--paimana-border);
        border-radius: 3px;
        color: var(--paimana-text);
    }

    .stTextInput label,
    .stTextInput [data-testid="stWidgetLabel"] p,
    .stCheckbox label,
    .stCheckbox [data-testid="stWidgetLabel"] p {
        color: var(--paimana-text) !important;
        font-size: 0.92rem;
        font-weight: 650;
    }

    .stTextInput input:focus {
        border-color: var(--paimana-primary);
        box-shadow: 0 0 0 1px var(--paimana-primary);
    }

    .stButton > button[kind="primary"] {
        background: var(--paimana-primary);
        border: 1px solid var(--paimana-primary);
        border-radius: 3px;
        color: #ffffff;
        font-weight: 650;
    }

    .stButton > button[kind="primary"]:hover {
        background: var(--paimana-primary-dark);
        border-color: var(--paimana-primary-dark);
    }

    .authorization-note {
        color: var(--paimana-secondary-text);
        font-size: 0.84rem;
        margin: 0.9rem 0 0;
        text-align: center;
    }

    .login-footer {
        border-top: 1px solid var(--paimana-border);
        color: var(--paimana-secondary-text);
        font-size: 0.76rem;
        margin: 1.5rem auto 0;
        max-width: 680px;
        padding-top: 0.8rem;
        text-align: center;
    }

    .sidebar-account {
        border-top: 1px solid rgba(217, 222, 229, 0.32);
        color: #FFFFFF !important;
        font-size: 0.92rem;
        font-weight: 650;
        margin-top: 2rem;
        padding-top: 1rem;
    }

    [data-testid="stSidebar"] .stButton > button {
        background: rgba(255, 255, 255, 0.06);
        border: 1px solid rgba(255, 255, 255, 0.45);
        border-radius: 4px;
        color: #FFFFFF !important;
        font-weight: 650;
    }

    [data-testid="stSidebar"] .stButton > button p {
        color: #FFFFFF !important;
    }

    [data-testid="stSidebar"] .stButton > button:hover {
        background: var(--paimana-sidebar-hover);
        border-color: rgba(255, 255, 255, 0.7);
        color: #FFFFFF !important;
    }

    [data-testid="stAlert"] {
        border-radius: 3px;
    }
</style>
"""


def apply_shared_styles(show_sidebar: bool = True) -> None:
    """Apply the common PAIMANA visual system to the current page."""
    sidebar_rule = "" if show_sidebar else """
        [data-testid="stSidebar"], [data-testid="collapsedControl"] {
            display: none;
        }

        .block-container {
            padding-top: 0 !important;
            padding-bottom: 1.25rem !important;
        }
    """
    rendered_css = SHARED_CSS.replace("</style>", f"{sidebar_rule}</style>")
    st.html(rendered_css)


def render_login_institutional_header() -> None:
    """Render the compact Government of India identity on the login page."""
    st.markdown(
        """
        <header class="login-institutional-header">
            <p class="login-government">Government of India</p>
            <p class="login-ministry">
                Ministry of Statistics and Programme Implementation<br>
                Infrastructure and Project Monitoring Division
            </p>
        </header>
        """,
        unsafe_allow_html=True,
    )


def render_login_identity() -> None:
    """Render the centered PAIMANA application identity."""
    st.markdown(
        """
        <section class="login-identity">
            <p class="login-wordmark">PAIMANA</p>
            <p class="login-system-name">Infrastructure Project Monitoring System</p>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_login_footer() -> None:
    """Render the minimal login-page footer."""
    st.markdown(
        """
        <footer class="login-footer">
            PAIMANA | Ministry of Statistics and Programme Implementation
        </footer>
        """,
        unsafe_allow_html=True,
    )


def render_brand_header() -> None:
    """Render the shared ministry and application identity."""
    st.markdown(
        """
        <header class="paimana-brand">
            <p class="paimana-wordmark">PAIMANA</p>
            <p class="paimana-system-name">Infrastructure Project Monitoring System</p>
            <p class="paimana-ministry">
                Ministry of Statistics and Programme Implementation<br>
                Infrastructure and Project Monitoring Division
            </p>
        </header>
        """,
        unsafe_allow_html=True,
    )


def render_page_header(title: str, introduction: str | None = None) -> None:
    """Render a consistent heading for an authenticated application page."""
    introduction_html = (
        f'<p class="page-introduction">{introduction}</p>' if introduction else ""
    )
    st.markdown(
        f"""
        <section>
            <h1 class="page-heading">{title}</h1>
            {introduction_html}
            <hr class="page-heading-rule">
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_account() -> bool:
    """Render the signed-in account label and return whether Logout was clicked."""
    with st.sidebar:
        st.markdown(
            '<p class="sidebar-account">Monitoring Officer</p>',
            unsafe_allow_html=True,
        )
        return st.button("Logout", use_container_width=True)
