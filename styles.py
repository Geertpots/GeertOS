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
    h1, h2, h3, p, label {{
        color: var(--pv-text) !important;
        overflow-wrap: anywhere;
        word-break: normal;
    }}
    [data-testid="stMarkdownContainer"],
    [data-testid="stCaptionContainer"],
    [data-testid="stMetric"],
    [data-testid="stAlertContainer"] {{
        min-width: 0;
        max-width: 100%;
        overflow-wrap: anywhere;
    }}
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
    .pv-today-hero {{
        display: flex; align-items: center; justify-content: space-between;
        gap: 1.25rem; padding: 1.5rem 1.65rem;
        border: 1px solid var(--pv-border); border-radius: 20px;
        margin: .25rem 0 1.3rem;
        background: linear-gradient(135deg, var(--pv-panel), rgba(32,201,151,.10));
    }}
    .pv-today-hero h1 {{
        margin: .3rem 0 .15rem; font-size: clamp(1.8rem, 4vw, 3rem);
    }}
    .pv-today-hero p {{ color: var(--pv-muted) !important; margin: 0; }}
    .pv-status {{
        display: flex; flex-direction: column; min-width: 15rem;
        padding: .85rem 1rem; border-radius: 14px;
        border: 1px solid var(--pv-border); background: var(--pv-panel);
    }}
    .pv-status span {{ font-size: 1.05rem; font-weight: 800; }}
    .pv-status small {{
        color: var(--pv-muted); margin-top: .25rem; line-height: 1.35;
    }}
    .pv-status-good {{ border-left: 5px solid var(--pv-green); }}
    .pv-status-attention {{ border-left: 5px solid var(--pv-gold); }}
    .pv-status-action {{ border-left: 5px solid var(--pv-red); }}
    [data-testid="stMetric"] {{
        background: var(--pv-panel); border: 1px solid var(--pv-border);
        padding: 1rem 1.1rem; border-radius: 16px;
    }}
    [data-testid="stMetricLabel"] {{ color: var(--pv-muted); }}
    [data-testid="stDataFrame"], [data-testid="stTable"], [data-testid="stForm"] {{
        border: 1px solid var(--pv-border); border-radius: 16px;
    }}
    [data-testid="stDataFrame"], [data-testid="stTable"] {{
        display: block;
        width: 100%;
        max-width: 100%;
        overflow-x: auto;
        overflow-y: hidden;
        -webkit-overflow-scrolling: touch;
    }}
    [data-testid="stDataFrame"] > div,
    [data-testid="stTable"] > div {{
        min-width: max-content;
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
        .block-container {{
            width: 100%;
            max-width: 100%;
            padding: 1rem .8rem 4rem;
            overflow-x: hidden;
        }}
        .pv-hero {{ padding: 1.1rem; border-radius: 15px; }}
        .pv-today-hero {{
            align-items: stretch; flex-direction: column;
            padding: 1.1rem; border-radius: 15px;
        }}
        .pv-today-hero h1 {{
            font-size: clamp(1.65rem, 8vw, 2.15rem);
            line-height: 1.15;
        }}
        .pv-status {{ min-width: 0; width: 100%; }}
        .pv-hero h1 {{
            font-size: clamp(1.65rem, 8vw, 2.15rem);
            line-height: 1.15;
        }}
        [data-testid="stHorizontalBlock"] {{
            flex-wrap: wrap;
            gap: .75rem;
        }}
        [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {{
            flex: 1 1 100% !important;
            width: 100% !important;
            min-width: 0 !important;
        }}
        [data-testid="stMetric"] {{
            width: 100%;
            padding: .9rem 1rem;
        }}
        [data-testid="stMetricValue"] {{
            font-size: clamp(1.45rem, 8vw, 2rem);
            line-height: 1.2;
            white-space: normal;
            overflow-wrap: anywhere;
        }}
        [data-testid="stMetricDelta"] {{
            white-space: normal;
            overflow-wrap: anywhere;
        }}
        [data-testid="stDataFrame"], [data-testid="stTable"] {{
            border-radius: 12px;
            overscroll-behavior-inline: contain;
        }}
        .stButton > button, .stDownloadButton > button {{
            width: 100%;
            min-height: 2.75rem;
            white-space: normal;
        }}
    }}
    </style>
    """
