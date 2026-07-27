"""Responsive application styling."""


def css(dark: bool) -> str:
    bg = "#0b1220" if dark else "#f4f7fb"
    panel = "#111c2f" if dark else "#ffffff"
    text = "#f7fafc" if dark else "#14213d"
    muted = "#9aabc4" if dark else "#61708a"
    border = "#243552" if dark else "#dce3ed"
    return f"""
    <style>
    :root {{
        --pv-bg: {bg}; --pv-panel: {panel}; --pv-text: {text};
        --pv-muted: {muted}; --pv-border: {border};
        --pv-green: #20c997; --pv-gold: #d5a64a; --pv-red: #ff6b6b;
    }}
    .stApp {{ background: var(--pv-bg); color: var(--pv-text); }}
    [data-testid="stSidebar"] {{ background: var(--pv-panel); }}
    [data-testid="stHeader"] {{ background: transparent; }}
    h1, h2, h3, p, label {{ color: var(--pv-text) !important; }}
    .pv-hero {{
        padding: 1.5rem 1.65rem; border: 1px solid var(--pv-border);
        border-radius: 20px; margin: .25rem 0 1.3rem;
        background: linear-gradient(135deg, var(--pv-panel), rgba(32,201,151,.10));
    }}
    .pv-kicker {{
        color: var(--pv-green); font-size: .78rem; font-weight: 800;
        letter-spacing: .12em; text-transform: uppercase;
    }}
    .pv-hero h1 {{ margin: .3rem 0 .15rem; font-size: clamp(1.8rem, 4vw, 3rem); }}
    .pv-hero p {{ color: var(--pv-muted) !important; margin: 0; }}
    [data-testid="stMetric"] {{
        background: var(--pv-panel); border: 1px solid var(--pv-border);
        padding: 1rem 1.1rem; border-radius: 16px;
    }}
    [data-testid="stMetricLabel"] {{ color: var(--pv-muted); }}
    [data-testid="stDataFrame"], [data-testid="stForm"] {{
        border: 1px solid var(--pv-border); border-radius: 16px;
    }}
    .stButton > button, .stDownloadButton > button {{
        border-radius: 10px; border: 0; font-weight: 700;
        background: var(--pv-green); color: #07130f;
    }}
    .pv-note {{
        padding: .8rem 1rem; border-left: 3px solid var(--pv-gold);
        background: var(--pv-panel); color: var(--pv-muted); border-radius: 8px;
    }}
    @media (max-width: 700px) {{
        .block-container {{ padding: 1rem .8rem 4rem; }}
        .pv-hero {{ padding: 1.1rem; border-radius: 15px; }}
    }}
    </style>
    """

