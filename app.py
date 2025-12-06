import streamlit as st
import pandas as pd
from pathlib import Path
import plotly.graph_objects as go
import plotly.express as px  # ponechané pre prípadné ďalšie grafy

# -------------------------------------------------
# ZÁKLADNÉ NASTAVENIE STRÁNKY
# -------------------------------------------------
st.set_page_config(
    page_title="FixShop – dashboard",
    layout="wide"
)

# Custom CSS – biele pozadie, sivý text, dlhé horizontálne inputy
st.markdown(
    """
    <style>
    [data-testid="stAppViewContainer"] {
        background-color: #FFFFFF;
        color: #444444;
    }
    [data-testid="stHeader"] {
        background-color: transparent;
    }
    [data-testid="stSidebar"] {
        background-color: #F7F7F7;
    }
    .fixshop-title {
        font-size: 40px;
        font-weight: 600;
        color: #444444;
        margin-bottom: 0.25rem;
    }
    .fixshop-subtitle {
        font-size: 16px;
        color: #777777;
        margin-bottom: 1.5rem;
    }
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 3rem;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ✔ Upravené pre cloud (bez __file__)
DATA_DIR = Path("data")
HODINOVA_SADZBA = 10.0  # jednoduchý model mzdy

# Preddefinované farby
COLOR_OPTIONS = {
    "🟦 Modrá": "#1E88E5",
    "🟧 Oranžová": "#FB8C00",
    "🟩 Zelená": "#43A047",
    "🟥 Červená": "#E53935",
    "🟪 Fialová": "#8E24AA",
}


# -------------------------------------------------
# NAČÍTANIE CSV
# -------------------------------------------------
@st.cache_data
def load_csv(filename: str) -> pd.DataFrame:
    path = DATA_DIR / filename
    return pd.read_csv(path, encoding="utf-8", sep=";", engine="python")


@st.cache_data
def load_all_data():
    return {
        "dodavatel": load_csv("cerovskywzsk5265_table_Dodavatel.csv"),
        "zakaznik": load_csv("cerovskywzsk5265_table_Zakaznik.csv"),
        "technik": load_csv("cerovskywzsk5265_table_Technik.csv"),
        "zariadenie": load_csv("cerovskywzsk5265_table_Zariadenie.csv"),
        "sklad_diely": load_csv("cerovskywzsk5265_table_Sklad_diely.csv"),
        "pouzite_diely": load_csv("cerovskywzsk5265_table_Pouzite_diely.csv"),
        "praca": load_csv("cerovskywzsk5265_table_Praca.csv"),
        "servis": load_csv("cerovskywzsk5265_table_Servis_protokol.csv"),
        "marketing": load_csv("cerovskywzsk5265_table_Marketing_naklady.csv"),
    }


# -------------------------------------------------
# PRÍPRAVA HLAVNÝCH DÁT
# -------------------------------------------------
@st.cache_data
def prepare_servis_df(data: dict):
    servis = data["servis"].copy()
    zariadenie = data["zariadenie"].copy()
    praca = data["praca"].copy()
    pouzite_diely = data["pouzite_diely"].copy()
    sklad_diely = data["sklad_diely"].copy()
    marketing = data["marketing"].copy()

    servis["Datum_prijatia"] = pd.to_datetime(servis["Datum_prijatia"])
    servis["Datum_odovzdania"] = pd.to_datetime(servis["Datum_odovzdania"])
    servis["Rok"] = servis["Datum_odovzdania"].dt.year
    servis["Mesiac"] = servis["Datum_odovzdania"].dt.month

    servis["RokMesiac"] = servis["Datum_odovzdania"].dt.to_period("M").astype(str)
    min_year = servis["Rok"].min()
    servis["MesiacIndex"] = (servis["Rok"] - min_year) * 12 + servis["Mesiac"]

    servis = servis.merge(
        zariadenie,
        left_on="Zariadenie_id",
        right_on="id_zariadenia",
        how="left",
    )

    if "Trvanie_h" in praca.columns:
        servis = servis.merge(
            praca[["Praca_id", "Trvanie_h"]],
            on="Praca_id",
            how="left"
        )
    else:
        servis["Trvanie_h"] = 0.0

    servis["Trvanie_h"] = servis["Trvanie_h"].fillna(0.0)

    pd_diely = pouzite_diely.merge(
        sklad_diely[["Artikel", "Cena"]],
        on="Artikel",
        how="left"
    )
    pd_diely["naklad_material"] = pd_diely["Mnozstvo"] * pd_diely["Cena"]
    mat_per_set = pd_diely.groupby("pouzite_diely_id", as_index=False)["naklad_material"].sum()

    servis = servis.merge(mat_per_set, on="pouzite_diely_id", how="left")
    servis["naklad_material"] = servis["naklad_material"].fillna(0.0)

    marketing["Rok"] = marketing["Rok"].astype(int)
    marketing["Mesiac"] = marketing["Mesiac"].astype(int)

    return servis, marketing


data = load_all_data()
servis_df, marketing_df = prepare_servis_df(data)

min_month_index = int(servis_df["MesiacIndex"].min())
max_month_index = int(servis_df["MesiacIndex"].max())
min_year = int(servis_df["Rok"].min())
max_year = int(servis_df["Rok"].max())


# -------------------------------------------------
# AGREGÁCIA PRE ČIARY
# -------------------------------------------------
def aggregate_series(
    df: pd.DataFrame,
    marketing: pd.DataFrame,
    metric_type: str,
    zisk_with_marketing: bool,
    naklad_components: list,
    time_mode: str,
    month_range=None,
    year_range=None,
    filter_type=None,
    filter_values=None,
):
    work = df.copy()

    if filter_type == "Znacka" and filter_values:
        work = work[work["Znacka"].isin(filter_values)]
    elif filter_type == "Typ" and filter_values:
        work = work[work["Typ_zariadenia"].isin(filter_values)]

    work["naklad_praca"] = work["Trvanie_h"] * HODINOVA_SADZBA

    if time_mode == "Mesiace":
        if month_range is not None:
            work = work[(work["MesiacIndex"] >= month_range[0]) & (work["MesiacIndex"] <= month_range[1])]
        group_keys = ["Rok", "Mesiac"]
    else:
        if year_range is not None:
            work = work[(work["Rok"] >= year_range[0]) & (work["Rok"] <= year_range[1])]
        group_keys = ["Rok"]

    if work.empty:
        return [], [], None

    agg = work.groupby(group_keys, as_index=False).agg({
        "Cena": "sum",
        "naklad_material": "sum",
        "naklad_praca": "sum"
    }).rename(columns={
        "Cena": "trzby",
        "naklad_material": "naklad_diely",
        "naklad_praca": "naklad_praca"
    })

    if time_mode == "Mesiace":
        mk = marketing.groupby(["Rok", "Mesiac"], as_index=False)["Suma"].sum().rename(columns={"Suma": "marketing"})
        agg = agg.merge(mk, on=["Rok", "Mesiac"], how="left")
        agg["marketing"] = agg["marketing"].fillna(0.0)
        x_labels = agg["Rok"].astype(str) + "-" + agg["Mesiac"].astype(str).str.zfill(2)
    else:
        mk = marketing.groupby(["Rok"], as_index=False)["Suma"].sum().rename(columns={"Suma": "marketing"})
        agg = agg.merge(mk, on=["Rok"], how="left")
        agg["marketing"] = agg["marketing"].fillna(0.0)
        x_labels = agg["Rok"].astype(str)

    agg["naklad_spolu"] = 0.0
    if "diely" in naklad_components:
        agg["naklad_spolu"] += agg["naklad_diely"]
    if "praca" in naklad_components:
        agg["naklad_spolu"] += agg["naklad_praca"]
    if "marketing" in naklad_components:
        agg["naklad_spolu"] += agg["marketing"]

    if metric_type == "Tržby":
        y = agg["trzby"]
    elif metric_type == "Zisk":
        if zisk_with_marketing:
            y = agg["trzby"] - agg["naklad_diely"] - agg["naklad_praca"] - agg["marketing"]
        else:
            y = agg["trzby"] - agg["naklad_diely"] - agg["naklad_praca"]
    else:
        y = agg["naklad_spolu"]

    avg_val = float(y.mean()) if len(y) > 0 else None
    return list(x_labels), list(y), avg_val


# -------------------------------------------------
# STAV – POČET ČIAR
# -------------------------------------------------
if "lines_count" not in st.session_state:
    st.session_state["lines_count"] = 1


# -------------------------------------------------
# UI + GRAF REŠTÁRT
# -------------------------------------------------
top_cols = st.columns([3, 1.3])

with top_cols[0]:
    st.markdown('<div class="fixshop-title">FixShop</div>', unsafe_allow_html=True)
    st.markdown('<div class="fixshop-subtitle">Servis telefónov – výnosy, náklady a zisk</div>', unsafe_allow_html=True)
    graph_placeholder = st.empty()

with top_cols[1]:
    st.markdown("#### Typ grafu")
    chart_type = st.selectbox("", ["Čiarový", "Stĺpcový", "Histogram"])

    st.markdown("#### Časová os")
    time_mode_global = st.radio("", ["Mesiace", "Roky"], horizontal=True)

    if time_mode_global == "Mesiace":
        month_range_global = st.slider("Rozsah", min_month_index, max_month_index, (min_month_index, max_month_index))
        year_range_global = None
    else:
        year_range_global = st.slider("Rozsah", min_year, max_year, (min_year, max_year))
        month_range_global = None


# -------------------------------------------------
# VELIČINY
# -------------------------------------------------
st.markdown("---")
st.markdown("## Údaje")

# 1. základná čiara
st.markdown("#### Veličina 1")

row0 = st.columns([1, 1, 1, 0.3])

with row0[0]:
    metric_0 = st.selectbox("", ["Tržby", "Zisk", "Náklady"])
    show_avg_0 = st.checkbox("Priemer")
    zisk_with_marketing_0 = False
    if metric_0 == "Zisk":
        zisk_mode_0 = st.radio("Zisk", ["Bez marketingu", "Vrátane marketingu"], horizontal=True)
        zisk_with_marketing_0 = (zisk_mode_0 == "Vrátane marketingu")

with row0[1]:
    filter_type_0 = None
    filter_values_0 = None
    naklad_components_0 = ["diely", "praca", "marketing"]

    if metric_0 == "Zisk":
        ft = st.selectbox("", ["Celkový", "Podľa značky", "Podľa typu zariadenia"])
        if ft == "Podľa značky":
            filter_type_0 = "Znacka"
            filter_values_0 = st.multiselect("Značky", sorted(servis_df["Znacka"].dropna().unique()))
        elif ft == "Podľa typu zariadenia":
            filter_type_0 = "Typ"
            filter_values_0 = st.multiselect("Typ", sorted(servis_df["Typ_zariadenia"].dropna().unique()))

    elif metric_0 == "Náklady":
        naklad_components_0 = st.multiselect("", ["diely", "praca", "marketing"], default=["diely", "praca", "marketing"])

with row0[2]:
    color_name_0 = st.selectbox("", list(COLOR_OPTIONS.keys()), index=0)
    color_0 = COLOR_OPTIONS[color_name_0]

line_configs = [{
    "metric_type": metric_0,
    "show_avg": show_avg_0,
    "zisk_with_marketing": zisk_with_marketing_0,
    "filter_type": filter_type_0,
    "filter_values": filter_values_0,
    "naklad_components": naklad_components_0,
    "color": color_0,
}]

plus_row = st.columns([0.15, 0.85])
with plus_row[0]:
    if st.button("➕", help="Pridať ďalšiu čiaru", disabled=(st.session_state["lines_count"] >= 3)):
        st.session_state["lines_count"] += 1


# -------------------------------------------------
# ĎALŠIE ČIARY
# -------------------------------------------------
remove_idx = None

for i in range(1, st.session_state["lines_count"]):
    st.markdown(f"#### Veličina {i + 1}")
    cols = st.columns([1, 1, 1, 0.25])

    with cols[0]:
        metric_i = st.selectbox("", ["Tržby", "Zisk", "Náklady"], key=f"metric_{i}")
        show_avg_i = st.checkbox("Priemer", key=f"avg_{i}")
        zisk_with_marketing_i = False
        if metric_i == "Zisk":
            zisk_mode_i = st.radio("Zisk", ["Bez marketingu", "Vrátane marketingu"], horizontal=True, key=f"zisk_mode_{i}")
            zisk_with_marketing_i = (zisk_mode_i == "Vrátane marketingu")

    with cols[1]:
        filter_type_i = None
        filter_values_i = None
        naklad_components_i = ["diely", "praca", "marketing"]

        if metric_i == "Zisk":
            ft_i = st.selectbox("", ["Celkový", "Podľa značky", "Podľa typu zariadenia"], key=f"ft_{i}")
            if ft_i == "Podľa značky":
                filter_type_i = "Znacka"
                filter_values_i = st.multiselect("Značky", sorted(servis_df["Znacka"].dropna().unique()), key=f"fv_{i}")
            elif ft_i == "Podľa typu zariadenia":
                filter_type_i = "Typ"
                filter_values_i = st.multiselect("Typ", sorted(servis_df["Typ_zariadenia"].dropna().unique()), key=f"fv2_{i}")
        elif metric_i == "Náklady":
            naklad_components_i = st.multiselect("", ["diely", "praca", "marketing"], default=["diely", "praca", "marketing"], key=f"nc_{i}")

    with cols[2]:
        color_name_i = st.selectbox("", list(COLOR_OPTIONS.keys()), index=min(i, len(COLOR_OPTIONS)-1), key=f"col_{i}")
        color_i = COLOR_OPTIONS[color_name_i]

    with cols[3]:
        if st.button("❌", key=f"rem_{i}"):
            remove_idx = i

    line_configs.append({
        "metric_type": metric_i,
        "show_avg": show_avg_i,
        "zisk_with_marketing": zisk_with_marketing_i,
        "filter_type": filter_type_i,
        "filter_values": filter_values_i,
        "naklad_components": naklad_components_i,
        "color": color_i,
    })

if remove_idx is not None and st.session_state["lines_count"] > 1:
    st.session_state["lines_count"] -= 1


# -------------------------------------------------
# GRAF
# -------------------------------------------------
fig = go.Figure()

for cfg in line_configs:
    x, y, avg_val = aggregate_series(
        df=servis_df,
        marketing=marketing_df,
        metric_type=cfg["metric_type"],
        zisk_with_marketing=cfg["zisk_with_marketing"],
        naklad_components=cfg["naklad_components"],
        time_mode=time_mode_global,
        month_range=month_range_global,
        year_range=year_range_global,
        filter_type=cfg["filter_type"],
        filter_values=cfg["filter_values"],
    )

    if not y:
        continue

    name = cfg["metric_type"]
    if cfg["metric_type"] == "Zisk" and cfg["zisk_with_marketing"]:
        name += " (vrátane marketingu)"

    if chart_type == "Čiarový":
        fig.add_trace(go.Scatter(x=x, y=y, mode="lines+markers", name=name, line=dict(color=cfg["color"], width=2)))
        if cfg["show_avg"] and len(y) >= 2:
            ma_window = 5
            y_ma = pd.Series(y).rolling(ma_window).mean().tolist()
            fig.add_trace(go.Scatter(x=x, y=y_ma, mode="lines", name=f"Priemer ({ma_window}) – {name}",
                                     line=dict(color=cfg["color"], width=2, dash="dot")))

    elif chart_type == "Stĺpcový":
        fig.add_trace(go.Bar(x=x, y=y, name=name, marker_color=cfg["color"]))
        if cfg["show_avg"] and avg_val is not None:
            fig.add_trace(go.Scatter(x=x, y=[avg_val] * len(x), mode="lines",
                                     name=f"Priemer – {name}", line=dict(color=cfg["color"], width=1, dash="dash")))

    else:
        fig.add_trace(go.Histogram(x=y, name=name, marker_color=cfg["color"], opacity=0.7))


fig.update_layout(
    xaxis_title="Čas",
    yaxis_title="Hodnota",
    height=450,
    margin=dict(l=40, r=40, t=10, b=40),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
)

graph_placeholder.plotly_chart(fig, use_container_width=True)
