"""GeertOS – Freedom Edition: persoonlijke financiële cockpit."""

# Sprint 8D deployment marker: forces a clean rebuild after all modules are online.
from __future__ import annotations

from datetime import date, datetime

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from calculations import (
    money,
    net_worth,
    portfolio_summary,
    monte_carlo_income_plan,
    decision_label,
)
from financial_engine import FinancialEngine
from cockpit import daily_insights, greeting, plan_status
from planning_analysis import compare_scenarios
from advisor import answer_question
from database import (
    SyncConflictError,
    backend_name,
    get_settings,
    get_sync_version,
    init_db,
    read_table,
    replace_balance_with_freedom_plan,
    replace_table,
    set_settings,
    create_backup,
    validate_backup,
    add_opa_transaction,
    clean_bitcoin_transactions,
)
from styles import css
from security import access_control_enabled, require_access


st.set_page_config(
    page_title="GeertOS – Freedom Edition",
    page_icon="🟦",
    layout="wide",
    initial_sidebar_state="auto",
)
require_access()
try:
    init_db()
except Exception:
    st.error(
        "GeertOS kan de centrale database nu niet bereiken. "
        "Je gegevens zijn niet gewijzigd. Probeer het over enkele minuten opnieuw."
    )
    st.stop()
settings = get_settings()

if "_sync_notice" in st.session_state:
    st.warning(st.session_state.pop("_sync_notice"))


def save_synced_table(
    table: str,
    frame: pd.DataFrame,
    expected_version: int,
) -> bool:
    """Sla centraal op en herlaad veilig bij een gelijktijdige wijziging."""
    try:
        replace_table(table, frame, expected_version=expected_version)
    except SyncConflictError as exc:
        st.session_state["_sync_notice"] = str(exc)
        st.rerun()
    except ValueError as exc:
        st.error(str(exc))
        return False
    return True


def number(key: str, default: float = 0.0) -> float:
    try:
        return float(settings.get(key, default))
    except (TypeError, ValueError):
        return default


def integer(key: str, default: int = 0) -> int:
    return int(number(key, default))


def page_header(title: str, subtitle: str) -> None:
    st.markdown(
        f"""
        <div class="pv-hero">
          <div class="pv-kicker">GeertOS · Freedom Edition</div>
          <h1>{title}</h1>
          <p>{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def chart_layout(fig: go.Figure, dark: bool, height: int = 370) -> go.Figure:
    fig.update_layout(
        height=height,
        margin=dict(l=15, r=15, t=45, b=15),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#f7fafc" if dark else "#14213d",
        legend_title_text="",
    )
    return fig


def make_engine() -> FinancialEngine:
    """Laad één consistente cloudmomentopname voor de centrale rekenmotor."""
    return FinancialEngine(
        settings,
        balance_items=read_table("balance_items"),
        etf_positions=read_table("etf_positions"),
        bitcoin_transactions=read_table("bitcoin_transactions"),
        expenses=read_table("expenses"),
    )


def make_annuity() -> pd.DataFrame:
    return make_engine().evaluate().annuity


def make_projection() -> pd.DataFrame:
    return make_engine().evaluate().projection


dark_mode = st.sidebar.toggle(
    "Donkere modus",
    value=settings.get("dark_mode", "1") == "1",
    help="Schakel tussen de lichte en donkere weergave.",
)
set_settings({"dark_mode": int(dark_mode)})
st.markdown(css(dark_mode), unsafe_allow_html=True)

st.sidebar.markdown("## 🟦 GeertOS")
st.sidebar.caption("Freedom Edition · financiële cockpit")
if access_control_enabled():
    st.sidebar.caption("🔒 Toegangscode actief")
else:
    st.sidebar.caption("💻 Alleen lokaal · geen toegangscode ingesteld")
st.sidebar.success("Sprint 10C · Veilige adviseur actief")
st.sidebar.caption(f"Bronmap: {__file__}")
PAGES = [
    "Vandaag",
    "Dashboard",
    "Persoonlijke waarheid",
    "Familie",
    "Opa-fonds",
    "Project Vrijheid",
    "Vrijheidstijdlijn",
    "Netto vermogen",
    "ETF-portefeuille",
    "Bitcoin-portefeuille",
    "Pensioenplanning",
    "Lijfrenteplanning",
    "Netto maandinkomen",
    "Uitgavenplanner",
    "Scenarioanalyse",
    "AI-assistent",
    "Plancontrole",
    "Beslislab",
    "Grafieken",
    "Mijn uitgangspunten",
]
NAVIGATION_LABELS = {
    "Vandaag": "🏠 Vandaag",
    "Dashboard": "🏠 Financieel dashboard",
    "Persoonlijke waarheid": "🔎 Controle · Persoonlijke waarheid",
    "Familie": "👨‍👩‍👧 Familie · Overzicht",
    "Opa-fonds": "👨‍👩‍👧 Familie · Opa-fonds",
    "Project Vrijheid": "🎯 Vrijheid · Project Vrijheid",
    "Vrijheidstijdlijn": "🎯 Vrijheid · Tijdlijn 2026–2047",
    "Netto vermogen": "💰 Vermogen · Netto vermogen",
    "ETF-portefeuille": "📈 Beleggingen · ETF",
    "Bitcoin-portefeuille": "📈 Beleggingen · Bitcoin",
    "Pensioenplanning": "🏦 Pensioen · Pensioenplanning",
    "Lijfrenteplanning": "🏦 Pensioen · Lijfrenteplanning",
    "Netto maandinkomen": "🎯 Vrijheid · Netto maandinkomen",
    "Uitgavenplanner": "💰 Vermogen · Uitgavenplanner",
    "Scenarioanalyse": "📊 Analyse · Scenarioanalyse",
    "AI-assistent": "🤖 Adviseur · AI-assistent",
    "Plancontrole": "📊 Analyse · Plancontrole",
    "Beslislab": "📊 Analyse · Beslislab",
    "Grafieken": "📊 Analyse · Grafieken",
    "Mijn uitgangspunten": "⚙️ Instellingen · Uitgangspunten",
}
page = st.sidebar.selectbox(
    "Ga naar",
    PAGES,
    format_func=lambda item: NAVIGATION_LABELS[item],
    key="main_navigation",
)
st.sidebar.divider()
if backend_name() == "postgresql":
    st.sidebar.caption("Cloud actief · laptop en iPhone gebruiken dezelfde gegevens")
else:
    st.sidebar.caption("Lokale herstelmodus · gegevens staan in SQLite")


def parse_date(value: object) -> date | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


def age_on(birth_date: date, today: date | None = None) -> int:
    today = today or date.today()
    return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))


def months_until_18(birth_date: date, today: date | None = None) -> int:
    today = today or date.today()
    eighteenth = birth_date.replace(year=birth_date.year + 18)
    months = (eighteenth.year - today.year) * 12 + eighteenth.month - today.month
    if eighteenth.day > today.day:
        months += 1
    return max(months, 0)


def required_monthly_deposit(current: float, target: float, months: int, annual_return_pct: float) -> float:
    if months <= 0:
        return max(target - current, 0.0)
    monthly_rate = annual_return_pct / 100 / 12
    future_current = current * ((1 + monthly_rate) ** months)
    gap = max(target - future_current, 0.0)
    if gap <= 0:
        return 0.0
    if monthly_rate == 0:
        return gap / months
    factor = (((1 + monthly_rate) ** months) - 1) / monthly_rate
    return gap / factor


def opa_summary() -> pd.DataFrame:
    funds = read_table("opa_funds")
    transactions = read_table("opa_transactions")
    if funds.empty:
        return funds
    totals = transactions.groupby("child_name")["amount"].sum() if not transactions.empty else pd.Series(dtype=float)
    rows = []
    for _, item in funds.iterrows():
        birth = parse_date(item["birth_date"])
        current = float(totals.get(item["child_name"], 0.0))
        target = float(item["target_amount"] or 25000)
        months = months_until_18(birth) if birth else 0
        monthly = required_monthly_deposit(current, target, months, float(item["expected_return_pct"] or 0))
        rows.append({
            "child_name": item["child_name"],
            "birth_date": item["birth_date"],
            "current": current,
            "target": target,
            "remaining": max(target-current, 0),
            "progress": min(current / target * 100, 100) if target else 0,
            "months": months,
            "monthly_needed": monthly,
            "return_pct": float(item["expected_return_pct"] or 0),
        })
    return pd.DataFrame(rows)


def navigate_to(destination: str) -> None:
    """Open een bestaande GeertOS-module via de centrale navigatie."""
    st.session_state["main_navigation"] = destination


def today_page() -> None:
    """Centrale dagelijkse cockpit, gevoed door één financiële momentopname."""
    now = datetime.now()
    result = make_engine().evaluate()
    projection = result.projection
    first_year = projection.iloc[0]
    status = plan_status(result, settings)
    insights = daily_insights(result, settings)

    day_names = [
        "maandag", "dinsdag", "woensdag", "donderdag",
        "vrijdag", "zaterdag", "zondag",
    ]
    month_names = [
        "januari", "februari", "maart", "april", "mei", "juni",
        "juli", "augustus", "september", "oktober", "november", "december",
    ]
    date_label = (
        f"{day_names[now.weekday()]} {now.day} "
        f"{month_names[now.month - 1]} {now.year}"
    )

    st.markdown(
        f"""
        <div class="pv-today-hero">
          <div>
            <div class="pv-kicker">GeertOS · Vandaag</div>
            <h1>{greeting(now)} Geert</h1>
            <p>{date_label} · bijgewerkt om {now:%H:%M}</p>
          </div>
          <div class="pv-status pv-status-{status['level']}">
            <span>{status['label']}</span>
            <small>{status['message']}</small>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="pv-section-title">Hoe je er vandaag voor staat</div>',
        unsafe_allow_html=True,
    )
    a, b, c, d = st.columns(4)
    a.metric("Netto vermogen na verkoop", money(result.post_sale_net_worth))
    b.metric(
        f"Netto inkomen {int(first_year['year'])}",
        money(float(first_year["actual"])),
        "per maand",
    )
    c.metric("ETF-portefeuille", money(result.etf["value"]))
    d.metric("Bitcoin-portefeuille", money(result.bitcoin_value))

    a, b, c = st.columns(3)
    a.metric(
        "Pensioen + lijfrente",
        money(result.pension_monthly + result.annuity_monthly),
        "per maand",
    )
    b.metric("Netto cash bij verkoop", money(result.sale["net_cash"]))
    c.metric(
        "Verwacht ETF-restvermogen 2047",
        money(float(result.projection_health["end_balance"])),
    )

    st.markdown(
        '<div class="pv-section-title">Voortgang financiële vrijheid</div>',
        unsafe_allow_html=True,
    )
    score = max(0, min(100, int(result.freedom_score)))
    st.progress(score / 100, text=f"Vrijheidsstatus: {score}%")
    with st.expander("Hoe wordt deze status bepaald?"):
        components = result.freedom_components
        left, right = st.columns(2)
        left.metric(
            "Inkomen op koers",
            f"{int(components['budget_score'])}%",
            "weegt voor 55%",
        )
        right.metric(
            "Buffer in 2047",
            f"{int(components['reserve_score'])}%",
            "weegt voor 45%",
        )
        st.write(
            "De status gebruikt uitsluitend de centrale GeertOS-berekeningen: "
            "je werkelijke uitgaven, gewenste maandinkomen, resterend vermogen "
            "in 2047 en de verhouding tot het geplande startvermogen."
        )
        st.caption(
            "Dit is een planningsindicator en geen garantie of zelfstandig financieel advies."
        )

    st.markdown(
        '<div class="pv-section-title">Belangrijk vandaag</div>',
        unsafe_allow_html=True,
    )
    for index, insight in enumerate(insights):
        message = f"**{insight.title}**  \n{insight.message}"
        getattr(st, insight.level)(message)
        st.button(
            f"Bekijk {insight.destination}",
            key=f"today_insight_{index}",
            on_click=navigate_to,
            args=(insight.destination,),
        )

    st.markdown(
        '<div class="pv-section-title">Direct naar</div>',
        unsafe_allow_html=True,
    )
    quick_links = [
        ("🎯", "Project Vrijheid"),
        ("🗓️", "Vrijheidstijdlijn"),
        ("💰", "Netto vermogen"),
        ("📈", "ETF-portefeuille"),
        ("🏦", "Pensioenplanning"),
        ("👨‍👩‍👧", "Familie"),
        ("👴", "Opa-fonds"),
        ("📊", "Plancontrole"),
        ("🔎", "Persoonlijke waarheid"),
        ("🤖", "AI-assistent"),
    ]
    for start in range(0, len(quick_links), 4):
        columns = st.columns(4)
        for column, (icon, destination) in zip(
            columns, quick_links[start:start + 4]
        ):
            column.button(
                f"{icon} {destination}",
                key=f"today_link_{destination}",
                use_container_width=True,
                on_click=navigate_to,
                args=(destination,),
            )

    st.caption(
        "Alle bedragen op deze pagina komen uit dezelfde centrale rekenmotor "
        "en dezelfde cloudgegevens als de bestaande Sprint 9-pagina’s."
    )


def dashboard() -> None:
    page_header(
        "Project Vrijheid",
        "Jouw financiële cockpit: verkoop, vermogen, inkomen en toekomst in één overzicht.",
    )

    engine = make_engine()
    base_price = number("sale_property_price", 1595000)
    scenario_price = float(
        st.session_state.get("dashboard_sale_price", base_price)
    )
    result = engine.evaluate({"sale_property_price": scenario_price})
    projection = result.projection

    st.markdown(
        '<div class="pv-section-title">Financiële positie</div>',
        unsafe_allow_html=True,
    )
    a, b, c, d = st.columns(4)
    a.metric("Netto vermogen na verkoop", money(result.post_sale_net_worth))
    b.metric(
        "ETF-portefeuille",
        money(result.etf["value"]),
        f"{result.etf['return_pct']:.1f}%",
    )
    c.metric(
        "Bitcoin-portefeuille",
        money(result.bitcoin_value),
        f"{result.bitcoin_amount:.6f} BTC",
    )
    d.metric(
        "Pensioen + lijfrente p/m",
        money(result.pension_monthly + result.annuity_monthly),
    )

    st.markdown(
        '<div class="pv-section-title">Verkoopscenario POTZ WONEN</div>',
        unsafe_allow_html=True,
    )
    scenario_price = st.slider(
        "Verkoopprijs pand",
        min_value=1300000,
        max_value=1800000,
        value=int(min(max(base_price, 1300000), 1800000)),
        step=25000,
        format="€ %d",
        help="Schuif om direct te zien wat een andere verkoopprijs betekent.",
        key="dashboard_sale_price",
    )
    sale = result.sale
    a, b, c, d = st.columns(4)
    a.metric("Verkoopprijs pand", money(scenario_price))
    b.metric("Bruto verkoop", money(sale["gross"]))
    c.metric("Netto cash", money(sale["net_cash"]))
    d.metric("Totaal na verkoop", money(sale["total_after_sale"]))

    goal = number("sale_net_cash_goal", 600000)
    difference = sale["net_cash"] - goal
    if difference >= 0:
        st.success(f"Dit scenario ligt {money(difference)} boven je netto-cashdoel.")
    else:
        st.warning(f"Dit scenario ligt {money(abs(difference))} onder je netto-cashdoel.")

    if st.button(
        "Gebruik deze verkoopprijs in Project Vrijheid",
        use_container_width=True,
    ):
        set_settings({"sale_property_price": scenario_price})
        st.success("De verkoopprijs is opgeslagen in Project Vrijheid.")

    st.markdown(
        '<div class="pv-section-title">Inkomen en vermogen tot 2047</div>',
        unsafe_allow_html=True,
    )
    first_year = projection.iloc[0]
    last_year = projection.iloc[-1]
    a, b, c, d = st.columns(4)
    a.metric(
        f"Netto inkomen {int(first_year['year'])}",
        money(float(first_year["actual"])),
        "per maand",
    )
    b.metric(
        "Gewenst netto p/m",
        money(number("target_monthly", 4000)),
    )
    c.metric(
        f"ETF-vermogen {int(last_year['year'])}",
        money(float(last_year["etf_closing"])),
    )
    d.metric(
        "ETF-opname eerste jaar",
        money(float(first_year["etf_withdrawal"])),
        "per maand",
    )

    left, right = st.columns([1.6, 1])
    with left:
        fig = px.area(
            projection,
            x="year",
            y="etf_closing",
            title="Vermogensontwikkeling",
            labels={"year": "Jaar", "etf_closing": "Vermogen"},
            color_discrete_sequence=["#20c997"],
        )
        st.plotly_chart(chart_layout(fig, dark_mode), use_container_width=True)
    with right:
        income_frame = projection[["year", "target", "actual"]].melt(
            "year",
            var_name="Reeks",
            value_name="Netto per maand",
        )
        income_frame["Reeks"] = income_frame["Reeks"].replace(
            {"target": "Doel", "actual": "Beschikbaar"}
        )
        fig = px.line(
            income_frame,
            x="year",
            y="Netto per maand",
            color="Reeks",
            title="Netto maandinkomen",
            labels={"year": "Jaar"},
            color_discrete_map={"Doel": "#d5a64a", "Beschikbaar": "#5b8def"},
        )
        st.plotly_chart(chart_layout(fig, dark_mode), use_container_width=True)

    st.subheader("Netto maandinkomen: eerstvolgende jaren")
    preview = projection.head(6).copy()
    preview.columns = [
        "Jaar",
        "Doel",
        "Lijfrente",
        "AOW",
        "Pensioen",
        "Bijverdienen",
        "ETF-opname",
        "Beschikbaar",
        "ETF eindstand",
    ]
    st.dataframe(preview, hide_index=True, use_container_width=True)


def balance_page() -> None:
    page_header(
        "Netto vermogen",
        "Bezittingen en schulden overzichtelijk op één balans.",
    )
    sync_version = get_sync_version("balance_items")
    frame = read_table("balance_items")
    assets = frame.loc[frame["item_type"] == "asset", "amount"].sum()
    debts = frame.loc[frame["item_type"] == "liability", "amount"].sum()
    private_frame = frame.loc[frame["owner_scope"] == "Privé"]
    bv_frame = frame.loc[frame["owner_scope"] == "BV"]
    private_net = (
        private_frame.loc[private_frame["item_type"] == "asset", "amount"].sum()
        - private_frame.loc[private_frame["item_type"] == "liability", "amount"].sum()
    )
    bv_net = (
        bv_frame.loc[bv_frame["item_type"] == "asset", "amount"].sum()
        - bv_frame.loc[bv_frame["item_type"] == "liability", "amount"].sum()
    )
    a, b, c, d, e = st.columns(5)
    a.metric("Bezittingen", money(assets))
    b.metric("Schulden", money(debts))
    c.metric("Netto vermogen", money(net_worth([assets], [debts])))
    d.metric("Privé", money(private_net))
    e.metric("BV", money(bv_net))

    st.subheader("Balans bijwerken")
    edited = st.data_editor(
        frame.drop(columns=["id"]),
        num_rows="dynamic",
        hide_index=True,
        use_container_width=True,
        column_config={
            "category": st.column_config.TextColumn("Categorie", required=True),
            "name": st.column_config.TextColumn("Omschrijving", required=True),
            "amount": st.column_config.NumberColumn(
                "Bedrag", min_value=0.0, format="€ %.2f", required=True
            ),
            "item_type": st.column_config.SelectboxColumn(
                "Soort",
                options=["asset", "liability"],
                required=True,
                help="asset = bezit, liability = schuld",
            ),
            "owner_scope": st.column_config.SelectboxColumn(
                "Waar staat het?",
                options=["Privé", "BV"],
                required=True,
            ),
        },
        key="balance_editor",
    )
    if st.button("Balans opslaan", type="primary"):
        if save_synced_table("balance_items", edited, sync_version):
            st.success("Balans opgeslagen.")
            st.rerun()


def etf_page() -> None:
    page_header(
        "ETF-portefeuille",
        "Verdeling, rendement en actuele waarde van je beleggingen.",
    )
    sync_version = get_sync_version("etf_positions")
    frame = read_table("etf_positions")
    summary = portfolio_summary(frame)
    a, b, c = st.columns(3)
    a.metric("Ingelegd", money(summary["invested"]))
    b.metric("Actuele waarde", money(summary["value"]))
    c.metric("Resultaat", money(summary["result"]), f"{summary['return_pct']:.1f}%")

    if not frame.empty and frame["value"].sum() > 0:
        left, right = st.columns([1, 1.35])
        with left:
            fig = px.pie(
                frame,
                names="ticker",
                values="value",
                hole=.62,
                title="Portefeuilleverdeling",
                color_discrete_sequence=["#20c997", "#d5a64a", "#5b8def", "#9b7ede"],
            )
            st.plotly_chart(chart_layout(fig, dark_mode), use_container_width=True)
        with right:
            chart = frame.melt(
                id_vars=["ticker"],
                value_vars=["invested", "value"],
                var_name="type",
                value_name="amount",
            )
            fig = px.bar(
                chart,
                x="ticker",
                y="amount",
                color="type",
                barmode="group",
                title="Inleg tegenover actuele waarde",
                labels={"ticker": "ETF", "amount": "Bedrag"},
                color_discrete_map={"invested": "#61708a", "value": "#20c997"},
            )
            st.plotly_chart(chart_layout(fig, dark_mode), use_container_width=True)

    edited = st.data_editor(
        frame.drop(columns=["id"]),
        num_rows="dynamic",
        hide_index=True,
        use_container_width=True,
        column_config={
            "name": st.column_config.TextColumn("Naam", required=True),
            "ticker": st.column_config.TextColumn("Ticker", required=True),
            "invested": st.column_config.NumberColumn("Ingelegd", format="€ %.2f"),
            "value": st.column_config.NumberColumn("Actuele waarde", format="€ %.2f"),
        },
        key="etf_editor",
    )
    if st.button("ETF-portefeuille opslaan", type="primary"):
        if save_synced_table("etf_positions", edited, sync_version):
            set_settings({"etf_start": float(edited["value"].sum())})
            st.success("ETF-portefeuille opgeslagen.")
            st.rerun()


def bitcoin_page() -> None:
    page_header(
        "Bitcoin-portefeuille",
        "Leg aankopen vast en volg kostprijs, bezit en actuele waarde.",
    )
    sync_version = get_sync_version("bitcoin_transactions")
    frame = read_table("bitcoin_transactions")
    total_btc = float(frame["btc_amount"].sum()) if not frame.empty else 0.0
    total_cost = float(frame["amount_eur"].sum()) if not frame.empty else 0.0
    current_price = st.number_input(
        "Actuele Bitcoin-prijs",
        min_value=0.0,
        value=number("bitcoin_current_price", 60000),
        step=500.0,
        format="%.2f",
        help="Vul handmatig de actuele koers in. Er is geen internetverbinding nodig.",
    )
    current_value = total_btc * current_price
    avg_price = total_cost / total_btc if total_btc else 0.0
    a, b, c, d = st.columns(4)
    a.metric("Bitcoin", f"{total_btc:.6f} BTC")
    b.metric("Totale inleg", money(total_cost))
    c.metric("Gem. aankoopkoers", money(avg_price))
    d.metric("Actuele waarde", money(current_value), money(current_value - total_cost))

    editable = frame.drop(columns=["id"])
    if editable.empty:
        editable = pd.DataFrame(
            columns=["trade_date", "amount_eur", "btc_amount", "note"]
        )
    edited = st.data_editor(
        editable,
        num_rows="dynamic",
        hide_index=True,
        use_container_width=True,
        column_config={
            "trade_date": st.column_config.TextColumn(
                "Datum", help="Bijvoorbeeld 2026-07-25"
            ),
            "amount_eur": st.column_config.NumberColumn("Inleg", format="€ %.2f"),
            "btc_amount": st.column_config.NumberColumn("BTC", format="%.8f"),
            "note": st.column_config.TextColumn("Notitie"),
        },
        key="btc_editor",
    )
    if st.button("Bitcoin-transacties opslaan", type="primary"):
        try:
            clean_transactions = clean_bitcoin_transactions(edited)
        except ValueError as exc:
            st.error(str(exc))
        else:
            saved = save_synced_table(
                "bitcoin_transactions", clean_transactions, sync_version
            )
            if saved:
                set_settings({"bitcoin_current_price": current_price})
                st.success("Bitcoin-portefeuille opgeslagen.")
                st.rerun()


def pension_page() -> None:
    page_header(
        "Pensioenplanning",
        "AOW, pensioen en tijdelijk bijverdienen als basis voor je inkomen.",
    )
    with st.form("pension_form"):
        c1, c2 = st.columns(2)
        birth = c1.date_input(
            "Geboortedatum",
            value=date.fromisoformat(settings.get("birth_date", "1964-12-21")),
        )
        side = c2.number_input(
            "Netto bijverdienen p/m tot AOW",
            min_value=0.0,
            value=number("side_income_monthly", 1500),
            step=50.0,
        )
        own = c1.number_input(
            "Eigen pensioen netto p/m",
            min_value=0.0,
            value=number("own_pension_monthly", 145),
            step=10.0,
        )
        partner = c2.number_input(
            "Pensioen partner netto p/m",
            min_value=0.0,
            value=number("partner_pension_monthly", 350),
            step=10.0,
        )
        aow = st.number_input(
            "Gezamenlijke AOW netto p/m (aanname)",
            min_value=0.0,
            value=number("aow_combined_monthly", 2000),
            step=50.0,
        )
        d1, d2, d3 = st.columns(3)
        aow_date = d1.date_input(
            "Exacte AOW-datum",
            value=date.fromisoformat(settings.get("aow_start_date", "2032-03-21")),
        )
        own_pension_date = d2.date_input(
            "Start eigen pensioen",
            value=date.fromisoformat(settings.get("own_pension_start_date", "2032-03-21")),
        )
        partner_pension_date = d3.date_input(
            "Start partnerpensioen",
            value=date.fromisoformat(settings.get("partner_pension_start_date", "2032-03-21")),
        )
        submitted = st.form_submit_button("Pensioeninstellingen opslaan")
        if submitted:
            set_settings(
                {
                    "birth_date": birth.isoformat(),
                    "side_income_monthly": side,
                    "own_pension_monthly": own,
                    "partner_pension_monthly": partner,
                    "aow_combined_monthly": aow,
                    "aow_start_date": aow_date.isoformat(),
                    "own_pension_start_date": own_pension_date.isoformat(),
                    "partner_pension_start_date": partner_pension_date.isoformat(),
                }
            )
            st.success("Pensioeninstellingen opgeslagen.")
            st.rerun()

    plan = make_engine().evaluate()
    projection = plan.projection
    sources = projection[["year", "aow", "pension", "side_income"]].melt(
        "year", var_name="source", value_name="amount"
    )
    fig = px.bar(
        sources,
        x="year",
        y="amount",
        color="source",
        title="Vaste inkomstenbronnen per maand",
        labels={"year": "Jaar", "amount": "Netto per maand"},
        color_discrete_sequence=["#20c997", "#d5a64a", "#5b8def"],
    )
    st.plotly_chart(chart_layout(fig, dark_mode), use_container_width=True)


def annuity_page() -> None:
    page_header(
        "Lijfrenteplanning",
        "Bereken een direct ingaande lijfrente en zie de netto uitkering per jaar.",
    )
    with st.form("annuity_form"):
        c1, c2 = st.columns(2)
        principal = c1.number_input(
            "Startkapitaal",
            min_value=0.0,
            value=number("annuity_principal", 250000),
            step=5000.0,
        )
        years = c2.number_input(
            "Looptijd in jaren",
            min_value=1,
            max_value=40,
            value=integer("annuity_years", 15),
        )
        annual_return = c1.number_input(
            "Rekenrente per jaar (%)",
            min_value=0.0,
            max_value=15.0,
            value=number("annuity_return_pct", 2.5),
            step=.1,
        )
        tax = c2.number_input(
            "Indicatieve belasting (%)",
            min_value=0.0,
            max_value=60.0,
            value=number("annuity_tax_pct", 37),
            step=.5,
        )
        annuity_start = st.date_input(
            "Exacte ingangsdatum lijfrente",
            value=date.fromisoformat(settings.get("annuity_start_date", "2027-01-01")),
        )
        if st.form_submit_button("Lijfrente opslaan"):
            set_settings(
                {
                    "annuity_principal": principal,
                    "annuity_years": years,
                    "annuity_return_pct": annual_return,
                    "annuity_tax_pct": tax,
                    "annuity_start_date": annuity_start.isoformat(),
                }
            )
            st.success("Lijfrente-instellingen opgeslagen.")
            st.rerun()

    schedule = make_annuity()
    a, b, c = st.columns(3)
    a.metric("Kapitaal", money(number("annuity_principal")))
    b.metric("Netto eerste jaar", money(schedule.iloc[0]["net"]))
    c.metric("Netto per maand", money(schedule.iloc[0]["net_monthly"]))
    display = schedule.copy()
    display.columns = [
        "Jaar",
        "Beginstand",
        "Rente",
        "Bruto uitkering",
        "Netto uitkering",
        "Netto p/m",
        "Eindstand",
    ]
    st.dataframe(display, hide_index=True, use_container_width=True)


def income_page() -> None:
    page_header(
        f"Netto maandinkomen tot {integer('calculation_end_year', 2047)}",
        "Ieder jaar je geïndexeerde doel, inkomstenbronnen en benodigde ETF-opname.",
    )
    with st.form("income_form"):
        c1, c2, c3 = st.columns(3)
        target = c1.number_input(
            "Netto maanddoel",
            min_value=0.0,
            value=number("target_monthly", 4000),
            step=100.0,
        )
        inflation = c2.number_input(
            "Jaarlijkse indexatie (%)",
            min_value=0.0,
            max_value=15.0,
            value=number("inflation_pct", 2.5),
            step=.1,
        )
        etf_return = c3.number_input(
            "Verwacht ETF-rendement (%)",
            min_value=-20.0,
            max_value=20.0,
            value=number("etf_return_pct", 4),
            step=.1,
        )
        etf_start = st.number_input(
            "ETF-startvermogen",
            min_value=0.0,
            value=number("etf_start", 500000),
            step=10000.0,
        )
        if st.form_submit_button("Inkomensplan opslaan"):
            set_settings(
                {
                    "target_monthly": target,
                    "inflation_pct": inflation,
                    "etf_return_pct": etf_return,
                    "etf_start": etf_start,
                }
            )
            st.success("Inkomensplan opgeslagen.")
            st.rerun()

    plan = make_engine().evaluate()
    projection = plan.projection
    long = projection.melt(
        id_vars=["year"],
        value_vars=["annuity", "aow", "pension", "side_income", "etf_withdrawal"],
        var_name="source",
        value_name="amount",
    )
    fig = px.bar(
        long,
        x="year",
        y="amount",
        color="source",
        title="Opbouw netto maandinkomen",
        labels={"year": "Jaar", "amount": "Netto per maand"},
        color_discrete_sequence=["#20c997", "#d5a64a", "#5b8def", "#9b7ede", "#ff8c61"],
    )
    fig.add_scatter(
        x=projection["year"],
        y=projection["target"],
        mode="lines",
        name="Geïndexeerd doel",
        line=dict(color="#ff6b6b", width=3),
    )
    st.plotly_chart(chart_layout(fig, dark_mode, 450), use_container_width=True)

    display = projection.copy()
    display.columns = [
        "Jaar",
        "Doel p/m",
        "Lijfrente",
        "AOW",
        "Pensioen",
        "Bijverdienen",
        "ETF-opname p/m",
        "Beschikbaar p/m",
        "ETF eindstand",
    ]
    st.dataframe(display, hide_index=True, use_container_width=True)
    st.download_button(
        "Download als CSV",
        projection.to_csv(index=False).encode("utf-8"),
        "netto_maandinkomen_tot_2047.csv",
        "text/csv",
    )


def freedom_page() -> None:
    page_header(
        "Project Vrijheid",
        "Bereken wat verkoop van POTZ WONEN oplevert en neem het resultaat over in je financiële balans.",
    )

    scenario_col1, scenario_col2, scenario_col3 = st.columns(3)
    if scenario_col1.button("Voorzichtig · pand € 1.450.000", use_container_width=True):
        st.session_state["sale_property_price"] = 1450000.0
    if scenario_col2.button("Ondergrens · pand € 1.500.000", use_container_width=True):
        st.session_state["sale_property_price"] = 1500000.0
    if scenario_col3.button("Vraagprijs · pand € 1.595.000", use_container_width=True):
        st.session_state["sale_property_price"] = 1595000.0

    with st.form("freedom_form"):
        st.subheader("Verkoop")
        sale_structure = st.selectbox(
            "Fiscale structuur van de verkoop",
            ["Privé/eenmanszaak", "BV"],
            index=1 if settings.get("sale_structure") == "BV" else 0,
            help="Deze keuze bepaalt of GeertOS rekent met een indicatief inkomstenbelastingtarief of met Vpb en box 2.",
        )
        c1, c2, c3 = st.columns(3)
        property_price = c1.number_input(
            "Verkoopprijs pand",
            min_value=0.0,
            value=float(st.session_state.get("sale_property_price", number("sale_property_price", 1595000))),
            step=25000.0,
        )
        property_book = c2.number_input(
            "Boekwaarde pand + grond",
            min_value=0.0,
            value=number("sale_property_book", 885000),
            step=5000.0,
        )
        inventory_price = c3.number_input(
            "Verkoopprijs voorraad",
            min_value=0.0,
            value=number("sale_inventory_price", 275000),
            step=5000.0,
        )
        inventory_book = c1.number_input(
            "Boekwaarde voorraad",
            min_value=0.0,
            value=number("sale_inventory_book", 335000),
            step=5000.0,
        )
        brokerage = c2.number_input(
            "Courtage excl. btw (%)",
            min_value=0.0,
            value=number("sale_brokerage_pct", 1.75),
            step=0.05,
        )
        brokerage_vat = c3.number_input(
            "Btw over courtage (%)",
            min_value=0.0,
            value=number("sale_brokerage_vat_pct", 21),
            step=1.0,
        )

        st.subheader("Schulden en reserveringen")
        d1, d2, d3 = st.columns(3)
        mortgage = d1.number_input(
            "Hypotheek", min_value=0.0, value=number("sale_mortgage", 675000), step=5000.0
        )
        credit = d2.number_input(
            "Bedrijfskrediet", min_value=0.0, value=number("sale_business_credit", 100000), step=5000.0
        )
        other_loans = d3.number_input(
            "Overige leningen", min_value=0.0, value=number("sale_other_loans", 125000), step=5000.0
        )
        annuity_reserve = d1.number_input(
            "Stakingslijfrente", min_value=0.0, value=number("sale_annuity_reserve", 250000), step=5000.0
        )
        tax = d2.number_input(
            "Indicatief belastingtarief (%)",
            min_value=0.0,
            max_value=60.0,
            value=number("sale_tax_pct", 25.8),
            step=0.1,
        )
        other_costs = d3.number_input(
            "Overige verkoopkosten", min_value=0.0, value=number("sale_other_costs", 0), step=1000.0
        )
        st.subheader("Fiscale aannames")
        f1, f2, f3 = st.columns(3)
        vpb_low = f1.number_input(
            "Vpb laag (%)", min_value=0.0, max_value=60.0,
            value=number("sale_vpb_low_pct", 19), step=0.1,
            disabled=sale_structure != "BV",
        )
        vpb_high = f2.number_input(
            "Vpb hoog (%)", min_value=0.0, max_value=60.0,
            value=number("sale_vpb_high_pct", 25.8), step=0.1,
            disabled=sale_structure != "BV",
        )
        vpb_threshold = f3.number_input(
            "Vpb-schijfgrens", min_value=0.0,
            value=number("sale_vpb_threshold", 200000), step=5000.0,
            disabled=sale_structure != "BV",
        )
        f4, f5 = st.columns(2)
        box2 = f4.number_input(
            "Box 2 bij uitkering (%)", min_value=0.0, max_value=60.0,
            value=number("sale_box2_pct", 31), step=0.1,
            disabled=sale_structure != "BV",
        )
        retain_bv = f5.number_input(
            "Bedrag dat in BV blijft", min_value=0.0,
            value=number("sale_retain_in_bv", 0), step=5000.0,
            disabled=sale_structure != "BV",
        )
        submitted = st.form_submit_button("Berekening opslaan", type="primary")

    if submitted:
        set_settings(
            {
                "sale_property_price": property_price,
                "sale_property_book": property_book,
                "sale_inventory_price": inventory_price,
                "sale_inventory_book": inventory_book,
                "sale_mortgage": mortgage,
                "sale_business_credit": credit,
                "sale_other_loans": other_loans,
                "sale_brokerage_pct": brokerage,
                "sale_brokerage_vat_pct": brokerage_vat,
                "sale_other_costs": other_costs,
                "sale_tax_pct": tax,
                "sale_annuity_reserve": annuity_reserve,
                "sale_structure": sale_structure,
                "sale_vpb_low_pct": vpb_low,
                "sale_vpb_high_pct": vpb_high,
                "sale_vpb_threshold": vpb_threshold,
                "sale_box2_pct": box2,
                "sale_retain_in_bv": retain_bv,
            }
        )
        st.success("Project Vrijheid is opgeslagen.")

    engine = make_engine()
    sale_overrides = {
        "sale_property_price": property_price,
        "sale_property_book": property_book,
        "sale_inventory_price": inventory_price,
        "sale_inventory_book": inventory_book,
        "sale_mortgage": mortgage,
        "sale_business_credit": credit,
        "sale_other_loans": other_loans,
        "sale_brokerage_pct": brokerage,
        "sale_brokerage_vat_pct": brokerage_vat,
        "sale_other_costs": other_costs,
        "sale_tax_pct": tax,
        "sale_annuity_reserve": annuity_reserve,
        "sale_structure": sale_structure,
        "sale_vpb_low_pct": vpb_low,
        "sale_vpb_high_pct": vpb_high,
        "sale_vpb_threshold": vpb_threshold,
        "sale_box2_pct": box2,
        "sale_retain_in_bv": retain_bv,
    }
    result = engine.evaluate(sale_overrides).sale

    st.subheader("Uitkomst")
    a, b, c, d = st.columns(4)
    a.metric("Bruto verkoop", money(result["gross"]))
    b.metric("Totale schulden", money(result["total_debt"]))
    c.metric("Belasting indicatief", money(result["tax"]))
    d.metric("Netto cash", money(result["net_cash"]))

    a2, b2, c2, d2 = st.columns(4)
    a2.metric("Courtage incl. btw", money(result["brokerage"]))
    b2.metric("Belastbare winst", money(result["taxable_profit"]))
    c2.metric("Lijfrente", money(result["annuity_reserve"]))
    d2.metric("Totaal na verkoop", money(result["total_after_sale"]))

    fiscal = pd.DataFrame(
        [
            ("Boekwinst pand", result["property_book_profit"]),
            ("Boekwinst voorraad", result["inventory_book_profit"]),
            ("Verkoopkosten", -result["total_sale_costs"]),
            ("Winst vóór lijfrente", result["book_profit"]),
            ("Lijfrenteaftrek/reservering", -result["annuity_reserve"]),
            ("Belastbare winst", result["taxable_profit"]),
            ("Inkomstenbelasting indicatief", -result["income_tax"]),
            ("Vennootschapsbelasting indicatief", -result["corporate_tax"]),
            ("Box 2 indicatief", -result["box2_tax"]),
            ("Netto privé", result["net_cash"]),
            ("Blijft in BV", result["retained_bv"]),
        ],
        columns=["Onderdeel", "Bedrag"],
    )
    st.subheader("Fiscale uitsplitsing")
    st.dataframe(fiscal, hide_index=True, use_container_width=True)

    cash_goal = number("sale_net_cash_goal", 600000)
    if result["net_cash"] < cash_goal:
        st.warning(
            f"De netto cash ligt {money(cash_goal - result['net_cash'])} onder je doel van {money(cash_goal)}."
        )
    else:
        st.success(
            f"De netto cash ligt {money(result['net_cash'] - cash_goal)} boven je doel van {money(cash_goal)}."
        )

    if st.button("Neem dit resultaat over in Netto vermogen", use_container_width=True):
        replace_balance_with_freedom_plan(
            max(0.0, result["net_cash"]),
            result["annuity_reserve"],
        )
        set_settings(
            {
                "etf_start": max(0.0, result["net_cash"] - number("safety_buffer", 100000)),
                "annuity_principal": result["annuity_reserve"],
            }
        )
        st.success("De balans en financiële planning zijn bijgewerkt.")

    st.subheader("Verkoopprijs pand vergelijken")
    scenarios = []
    for price in range(1300000, 1700001, 25000):
        item = engine.sale_result(
            {**sale_overrides, "sale_property_price": price}
        )
        scenarios.append({"Verkoopprijs pand": price, "Netto cash": item["net_cash"]})
    scenario_frame = pd.DataFrame(scenarios)
    fig = px.line(
        scenario_frame,
        x="Verkoopprijs pand",
        y="Netto cash",
        markers=True,
        color_discrete_sequence=["#20c997"],
    )
    fig.add_hline(
        y=cash_goal, line_dash="dash", line_color="#d5a64a",
        annotation_text=f"Doel {money(cash_goal)} netto cash",
    )
    st.plotly_chart(chart_layout(fig, dark_mode), use_container_width=True)
    st.caption(
        "Dit is een indicatief planningsmodel. Laat de fiscale uitkomst altijd controleren door je accountant of fiscalist."
    )


def expenses_page() -> None:
    page_header(
        "Uitgavenplanner",
        "Breng vaste lasten én ruimte om te genieten samen in één maandbudget.",
    )
    sync_version = get_sync_version("expenses")
    frame = read_table("expenses")
    total = float(frame["monthly_amount"].sum())
    target = number("target_monthly", 4000)
    a, b, c = st.columns(3)
    a.metric("Uitgaven p/m", money(total))
    b.metric("Jaarbudget", money(total * 12))
    c.metric("Ruimte binnen doel", money(target - total))

    edited = st.data_editor(
        frame.drop(columns=["id"]),
        num_rows="dynamic",
        hide_index=True,
        use_container_width=True,
        column_config={
            "category": st.column_config.TextColumn("Categorie", required=True),
            "description": st.column_config.TextColumn("Omschrijving", required=True),
            "monthly_amount": st.column_config.NumberColumn(
                "Per maand", min_value=0.0, format="€ %.2f", required=True
            ),
        },
        key="expense_editor",
    )
    if st.button("Uitgaven opslaan", type="primary"):
        if save_synced_table("expenses", edited, sync_version):
            st.success("Uitgaven opgeslagen.")
            st.rerun()

    if not frame.empty and total:
        fig = px.treemap(
            frame,
            path=["category", "description"],
            values="monthly_amount",
            color="monthly_amount",
            color_continuous_scale=["#14213d", "#20c997"],
            title="Verdeling maandbudget",
        )
        st.plotly_chart(chart_layout(fig, dark_mode, 430), use_container_width=True)



def freedom_timeline_page() -> None:
    page_header(
        "Tijdlijn financiële vrijheid",
        "Bekijk per jaar hoe inkomen, pensioen, AOW en ETF-vermogen zich ontwikkelen.",
    )
    result = make_engine().evaluate()
    projection = result.projection.copy()
    projection["tekort"] = (projection["target"] - projection["actual"]).clip(lower=0)
    projection["overschot"] = (projection["actual"] - projection["target"]).clip(lower=0)

    wealth_fig = go.Figure()
    wealth_fig.add_trace(
        go.Scatter(
            x=projection["year"],
            y=projection["etf_closing"],
            mode="lines+markers",
            name="ETF-restvermogen",
            line=dict(color="#20c997", width=3),
        )
    )
    wealth_fig.update_layout(
        title="Verwachte ontwikkeling ETF-vermogen",
        xaxis_title="Jaar",
        yaxis_title="Vermogen",
        hovermode="x unified",
    )
    st.plotly_chart(chart_layout(wealth_fig, dark_mode), use_container_width=True)

    income_fig = go.Figure()
    for column, label, color in [
        ("target", "Gewenst netto inkomen", "#d5a64a"),
        ("actual", "Berekend netto inkomen", "#5b8def"),
    ]:
        income_fig.add_trace(
            go.Scatter(
                x=projection["year"],
                y=projection[column],
                mode="lines",
                name=label,
                line=dict(color=color, width=3),
            )
        )
    income_fig.update_layout(
        title="Netto maandinkomen tegenover doel",
        xaxis_title="Jaar",
        yaxis_title="Per maand",
        hovermode="x unified",
    )
    st.plotly_chart(chart_layout(income_fig, dark_mode), use_container_width=True)

    years = projection["year"].astype(int).tolist()
    selected_year = st.slider(
        "Kies een jaar",
        min_value=min(years),
        max_value=max(years),
        value=min(years),
        step=1,
    )
    row = projection.loc[projection["year"].astype(int) == selected_year].iloc[0]
    st.subheader(f"Details {selected_year}")
    a, b, c, d = st.columns(4)
    a.metric("Netto maandinkomen", money(float(row["actual"])))
    b.metric("Gewenst maandinkomen", money(float(row["target"])))
    c.metric("ETF-restvermogen", money(float(row["etf_closing"])))
    d.metric("ETF-opname per maand", money(float(row["etf_withdrawal"])))

    a, b, c, d = st.columns(4)
    a.metric("Pensioen", money(float(row["pension"])))
    b.metric("Lijfrente", money(float(row["annuity"])))
    c.metric("AOW", money(float(row["aow"])))
    if float(row["tekort"]) > 0:
        d.metric("Tekort", money(float(row["tekort"])), "aandacht nodig")
    else:
        d.metric("Overschot", money(float(row["overschot"])), "per maand")

    st.info(
        f"Bitcoin: {money(result.bitcoin_value)} huidige waarde. "
        "GeertOS projecteert Bitcoin bewust niet naar toekomstige jaren, "
        "omdat daarvoor geen betrouwbare groeiaanname is vastgelegd."
    )
    st.caption(
        "Alle waarden komen rechtstreeks uit de centrale GeertOS-rekenmotor. "
        "Een keuze op deze pagina wijzigt geen opgeslagen gegevens."
    )


def scenario_analysis_page() -> None:
    page_header(
        "Scenariovergelijker",
        "Vergelijk voorzichtig, verwacht en optimistisch op dezelfde financiële uitgangspunten.",
    )
    frame = compare_scenarios(make_engine(), settings)

    cards = st.columns(3)
    for index, row in frame.iterrows():
        cards[index].metric(
            str(row["Scenario"]),
            money(float(row["Netto vermogen na verkoop"])),
            f"Risico: {row['Risico']}",
        )

    fig = px.bar(
        frame,
        x="Scenario",
        y="ETF-restvermogen 2047",
        color="Scenario",
        title="Verwacht ETF-restvermogen in 2047",
        color_discrete_sequence=["#ff8c61", "#20c997", "#5b8def"],
    )
    st.plotly_chart(chart_layout(fig, dark_mode), use_container_width=True)

    display = frame.copy()
    for column in [
        "Verkoopprijs pand",
        "Netto cash",
        "Netto vermogen na verkoop",
        "ETF-restvermogen 2047",
        "ETF-opname eerste jaar",
        "Bitcoin-waarde",
        "Netto inkomen eerste jaar",
    ]:
        display[column] = display[column].map(money)
    display["ETF-rendement"] = display["ETF-rendement"].map(lambda value: f"{value:.1f}%")
    display["Inflatie"] = display["Inflatie"].map(lambda value: f"{value:.1f}%")
    display["Vrijheidsstatus"] = display["Vrijheidsstatus"].map(lambda value: f"{value}%")
    st.dataframe(display, hide_index=True, use_container_width=True)
    with st.expander("Welke aannames verschillen?"):
        st.write(
            "Voorzichtig rekent met een lagere verkoopprijs, twee procentpunt "
            "lager ETF-rendement, één procentpunt hogere inflatie en 20% lagere "
            "Bitcoinwaarde. Optimistisch doet het omgekeerde met begrensde, "
            "zichtbare afwijkingen. Verwacht gebruikt je opgeslagen planning."
        )
    st.caption(
        "Scenario's zijn tijdelijke berekeningen. Ze worden niet opgeslagen en "
        "wijzigen jouw persoonlijke financiële waarheid niet."
    )


def advisor_page() -> None:
    page_header(
        "GeertOS AI-assistent",
        "Stel financiële vragen in gewone taal en krijg een controleerbare berekening.",
    )
    st.info(
        "Veilige analysemodus: de assistent kan alleen lezen en rekenen. "
        "Hij kan nooit zelfstandig gegevens, instellingen of transacties wijzigen."
    )

    examples = [
        "Wat gebeurt er als het pand € 1.575.000 oplevert?",
        "Kan ik € 500 per maand extra besteden?",
        "Wat gebeurt er als Bitcoin 20% daalt?",
        "Kan ik veilig € 80.000 aan een camper besteden?",
        "Wanneer ben ik financieel onafhankelijk?",
    ]
    st.write("**Voorbeeldvragen**")
    columns = st.columns(2)
    for index, example in enumerate(examples):
        columns[index % 2].button(
            example,
            key=f"advisor_example_{index}",
            use_container_width=True,
            on_click=lambda value=example: st.session_state.update(
                advisor_question=value
            ),
        )

    question = st.text_area(
        "Jouw vraag",
        key="advisor_question",
        placeholder="Bijvoorbeeld: Kan ik € 500 per maand extra besteden?",
        height=100,
    )
    if st.button("Analyseer mijn vraag", type="primary", use_container_width=True):
        if not question.strip():
            st.warning("Vul eerst een vraag in.")
        else:
            answer = answer_question(question, make_engine(), settings)
            getattr(st, answer.level)(f"**{answer.title}**\n\n{answer.message}")
            for detail in answer.details:
                st.write(f"• {detail}")
            st.button(
                f"Bekijk {answer.destination}",
                key="advisor_destination",
                on_click=navigate_to,
                args=(answer.destination,),
            )

    st.divider()
    st.caption(
        "Deze versie gebruikt geen externe of betaalde AI-dienst. Antwoorden "
        "komen uit vaste, testbare regels en de centrale GeertOS-rekenmotor. "
        "Bedragen blijven binnen GeertOS."
    )


def personal_truth_page() -> None:
    page_header(
        "Persoonlijke financiële waarheid",
        "Eén controlepunt voor werkelijke cijfers, bevestigde aannames en verschillen met de planning.",
    )
    st.info(
        "Werkelijke saldi komen uit de balans, ETF-, Bitcoin- en uitgaventabellen. "
        "Toekomstige rendementen en fiscale percentages blijven aannames en zijn daarom apart herkenbaar."
    )

    core = [
        ("Verkoopprijs pand", "sale_property_price", "Werkelijk / offerte"),
        ("Boekwaarde pand + grond", "sale_property_book", "Werkelijk / administratie"),
        ("Verkoopprijs voorraad", "sale_inventory_price", "Werkelijk / offerte"),
        ("Boekwaarde voorraad", "sale_inventory_book", "Werkelijk / administratie"),
        ("Hypotheek", "sale_mortgage", "Werkelijk / bank"),
        ("Bedrijfskrediet", "sale_business_credit", "Werkelijk / bank"),
        ("Overige leningen", "sale_other_loans", "Werkelijk / bank"),
        ("Doel netto per maand", "target_monthly", "Persoonlijk plan"),
        ("ETF-rendement per jaar", "etf_return_pct", "Aanname"),
        ("Inflatie per jaar", "inflation_pct", "Aanname"),
        ("Belastingtarief indicatief", "sale_tax_pct", "Aanname fiscalist"),
        ("Vpb laag", "sale_vpb_low_pct", "Aanname fiscalist"),
        ("Vpb hoog", "sale_vpb_high_pct", "Aanname fiscalist"),
        ("Box 2", "sale_box2_pct", "Aanname fiscalist"),
        ("AOW netto per maand", "aow_combined_monthly", "Aanname / beschikking"),
        ("Eigen pensioen per maand", "own_pension_monthly", "Werkelijk / UPO"),
        ("Partnerpensioen per maand", "partner_pension_monthly", "Werkelijk / UPO"),
    ]
    assumption_rows = []
    for label, key, source in core:
        assumption_rows.append(
            {
                "Onderdeel": label,
                "Waarde": number(key),
                "Bron/status": source,
                "Nog laten controleren": "Ja" if "Aanname" in source else "Nee",
            }
        )
    st.subheader("Controle van bedragen en aannames")
    st.dataframe(pd.DataFrame(assumption_rows), hide_index=True, use_container_width=True)

    date_rows = pd.DataFrame(
        [
            ("Geboortedatum", settings.get("birth_date", "")),
            ("AOW vanaf", settings.get("aow_start_date", "")),
            ("Eigen pensioen vanaf", settings.get("own_pension_start_date", "")),
            ("Partnerpensioen vanaf", settings.get("partner_pension_start_date", "")),
            ("Lijfrente vanaf", settings.get("annuity_start_date", "")),
        ],
        columns=["Gebeurtenis", "Exacte datum"],
    )
    st.subheader("Exacte ingangsdatums")
    st.dataframe(date_rows, hide_index=True, use_container_width=True)

    balance = read_table("balance_items")
    private = balance.loc[balance["owner_scope"] == "Privé"]
    bv = balance.loc[balance["owner_scope"] == "BV"]
    private_net = float(
        private.loc[private["item_type"] == "asset", "amount"].sum()
        - private.loc[private["item_type"] == "liability", "amount"].sum()
    )
    bv_net = float(
        bv.loc[bv["item_type"] == "asset", "amount"].sum()
        - bv.loc[bv["item_type"] == "liability", "amount"].sum()
    )
    c1, c2, c3 = st.columns(3)
    c1.metric("Netto privé", money(private_net))
    c2.metric("Netto BV", money(bv_net))
    c3.metric("Gecombineerd", money(private_net + bv_net))

    st.subheader("Werkelijkheid tegenover planning")
    sync_version = get_sync_version("plan_actuals")
    actuals = read_table("plan_actuals")
    editable = actuals.drop(columns=["id"])
    if editable.empty:
        editable = pd.DataFrame(
            [
                {
                    "period": date.today().strftime("%Y-%m"),
                    "metric": "Netto uitgaven",
                    "planned_amount": number("target_monthly", 4000),
                    "actual_amount": 0.0,
                    "notes": "",
                }
            ]
        )
    edited = st.data_editor(
        editable,
        num_rows="dynamic",
        hide_index=True,
        use_container_width=True,
        column_config={
            "period": st.column_config.TextColumn("Maand (JJJJ-MM)", required=True),
            "metric": st.column_config.TextColumn("Meetpunt", required=True),
            "planned_amount": st.column_config.NumberColumn("Planning", format="€ %.2f"),
            "actual_amount": st.column_config.NumberColumn("Werkelijk", format="€ %.2f"),
            "notes": st.column_config.TextColumn("Toelichting"),
        },
        key="plan_actuals_editor",
    )
    if st.button("Planning en werkelijkheid opslaan", type="primary"):
        if save_synced_table("plan_actuals", edited, sync_version):
            st.success("Vergelijking opgeslagen.")
            st.rerun()

    if not actuals.empty:
        comparison = actuals.copy()
        comparison["difference"] = comparison["actual_amount"] - comparison["planned_amount"]
        st.dataframe(
            comparison[["period", "metric", "planned_amount", "actual_amount", "difference"]],
            hide_index=True,
            use_container_width=True,
        )
        chart_data = comparison.melt(
            id_vars=["period", "metric"],
            value_vars=["planned_amount", "actual_amount"],
            var_name="Soort",
            value_name="Bedrag",
        )
        fig = px.bar(
            chart_data,
            x="period",
            y="Bedrag",
            color="Soort",
            barmode="group",
            facet_row="metric" if comparison["metric"].nunique() > 1 else None,
            title="Planning tegenover werkelijkheid",
        )
        st.plotly_chart(chart_layout(fig, dark_mode), use_container_width=True)

    confirmed = settings.get("truth_last_confirmed", "")
    if confirmed:
        st.success(f"Laatste integrale controle: {confirmed}")
    else:
        st.warning("De volledige set uitgangspunten is nog niet integraal bevestigd.")
    if st.button("Markeer alle huidige waarden als vandaag gecontroleerd"):
        set_settings({"truth_last_confirmed": date.today().isoformat()})
        st.success("Controledatum vastgelegd.")
        st.rerun()

    st.caption(
        "Fiscale percentages zijn planningsaannames. Laat verkoopstructuur, "
        "stakingslijfrente, Vpb en box 2 vóór een besluit schriftelijk bevestigen door accountant of fiscalist."
    )


def settings_page() -> None:
    page_header(
        "Mijn uitgangspunten",
        "Beheer de vaste aannames die in alle berekeningen van GeertOS worden gebruikt.",
    )
    with st.form("central_settings_form"):
        c1, c2, c3 = st.columns(3)
        target = c1.number_input("Gewenst netto maandinkomen", min_value=0.0, value=number("target_monthly", 4000), step=100.0)
        inflation = c2.number_input("Inflatie per jaar (%)", min_value=0.0, max_value=15.0, value=number("inflation_pct", 2.5), step=0.1)
        end_year = c3.number_input("Doorrekenen tot", min_value=date.today().year, max_value=2125, value=integer("calculation_end_year", 2047), step=1)
        etf_start = c1.number_input("ETF-startvermogen", min_value=0.0, value=number("etf_start", 500000), step=10000.0)
        etf_return = c2.number_input("ETF-rendement per jaar (%)", min_value=-20.0, max_value=20.0, value=number("etf_return_pct", 4.0), step=0.1)
        buffer = c3.number_input("Veiligheidsbuffer", min_value=0.0, value=number("safety_buffer", 100000), step=5000.0)
        cash_goal = c1.number_input("Doel netto cash na verkoop", min_value=0.0, value=number("sale_net_cash_goal", 600000), step=10000.0)
        annuity = c2.number_input("Doel stakingslijfrente", min_value=0.0, value=number("sale_annuity_reserve", 250000), step=5000.0)
        side_income = c3.number_input("Netto bijverdienen p/m tot AOW", min_value=0.0, value=number("side_income_monthly", 1500), step=50.0)
        submitted = st.form_submit_button("Uitgangspunten opslaan", type="primary")
    if submitted:
        set_settings({
            "target_monthly": target,
            "inflation_pct": inflation,
            "calculation_end_year": int(end_year),
            "etf_start": etf_start,
            "etf_return_pct": etf_return,
            "safety_buffer": buffer,
            "sale_net_cash_goal": cash_goal,
            "sale_annuity_reserve": annuity,
            "annuity_principal": annuity,
            "side_income_monthly": side_income,
        })
        st.success("Uitgangspunten opgeslagen.")
        st.rerun()

    st.divider()
    st.subheader("Back-up en herstel")
    st.caption(
        "Maak een volledige, gecontroleerde export van alle cloudgegevens. "
        "Bewaar het ZIP-bestand op je eigen computer of in je persoonlijke cloudmap."
    )
    if st.button("Maak gecontroleerde back-up", use_container_width=True):
        try:
            backup = create_backup()
            manifest = validate_backup(backup)
            st.session_state["verified_backup_name"] = backup.name
            st.session_state["verified_backup_data"] = backup.read_bytes()
            st.session_state["verified_backup_tables"] = len(manifest["tables"])
        except Exception:
            st.error(
                "De back-up kon niet veilig worden afgerond. "
                "Er zijn geen gegevens gewijzigd."
            )
        else:
            st.success(
                f"Back-up gecontroleerd: {len(manifest['tables'])} tabellen zijn compleet."
            )

    if st.session_state.get("verified_backup_data"):
        st.download_button(
            "Download laatste gecontroleerde back-up",
            data=st.session_state["verified_backup_data"],
            file_name=st.session_state["verified_backup_name"],
            mime="application/zip",
            use_container_width=True,
        )



def plan_check_page() -> None:
    page_header(
        "Plancontrole",
        "Toets je inkomensplan op haalbaarheid en vergelijk meerdere rendementsscenario’s.",
    )
    engine = make_engine()
    plan = engine.evaluate()
    projection = plan.projection
    health = plan.projection_health

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Plan volledig gedekt", "Ja" if health["funded"] else "Nee")
    c2.metric("ETF-restvermogen", money(float(health["end_balance"])))
    c3.metric("Totale ETF-opnames", money(float(health["total_withdrawals"])))
    c4.metric("Laagste dekking", f"{float(health['minimum_coverage_pct']):.1f}%")

    if health["funded"]:
        st.success(
            f"Met de huidige uitgangspunten wordt het maanddoel ieder jaar gehaald tot "
            f"{integer('calculation_end_year', 2047)}."
        )
    else:
        st.error(
            f"De eerste verwachte tekortperiode ontstaat in "
            f"{int(health['first_shortfall_year'])}."
        )

    stress = engine.stress_table((2.0, 4.0, 6.0))
    stress["Scenario"] = stress["return_pct"].map(
        {2.0: "Voorzichtig", 4.0: "Verwacht", 6.0: "Gunstig"}
    )
    stress["Status"] = stress["funded"].map({True: "Op koers", False: "Tekort"})

    fig = px.bar(
        stress,
        x="Scenario",
        y="end_balance",
        color="Status",
        title="ETF-restvermogen per rendementsscenario",
        labels={"end_balance": "Restvermogen", "Scenario": "Scenario"},
        color_discrete_map={"Op koers": "#20c997", "Tekort": "#ff6b6b"},
    )
    st.plotly_chart(chart_layout(fig, dark_mode), use_container_width=True)

    display = stress[[
        "Scenario", "return_pct", "Status", "first_shortfall_year",
        "end_balance", "total_withdrawals", "minimum_coverage_pct"
    ]].copy()
    display.columns = [
        "Scenario", "Rendement %", "Status", "Eerste tekortjaar",
        "ETF eindstand", "Totale ETF-opnames", "Laagste dekking %"
    ]
    display["Eerste tekortjaar"] = display["Eerste tekortjaar"].replace(0, "–")
    st.dataframe(display, hide_index=True, use_container_width=True)

    st.subheader("Jaarlijkse signalering")
    warning_table = projection[["year", "target", "actual", "etf_closing"]].copy()
    warning_table["coverage_pct"] = (warning_table["actual"] / warning_table["target"] * 100).round(1)
    warning_table["status"] = warning_table.apply(
        lambda row: "Goed" if row["coverage_pct"] >= 100 else "Aandacht", axis=1
    )
    warning_table.columns = [
        "Jaar", "Doel p/m", "Beschikbaar p/m", "ETF eindstand", "Dekking %", "Status"
    ]
    st.dataframe(warning_table, hide_index=True, use_container_width=True)

    st.divider()
    if st.button("Maak nu een databaseback-up", use_container_width=True):
        backup = create_backup()
        st.success(f"Back-up gemaakt: {backup.name}")



def decision_lab_page() -> None:
    page_header(
        "Beslislab",
        "Test een grote aankoop of extra maandelijkse uitgave met duizenden mogelijke beursverlopen.",
    )

    with st.form("decision_lab_form"):
        c1, c2, c3 = st.columns(3)
        purchase = c1.number_input(
            "Eenmalige uitgave",
            min_value=0.0,
            value=0.0,
            step=5000.0,
            help="Bijvoorbeeld een camper, verbouwing of grote reis.",
        )
        extra_monthly = c2.number_input(
            "Extra netto besteden per maand",
            min_value=0.0,
            value=0.0,
            step=100.0,
        )
        simulations = c3.number_input(
            "Aantal simulaties",
            min_value=500,
            max_value=10000,
            value=2000,
            step=500,
        )
        c4, c5 = st.columns(2)
        expected_return = c4.number_input(
            "Gemiddeld ETF-rendement (%)",
            min_value=-5.0,
            max_value=15.0,
            value=number("etf_return_pct", 4.0),
            step=0.1,
        )
        volatility = c5.number_input(
            "Jaarlijkse beweeglijkheid (%)",
            min_value=0.0,
            max_value=40.0,
            value=12.0,
            step=0.5,
            help="12% is een gangbare planningsaanname voor een gemengde portefeuille.",
        )
        run = st.form_submit_button("Bereken beslissing", type="primary")

    plan = make_engine().evaluate()
    projection = plan.projection
    summary, path = monte_carlo_income_plan(
        projection,
        starting_capital=plan.planned_etf_start,
        expected_return_pct=expected_return,
        volatility_pct=volatility,
        simulations=int(simulations),
        one_time_cost=purchase,
        extra_monthly_spending=extra_monthly,
        inflation_pct=number("inflation_pct", 2.5),
    )
    label, explanation = decision_label(float(summary["success_probability"]))

    a, b, c, d = st.columns(4)
    a.metric("Kans op volledige dekking", f"{float(summary['success_probability']):.1f}%")
    b.metric("Beoordeling", label)
    c.metric("Mediaan eindvermogen", money(float(summary["median_end_balance"])))
    d.metric("Slecht 10%-scenario", money(float(summary["p10_end_balance"])))

    if label in {"Sterk", "Haalbaar"}:
        st.success(explanation)
    elif label == "Aandacht":
        st.warning(explanation)
    else:
        st.error(explanation)

    if purchase or extra_monthly:
        annual_extra = extra_monthly * 12
        st.caption(
            f"Doorgerekend met {money(purchase)} eenmalig en {money(annual_extra)} extra per jaar, "
            f"geïndexeerd met {number('inflation_pct', 2.5):.1f}%."
        )

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=path["year"], y=path["p90"], mode="lines", name="Gunstig 90%",
        line=dict(width=1),
    ))
    fig.add_trace(go.Scatter(
        x=path["year"], y=path["p10"], mode="lines", name="Voorzichtig 10%",
        fill="tonexty", line=dict(width=1),
    ))
    fig.add_trace(go.Scatter(
        x=path["year"], y=path["median"], mode="lines", name="Mediaan",
        line=dict(width=3),
    ))
    fig.update_layout(
        title="Bandbreedte verwacht ETF-vermogen",
        xaxis_title="Jaar",
        yaxis_title="Vermogen",
    )
    st.plotly_chart(chart_layout(fig, dark_mode, 450), use_container_width=True)

    display = path.copy()
    display.columns = ["Jaar", "Voorzichtig 10%", "Mediaan", "Gunstig 90%"]
    st.dataframe(display, hide_index=True, use_container_width=True)
    st.caption(
        "Dit is een probabilistisch planningsmodel en geen garantie of persoonlijk beleggingsadvies."
    )

def family_page() -> None:
    page_header("Familie", "De mensen die centraal staan in jouw GeertOS.")
    sync_version = get_sync_version("family_members")
    frame = read_table("family_members")
    if frame.empty:
        st.info("Er staan nog geen familieleden in GeertOS.")
        return

    partner = frame[frame["relationship"] == "Partner"]
    children = frame[frame["relationship"].isin(["Kind", "Bonusdochter"])]
    grandchildren = frame[frame["relationship"] == "Kleinkind"]

    a, b, c = st.columns(3)
    a.metric("Partner", len(partner))
    b.metric("Kinderen", len(children), "3 kinderen + 2 bonusdochters")
    c.metric("Kleinkinderen", len(grandchildren))

    groups = [
        ("❤️ Samen", partner),
        ("👨‍👩‍👧‍👦 Kinderen en bonusdochters", children),
        ("👶 Kleinkinderen", grandchildren),
    ]
    for title, group in groups:
        st.subheader(title)
        cols = st.columns(3)
        for index, (_, person) in enumerate(group.iterrows()):
            birth = parse_date(person["birth_date"])
            age_text = f"{age_on(birth)} jaar" if birth else "Geboortedatum nog invullen"
            card = (
                '<div class="pv-family-card">'
                f'<div class="pv-avatar">{person["name"][0]}</div>'
                f'<div><strong>{person["name"]}</strong><br>'
                f'<span>{person["relationship"]} · {age_text}</span></div></div>'
            )
            with cols[index % 3]:
                st.markdown(card, unsafe_allow_html=True)

    st.divider()
    st.subheader("Familiegegevens bijwerken")
    edited = st.data_editor(
        frame.drop(columns=["id"]),
        num_rows="dynamic",
        hide_index=True,
        use_container_width=True,
        column_config={
            "name": st.column_config.TextColumn("Naam", required=True),
            "relationship": st.column_config.SelectboxColumn(
                "Relatie", options=["Partner", "Kind", "Bonusdochter", "Kleinkind"], required=True
            ),
            "birth_date": st.column_config.TextColumn("Geboortedatum (jjjj-mm-dd)"),
            "notes": st.column_config.TextColumn("Notitie"),
        },
        key="family_editor",
    )
    if st.button("Familiegegevens opslaan", type="primary"):
        if save_synced_table("family_members", edited, sync_version):
            st.success("Familiegegevens opgeslagen.")
            st.rerun()


def opa_fund_page() -> None:
    page_header("Opa-fonds", "Voor ieder kleinkind werken naar € 25.000 op de achttiende verjaardag.")
    summary = opa_summary()
    funds_sync_version = get_sync_version("opa_funds")
    funds = read_table("opa_funds")
    transactions = read_table("opa_transactions")

    total = float(summary["current"].sum()) if not summary.empty else 0.0
    target = float(summary["target"].sum()) if not summary.empty else 75000.0
    monthly = float(summary["monthly_needed"].sum()) if not summary.empty else 0.0
    a, b, c = st.columns(3)
    a.metric("Totaal gespaard", money(total))
    b.metric("Gezamenlijk doel", money(target))
    c.metric("Benodigde maandinleg", money(monthly))
    st.progress(min(total / target, 1.0) if target else 0, text=f"{(total/target*100 if target else 0):.1f}% van het gezamenlijke doel")

    if not summary.empty:
        cols = st.columns(3)
        for index, (_, child) in enumerate(summary.iterrows()):
            birth = parse_date(child["birth_date"])
            eighteenth = birth.replace(year=birth.year + 18) if birth else None
            with cols[index % 3]:
                st.markdown(f"### 👶 {child['child_name']}")
                st.metric("Huidige waarde", money(child["current"]))
                st.progress(min(child["progress"] / 100, 1.0), text=f"{child['progress']:.1f}% van {money(child['target'])}")
                st.metric("Nog nodig", money(child["remaining"]))
                st.metric("Maandelijks nodig", money(child["monthly_needed"]))
                if eighteenth:
                    st.caption(f"18 jaar op {eighteenth.strftime('%d-%m-%Y')} · gerekend met {child['return_pct']:.1f}% rendement")

    st.divider()
    left, right = st.columns([1, 1.4])
    with left:
        st.subheader("➕ Nieuwe storting")
        names = summary["child_name"].tolist() if not summary.empty else ["Aydin", "Sade", "Isabel"]
        with st.form("deposit_form", clear_on_submit=True):
            child_name = st.selectbox("Voor wie?", names)
            amount = st.number_input("Bedrag", min_value=0.0, step=25.0, value=100.0)
            transaction_date = st.date_input("Datum", value=date.today())
            note = st.text_input("Notitie", placeholder="Bijvoorbeeld: maandelijkse inleg")
            submitted = st.form_submit_button("Storting opslaan", type="primary")
        if submitted:
            try:
                add_opa_transaction(child_name, transaction_date.isoformat(), amount, note)
                st.success(f"{money(amount)} voor {child_name} is opgeslagen.")
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))

    with right:
        st.subheader("Ontwikkeling per kleinkind")
        chart = summary[["child_name", "current", "remaining"]].copy() if not summary.empty else pd.DataFrame()
        if not chart.empty:
            chart = chart.rename(columns={"child_name": "Kleinkind", "current": "Gespaard", "remaining": "Nog nodig"})
            fig = px.bar(chart, x="Kleinkind", y=["Gespaard", "Nog nodig"], barmode="stack", title="Stand richting € 25.000")
            st.plotly_chart(chart_layout(fig, dark_mode), use_container_width=True)
        else:
            st.info("Nog geen gegevens beschikbaar.")

    st.divider()
    st.subheader("Instellingen per kleinkind")
    edited_funds = st.data_editor(
        funds.drop(columns=["id"]),
        hide_index=True,
        use_container_width=True,
        column_config={
            "child_name": st.column_config.TextColumn("Kleinkind", disabled=True),
            "birth_date": st.column_config.TextColumn("Geboortedatum"),
            "target_amount": st.column_config.NumberColumn("Doelbedrag", format="€ %.2f", min_value=0.0),
            "expected_return_pct": st.column_config.NumberColumn("Verwacht rendement (%)", min_value=0.0, max_value=15.0),
        },
        key="opa_funds_editor",
    )
    if st.button("Opa-fonds instellingen opslaan"):
        if save_synced_table("opa_funds", edited_funds, funds_sync_version):
            st.success("Instellingen opgeslagen.")
            st.rerun()

    st.subheader("Stortingsgeschiedenis")
    if transactions.empty:
        st.caption("Nog geen stortingen geregistreerd.")
    else:
        display = transactions.drop(columns=["id"]).sort_values("transaction_date", ascending=False).copy()
        display.columns = ["Kleinkind", "Datum", "Bedrag", "Notitie"]
        st.dataframe(display, hide_index=True, use_container_width=True)


def charts_page() -> None:
    page_header(
        "Grafieken",
        "De belangrijkste financiële ontwikkelingen visueel naast elkaar.",
    )
    projection = make_projection()
    balance = read_table("balance_items")
    expenses = read_table("expenses")
    etf = read_table("etf_positions")

    c1, c2 = st.columns(2)
    with c1:
        fig = px.line(
            projection,
            x="year",
            y=["target", "actual"],
            title="Maanddoel en beschikbaar inkomen",
            labels={"year": "Jaar", "value": "Netto per maand"},
            color_discrete_map={"target": "#d5a64a", "actual": "#20c997"},
        )
        st.plotly_chart(chart_layout(fig, dark_mode), use_container_width=True)
    with c2:
        fig = px.area(
            projection,
            x="year",
            y="etf_closing",
            title="Ontwikkeling ETF-restvermogen",
            labels={"year": "Jaar", "etf_closing": "Vermogen"},
            color_discrete_sequence=["#5b8def"],
        )
        st.plotly_chart(chart_layout(fig, dark_mode), use_container_width=True)
    c3, c4 = st.columns(2)
    with c3:
        if not balance.empty:
            fig = px.bar(
                balance,
                x="name",
                y="amount",
                color="item_type",
                title="Balans",
                labels={"name": "", "amount": "Bedrag"},
                color_discrete_map={"asset": "#20c997", "liability": "#ff6b6b"},
            )
            st.plotly_chart(chart_layout(fig, dark_mode), use_container_width=True)
    with c4:
        if not expenses.empty:
            fig = px.pie(
                expenses,
                names="category",
                values="monthly_amount",
                hole=.5,
                title="Uitgaven per categorie",
                color_discrete_sequence=["#20c997", "#d5a64a", "#5b8def", "#9b7ede"],
            )
            st.plotly_chart(chart_layout(fig, dark_mode), use_container_width=True)
    if not etf.empty:
        fig = px.bar(
            etf,
            x="ticker",
            y="value",
            color="ticker",
            title="ETF-verdeling",
            labels={"ticker": "ETF", "value": "Actuele waarde"},
        )
        st.plotly_chart(chart_layout(fig, dark_mode), use_container_width=True)


ROUTES = {
    "Vandaag": today_page,
    "Dashboard": dashboard,
    "Persoonlijke waarheid": personal_truth_page,
    "Familie": family_page,
    "Opa-fonds": opa_fund_page,
    "Project Vrijheid": freedom_page,
    "Vrijheidstijdlijn": freedom_timeline_page,
    "Netto vermogen": balance_page,
    "ETF-portefeuille": etf_page,
    "Bitcoin-portefeuille": bitcoin_page,
    "Pensioenplanning": pension_page,
    "Lijfrenteplanning": annuity_page,
    "Netto maandinkomen": income_page,
    "Uitgavenplanner": expenses_page,
    "Scenarioanalyse": scenario_analysis_page,
    "AI-assistent": advisor_page,
    "Plancontrole": plan_check_page,
    "Beslislab": decision_lab_page,
    "Grafieken": charts_page,
    "Mijn uitgangspunten": settings_page,
}
ROUTES[page]()
