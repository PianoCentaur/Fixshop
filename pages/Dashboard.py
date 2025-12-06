import streamlit as st
import pandas as pd
from pathlib import Path
import plotly.express as px

st.set_page_config(page_title="FixShop – Prehľad a analýza", layout="wide")

st.title("🔧 FixShop – Prehľad a analýza")

# --------------------------------------------------------------------
# CESTA K DATA FOLDERU
# --------------------------------------------------------------------
DATA_DIR = Path("data")

# --------------------------------------------------------------------
# LOAD CSV
# --------------------------------------------------------------------
@st.cache_data
def load_csv(filename):
    path = DATA_DIR / filename
    return pd.read_csv(path, sep=";", encoding="utf-8", engine="python")


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

data = load_all_data()

# --------------------------------------------------------------------
# PRÍPRAVA DÁT
# --------------------------------------------------------------------
servis = data["servis"].copy()
zariadenie = data["zariadenie"].copy()
sklad = data["sklad_diely"].copy()
pouzite = data["pouzite_diely"].copy()
marketing = data["marketing"].copy()
praca = data["praca"].copy()

servis["Datum_odovzdania"] = pd.to_datetime(servis["Datum_odovzdania"])
servis["Rok"] = servis["Datum_odovzdania"].dt.year
servis["Mesiac"] = servis["Datum_odovzdania"].dt.month

# join zariadenie
servis = servis.merge(zariadenie, left_on="Zariadenie_id", right_on="id_zariadenia", how="left")

# join praca
praca["Trvanie_h"] = praca["Trvanie_h"].fillna(0)
servis = servis.merge(praca[["Praca_id", "Trvanie_h"]], on="Praca_id", how="left")
servis["naklad_praca"] = servis["Trvanie_h"] * 10.0

# materiál
pd_join = pouzite.merge(sklad[["Artikel", "Cena"]], on="Artikel", how="left")
pd_join["naklad_material"] = pd_join["Mnozstvo"] * pd_join["Cena"]

mat_sum = pd_join.groupby("pouzite_diely_id", as_index=False)["naklad_material"].sum()
servis = servis.merge(mat_sum, on="pouzite_diely_id", how="left")
servis["naklad_material"] = servis["naklad_material"].fillna(0)

# marketing – samostatný dataset (NEPRIPOČÍTAVAŤ k servisom!)
marketing["Rok"] = marketing["Rok"].astype(int)
marketing["Mesiac"] = marketing["Mesiac"].astype(int)

# --------------------------------------------------------------------
# FINÁLNE VÝPOČTY – OPRAVENÉ
# --------------------------------------------------------------------
servis["trzby"] = servis["Cena"]

# náklady (bez marketingu)
servis["naklady_spolu"] = servis["naklad_praca"] + servis["naklad_material"]

# marketing samostatne (mesačne)
marketing_total = marketing["Suma"].sum()

# celkový zisk
zisk = servis["trzby"].sum() - servis["naklady_spolu"].sum() - marketing_total

# KPI hodnoty
pocet_servisov = len(servis)
trzby_celkovo = servis["trzby"].sum()
naklady_celkovo = servis["naklady_spolu"].sum() + marketing_total
naklady_material = servis["naklad_material"].sum()
naklady_mzdy = servis["naklad_praca"].sum()
naklady_marketing = marketing_total

# --------------------------------------------------------------------
# ZOBRAZENIE KPI
# --------------------------------------------------------------------
def money(x):
    return f"{x:,.2f} €".replace(",", " ")

k1, k2, k3, k4 = st.columns(4)
k1.metric("🛠️ Počet servisov", pocet_servisov)
k2.metric("💰 Tržby celkom", money(trzby_celkovo))
k3.metric("📄 Náklady celkom", money(naklady_celkovo))
k4.metric("🟩 Zisk", money(zisk))

k5, k6, k7 = st.columns(3)
k5.metric("🔧 Náklady na materiál", money(naklady_material))
k6.metric("👨‍🔧 Náklady na mzdy", money(naklady_mzdy))
k7.metric("📣 Marketing", money(naklady_marketing))

st.divider()

# --------------------------------------------------------------------
# PIE CHARTY
# --------------------------------------------------------------------
st.subheader("🥧 Rozloženie podľa kategórií")

pie_cols = st.columns(3)

# podľa značky
with pie_cols[0]:
    st.markdown("### Podľa značky")
    df = servis.groupby("Znacka", as_index=False)["trzby"].sum()
    fig = px.pie(df, names="Znacka", values="trzby")
    fig.update_layout(height=350)
    st.plotly_chart(fig, use_container_width=True)

# podľa typu
with pie_cols[1]:
    st.markdown("### Podľa typu zariadenia")
    df = servis.groupby("Typ_zariadenia", as_index=False)["trzby"].sum()
    fig = px.pie(df, names="Typ_zariadenia", values="trzby")
    fig.update_layout(height=350)
    st.plotly_chart(fig, use_container_width=True)
