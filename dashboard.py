import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import re

# -----------------------------------------------------------------------------
# 1. PAGE CONFIGURATION
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Analisis Kompetitif", layout="wide")

# -----------------------------------------------------------------------------
# 2. CUSTOM CSS (RESTORED ORIGINAL WINGS UI)
# -----------------------------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }
    .stApp { background-color: #F8FAFC; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    [data-testid="stElementToolbar"] { display: none !important; }
    .block-container { padding-top: 3.5rem !important; padding-bottom: 2rem !important; padding-left: 3rem !important; padding-right: 3rem !important; max-width: 100% !important; }
    [data-testid="stSidebar"] { background: linear-gradient(180deg, #E30613 0%, #B71C1C 100%) !important; box-shadow: 4px 0 15px rgba(0,0,0,0.1); }
    [data-testid="stSidebarCollapseButton"] svg *, [data-testid="stSidebarNav"] svg *, button[aria-label="Collapse sidebar"] svg *, button[aria-label="Expand sidebar"] svg *, [data-testid="collapsedControl"] svg *, section[data-testid="stSidebar"] button svg * { color: #ffffff !important; fill: #ffffff !important; stroke: #ffffff !important; }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3, [data-testid="stSidebar"] h4 { color: #ffffff !important; font-weight: 700; letter-spacing: 0.5px; }
    [data-testid="stSidebar"] label { color: #ffffff !important; font-weight: 600; letter-spacing: 0.5px; margin-bottom: 2px !important; }
    .sidebar-menu-active { color: #E30613 !important; font-weight: 700; display: block; padding: 10px 15px; background: #ffffff; border-radius: 8px; border-left: 8px solid #FFD700; margin-bottom: 8px; transition: all 0.3s ease; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    .sidebar-menu-active:hover { background: #f8fafc; transform: translateX(4px); }
    div[data-baseweb="select"] > div { background-color: white !important; border: 1px solid #fca5a5 !important; border-radius: 10px !important; box-shadow: 0 2px 4px rgba(0,0,0,0.02) !important; transition: all 0.2s ease; }
    div[data-baseweb="select"] > div:hover { border-color: #E30613 !important; box-shadow: 0 0 0 2px rgba(227, 6, 19, 0.2) !important; }
    span[data-baseweb="tag"] { background-color: #fee2e2 !important; color: #b91c1c !important; border-radius: 12px !important; font-weight: 600; font-size: 13px !important; border: 1px solid #fca5a5 !important; padding: 2px 8px !important; margin: 1px 2px !important; display: inline-flex !important; align-items: center !important; justify-content: center !important; }
    span[data-baseweb="tag"] span { color: #b91c1c !important; padding-left: 5px !important; margin-left: 5px !important; }
    ul[data-baseweb="menu"] { border-radius: 10px !important; overflow: hidden !important; }
    .top-navbar { background-color: white; margin-left: -3rem; margin-right: -3rem; margin-top: -3.5rem; padding: 1.5rem 3rem; border-bottom: 1px solid #f1f5f9; margin-bottom: 2rem; display: flex; align-items: center; box-shadow: 0 4px 10px rgba(0,0,0,0.02); }
    [data-testid="stHeader"] { background-color: transparent !important; }
    .report-subtitle-card { background-color: white; padding: 12px 25px; margin-bottom: 25px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.02); border-left: 5px solid #E30613; border-top: 1px solid #f1f5f9; border-right: 1px solid #f1f5f9; border-bottom: 1px solid #f1f5f9; display: flex; align-items: center; width: 100%; }
    .report-subtitle { font-weight: 700; font-size: 14px; color: #1e293b; margin: 0; text-transform: uppercase; letter-spacing: 1px; }

    .kpi-container { background-color: white; padding: 14px 16px; border-radius: 16px; box-shadow: 0 4px 10px rgba(0,0,0,0.03), 0 1px 3px rgba(0,0,0,0.02); margin-bottom: 10px; height: 100%; min-height: 175px; position: relative; overflow: hidden; transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1); border: 1px solid #f1f5f9; display: flex; flex-direction: column; justify-content: space-between; }
    .kpi-container:hover { transform: translateY(-5px); box-shadow: 0 12px 25px rgba(0,0,0,0.06), 0 4px 8px rgba(0,0,0,0.04); }
    .kpi-container::after { content: ''; position: absolute; top: -20px; right: -20px; width: 60px; height: 60px; border-radius: 50%; opacity: 0.12; }
    .kpi-1::after { background-color: #E30613; }
    .kpi-2::after { background-color: #FFD700; }
    .kpi-3::after { background-color: #E30613; }
    .kpi-4::after { background-color: #FFD700; }
    .kpi-5::after { background-color: #E30613; }

    .kpi-title { font-size: 11.5px; font-weight: 700; color: #64748b; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.2px; line-height: 1.3; }
    .kpi-value { font-size: 22px; font-weight: 800; color: #0f172a; text-align: left; margin-bottom: 10px; line-height: 1.2; word-wrap: break-word; overflow-wrap: break-word; hyphens: auto; }
    .kpi-sub { font-size: 10px; font-weight: 500; color: #64748b; background-color: #f8fafc; padding: 4px 6px; border-radius: 6px; display: inline-block; border-left: 3px solid; line-height: 1.3; }

    .chart-container { margin-bottom: 15px; height: 100%; transition: all 0.3s ease; }
    .chart-title { font-size: 16px; font-weight: 700; color: #1e293b; margin-bottom: 8px; display: flex; align-items: flex-start; line-height: 1.3; }
    .chart-title::before { content: ''; display: inline-block; width: 5px; height: 20px; background-color: #E30613; margin-right: 10px; border-radius: 4px; margin-top: 0px; }
    .chart-desc { font-size: 11px; color: #64748b; margin-top: 0px; margin-bottom: 15px; line-height: 1.4; min-height: 35px; }
</style>
""", unsafe_allow_html=True)

# Colors
COLOR_WINGS_RED = "#E30613"
COLOR_WINGS_YELLOW = "#FFD700"
COLOR_INDO_BLUE = "#00529d"
COLOR_DARK_NAVY = "#0A2342"
COLOR_GREY = "#64748b"
# -----------------------------------------------------------------------------
# 3. DATA LOADING & PREPARATION
# -----------------------------------------------------------------------------
def load_data():
    cols = [
        'scrape_date', 'company', 'brand', 'product_name', 'sku_id', 'pack_size',
        'original_price', 'final_price', 'discount_pct', 'retailer', 'platform',
        'province', 'city', 'promo_type', 'promo_text', 'variant', 'flavor',
        'offer_structure', 'promo_start', 'promo_end', 'sales_volume'
    ]
    df = pd.read_csv('final_normalized_data.csv', header=None, names=cols, na_values=['NULL'])

    df['final_price'] = pd.to_numeric(df['final_price'], errors='coerce')
    df['original_price'] = pd.to_numeric(df['original_price'], errors='coerce')
    df['discount_pct'] = pd.to_numeric(df['discount_pct'], errors='coerce')
    df['sales_volume'] = pd.to_numeric(df['sales_volume'], errors='coerce').fillna(0)
    df['revenue'] = df['final_price'] * df['sales_volume']

    BRAND_AVG_WEIGHT = {
        'Mie Sedaap': 82,  # gram (avg dari varian goreng 90g, soto 75g, dll)
        'Indomie': 80,     # gram (avg dari goreng 80g, kuah 70g, dll)
    }

    def extract_total_weight(row):
        ps = row.get('pack_size', None)
        brand = row.get('brand', None)
        
        if pd.isna(ps):
            return None
        
        ps_str = str(ps).lower()
        
        # Format: "5 x 90g" atau "40 x 75g"
        m = re.match(r'(\d+)\s*x\s*(\d+)g', ps_str)
        if m:
            return int(m.group(1)) * int(m.group(2))
        
        # Format: "85g" atau "90g"
        m2 = re.match(r'^(\d+)g$', ps_str)
        if m2:
            return int(m2.group(1))
        
        # Format: "40 pcs" atau "5 pcs" -> estimasi pakai avg berat brand
        m3 = re.match(r'(\d+)\s*pcs', ps_str)
        if m3:
            qty = int(m3.group(1))
            avg_w = BRAND_AVG_WEIGHT.get(brand, 81)  # default 81g
            return qty * avg_w
        
        return None

    def extract_unit_quantity(ps):
        if pd.isna(ps): return 1
        ps = str(ps).lower()
        m = re.match(r'(\d+)\s*x\s*', ps)
        if m: return int(m.group(1))
        m2 = re.match(r'(\d+)\s*pcs', ps)
        if m2: return int(m2.group(1))
        return 1

    df['total_weight_g'] = df.apply(extract_total_weight, axis=1)
    df['unit_quantity'] = df['pack_size'].apply(extract_unit_quantity)
    df['price_per_100g'] = (df['final_price'] / df['total_weight_g']) * 100

    def validate_price_per_unit(row):
        price = row['final_price']
        pack_type = row['offer_structure']
        weight = row['total_weight_g']
        
        suspicious = False
        
        # Cek utama: price_per_100g di luar range wajar mie instan
        # Range wajar: Rp 300 (karton murah) s/d Rp 25.000 (premium cup/korean)
        if pd.notna(weight) and weight > 0:
            p100g = (price / weight) * 100
            # Menggunakan 25000 karena Cup Premium bisa mencapai Rp 19.700/100g
            if p100g > 25000 or p100g < 300:
                suspicious = True
        
        # Cek tambahan hanya untuk kasus ekstrem yang jelas
        if pack_type == 'Single Pack' and price > 25000:
            suspicious = True
            
        return suspicious

    # Flag dulu, jangan langsung drop
    df['price_flag'] = df.apply(validate_price_per_unit, axis=1)
    df[df['price_flag']].to_csv('suspicious_sku.csv', index=False)
    
    # Hanya pakai data yang lolos validasi
    df_clean = df[~df['price_flag']].copy()
    
    return df_clean
df = load_data()

# -----------------------------------------------------------------------------
# 4. SIDEBAR
# -----------------------------------------------------------------------------
import base64
import os

with st.sidebar:
    import os
    import base64
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    logo_path = os.path.join(current_dir, 'wings_logo.png')
    
    # CSS untuk memberi kotak putih di belakang logo agar warna merah asli tidak tenggelam di sidebar yang merah
    st.markdown("""
        <style>
        [data-testid="stSidebar"] img { 
            background-color: white; 
            padding: 15px; 
            border-radius: 12px; 
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            margin-bottom: 20px; 
            margin-top: -60px;
        }
        </style>
    """, unsafe_allow_html=True)

    if os.path.exists(logo_path):
        with open(logo_path, 'rb') as f:
            img_data = f.read()
            
        # Cek apakah file yang di-download ternyata berisi kode SVG/vektor
        if b'<svg' in img_data[:1000] or b'<path' in img_data[:1000] or b'<?xml' in img_data[:1000]:
            img_b64 = base64.b64encode(img_data).decode('utf-8')
            st.markdown(f'<div style="text-align: center;"><img src="data:image/svg+xml;base64,{img_b64}" width="140"></div>', unsafe_allow_html=True)
        else:
            # Jika itu benar-benar gambar PNG/JPEG asli
            st.image(logo_path, width=140)
    else:
        st.markdown("<p style='color:white; font-size:12px;'>[Logo tidak ditemukan]</p>", unsafe_allow_html=True)

    st.markdown("<h3 style='color:#ffffff;'>Halaman</h3>", unsafe_allow_html=True)
    st.markdown("<div class='sidebar-menu-active'>Ringkasan Eksekutif</div>", unsafe_allow_html=True)
    st.markdown("<h4 style='color:#ffffff; margin-top: 15px;'>Penyaring Data</h4>", unsafe_allow_html=True)
    companies = sorted(df['company'].dropna().unique())
    selected_company = st.multiselect("Perusahaan", companies, default=companies)
    df_comp = df[df['company'].isin(selected_company)] if selected_company else df
    platforms = sorted(df_comp['platform'].dropna().unique())
    selected_platform = st.multiselect("Platform", platforms, default=platforms)
    provinces = sorted(df_comp['province'].dropna().unique())
    selected_province = st.multiselect("Provinsi", provinces, default=provinces)
    offer_structs = sorted(df_comp['offer_structure'].dropna().unique())
    default_offer = ["Single Pack"] if "Single Pack" in offer_structs else offer_structs
    selected_offer = st.multiselect("Jenis Kemasan", offer_structs, default=default_offer)
df_filtered = df_comp[
    (df_comp['platform'].isin(selected_platform)) &
    (df_comp['province'].isin(selected_province)) &
    (df_comp['offer_structure'].isin(selected_offer))
]
if df_filtered.empty or not selected_company:
    st.error("No data available for the selected filters.")
    st.stop()

if len(selected_offer) > 1:
    st.warning("Peringatan: Metrik saat ini menggabungkan harga eceran dan grosir. Ini dapat memengaruhi rata-rata harga.")

if 'Bundle' in selected_offer or 'Multipack' in selected_offer:
    st.info(
        "ℹ️ Harga per 100g untuk kemasan Bundle/Multipack "
        "yang tidak mencantumkan berat (format '40 pcs') "
        "menggunakan estimasi berat rata-rata per bungkus. "
        "Gunakan sebagai indikasi, bukan nilai absolut."
    )

# -----------------------------------------------------------------------------
# 5. DYNAMIC KPI LOGIC & LAYOUT
# -----------------------------------------------------------------------------
MODE = "COMPARISON" if len(selected_company) == 2 else "SINGLE_BRAND"

report_title = "LAPORAN ANALISIS KOMPETITIF" if MODE == "COMPARISON" else f"LAPORAN ANALISIS {selected_company[0].upper()}"
report_subtitle = "Ringkasan Eksekutif " if MODE == "COMPARISON" else "Panel Analisis Merek"

st.markdown(f"""
<div class="top-navbar">
    <h2 style="margin:0; font-weight: 800; font-size: 22px; color: #1e293b; letter-spacing: -0.5px; text-transform: uppercase;">{report_title}</h2>
</div>
<div class="report-subtitle-card">
    <p class="report-subtitle">{report_subtitle}</p>
</div>
""", unsafe_allow_html=True)
def generate_exec_summary(df_filtered, mode):
    if mode == "SINGLE_BRAND":
        return "Insight analitik komparatif tidak tersedia. Silakan pilih minimal dua brand pada filter (misalnya: Wings Group dan Indofood) untuk melihat perbandingan agresivitas harga dan promosi secara langsung."
    
    wings_df = df_filtered[df_filtered['company'] == 'Wings Group']
    indo_df = df_filtered[df_filtered['company'] == 'Indofood']
    
    if wings_df.empty or indo_df.empty:
        return "Data tidak mencukupi untuk menghasilkan Executive Summary perbandingan harga dan promosi."

    def clean_prices(series, low_pct=0.05, high_pct=0.95):
        s = series.dropna()
        if s.empty: return s
        lo, hi = s.quantile(low_pct), s.quantile(high_pct)
        return s[(s >= lo) & (s <= hi)]
        
    w_price = clean_prices(wings_df['final_price']).mean()
    i_price = clean_prices(indo_df['final_price']).mean()
    w_promo_cov = len(wings_df[wings_df['discount_pct'] > 0]) / len(wings_df) if len(wings_df) else 0
    i_promo_cov = len(indo_df[indo_df['discount_pct'] > 0]) / len(indo_df) if len(indo_df) else 0
    
    cheaper_brand = "Mie Sedaap (Wings Group)" if w_price <= i_price else "Indomie (Indofood)"
    expensive_brand = "Indomie (Indofood)" if w_price <= i_price else "Mie Sedaap (Wings Group)"
    
    promo_leader = "Mie Sedaap (Wings Group)" if w_promo_cov >= i_promo_cov else "Indomie (Indofood)"
    
    if cheaper_brand == promo_leader:
        return f"Secara keseluruhan, rata-rata harga produk {cheaper_brand} terpantau lebih murah, menjadikannya lebih kompetitif secara harga dasar. Selain itu, merek ini juga menunjukkan penetrasi promosi yang lebih agresif dibandingkan {expensive_brand}. Sinyal pasar ini mengindikasikan strategi ganda yang kuat—menekan harga sekaligus memperluas visibilitas promo untuk merebut pangsa pasar."
    else:
        return f"Meskipun rata-rata harga produk {expensive_brand} cenderung lebih tinggi dibandingkan {cheaper_brand}, mereka mencoba mengimbanginya dengan penetrasi promosi yang lebih agresif. Sinyal pasar ini menunjukkan strategi harga premium yang dikompensasi dengan taktik diskon intensif untuk tetap mempertahankan daya tarik di mata konsumen."

exec_summary_text = generate_exec_summary(df_filtered, MODE)

st.markdown(f"""
<div style="background-color: #ffffff; border-left: 5px solid #10b981; padding: 16px 24px; border-radius: 8px; margin-bottom: 25px; box-shadow: 0 2px 8px rgba(0,0,0,0.02); border-top: 1px solid #f1f5f9; border-right: 1px solid #f1f5f9; border-bottom: 1px solid #f1f5f9;">
    <div style="display: flex; align-items: center; margin-bottom: 8px;">
        <span style="font-size: 16px; margin-right: 8px;">🤖</span>
        <strong style="color: #0f172a; font-size: 15px; letter-spacing: 0.5px;">WAWASAN ANALIS AI</strong>
    </div>
    <p style="margin: 0; font-size: 14px; color: #475569; line-height: 1.6;">{exec_summary_text}</p>
</div>
""", unsafe_allow_html=True)

def format_number(num):
    if pd.isna(num): return "-"
    return f"{num:,.0f}".replace(",", ".")

def draw_kpi_card(title, value, sub_text, sub_color, kpi_class):
    return f"""
    <div class="kpi-container {kpi_class}">
        <div class="kpi-title">{title}</div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-sub" style="border-left: 4px solid {sub_color};">{sub_text}</div>
    </div>
    """

if MODE == "COMPARISON":
    df_sedaap = df_filtered[df_filtered['brand'] == 'Mie Sedaap']
    df_indo = df_filtered[df_filtered['brand'] == 'Indomie']

    # ── Outlier-resistant price helper ───────────────────────────────────────
    def clean_prices(series, low_pct=0.05, high_pct=0.95):
        s = series.dropna()
        if s.empty:
            return s
        lo = s.quantile(low_pct)
        hi = s.quantile(high_pct)
        return s[(s >= lo) & (s <= hi)]

    # ── SEMUA KPI HARGA BERBASIS price_per_100g ──────────────────────────────
    # price_per_100g sudah dinormalisasi di load_data() untuk SEMUA jenis kemasan
    # (termasuk Bundle "40 pcs" via estimasi berat brand). Ini membuat perbandingan
    # apple-to-apple terlepas dari jenis kemasan apa yang aktif di filter.
    p100g_sed = clean_prices(df_sedaap['price_per_100g'])
    p100g_ind = clean_prices(df_indo['price_per_100g'])

    avg_unit_sedaap = p100g_sed.median()
    avg_unit_indo   = p100g_ind.median()

    # % Selisih: selalu berdasarkan median per-100g
    price_gap = ((avg_unit_sedaap - avg_unit_indo) / avg_unit_indo * 100) if pd.notna(avg_unit_sedaap) and pd.notna(avg_unit_indo) and avg_unit_indo > 0 else 0

    # Rasio Harga: berdasarkan per-100g supaya apple-to-apple
    pos_index = (avg_unit_sedaap / avg_unit_indo) if pd.notna(avg_unit_sedaap) and pd.notna(avg_unit_indo) and avg_unit_indo > 0 else 0

    # Selisih Produk Termurah: per-100g basis
    min_p100g_sed = p100g_sed.min() if not p100g_sed.empty else None
    min_p100g_ind = p100g_ind.min() if not p100g_ind.empty else None
    gap_min = (min_p100g_sed - min_p100g_ind) if pd.notna(min_p100g_sed) and pd.notna(min_p100g_ind) else 0

    # --- PRICING KPI ---
    st.markdown("<h4 style='color:#1e293b; margin-top:10px; margin-bottom:-5px;'>Indikator Utama: Harga</h4>", unsafe_allow_html=True)
    c1, c2, c3, c4, c5, c6 = st.columns(6)

    # Realita Bisnis: Harga Eceran vs Grosir (mengambil dari df_filtered agar konsisten dengan filter aktif)
    df_eceran = df_filtered[df_filtered['offer_structure'].str.contains('Single', case=False, na=False)]
    df_grosir = df_filtered[df_filtered['offer_structure'].str.contains('Bundle|Carton|Karton|Dus|Multipack', case=False, na=False)].copy()
    
    # Eceran: harga jual aktual per bungkus (yang dilihat konsumen di marketplace)
    # Grosir: harga jual / jumlah unit dalam bundle (harga per bungkus dari karton)
    df_grosir['normalized_price'] = df_grosir['final_price'] / df_grosir['unit_quantity']
    
    avg_eceran_s = clean_prices(df_eceran[df_eceran['brand'] == 'Mie Sedaap']['final_price']).median()
    avg_eceran_i = clean_prices(df_eceran[df_eceran['brand'] == 'Indomie']['final_price']).median()
    avg_grosir_s = clean_prices(df_grosir[df_grosir['brand'] == 'Mie Sedaap']['normalized_price']).median()
    avg_grosir_i = clean_prices(df_grosir[df_grosir['brand'] == 'Indomie']['normalized_price']).median()

    val_eceran_s = f"Rp {format_number(avg_eceran_s)}" if pd.notna(avg_eceran_s) else "-"
    val_eceran_i = f"Rp {format_number(avg_eceran_i)}" if pd.notna(avg_eceran_i) else "-"
    val_grosir_s = f"Rp {format_number(avg_grosir_s)}" if pd.notna(avg_grosir_s) else "-"
    val_grosir_i = f"Rp {format_number(avg_grosir_i)}" if pd.notna(avg_grosir_i) else "-"

    html_eceran = f"<div style='font-size: 0.55em; line-height: 1.4;'>Sedaap: {val_eceran_s}<br>Indomie: {val_eceran_i}</div>"
    html_grosir = f"<div style='font-size: 0.55em; line-height: 1.4;'>Sedaap: {val_grosir_s}<br>Indomie: {val_grosir_i}</div>"

    # Format Unit Price properly so it doesn't show "Rp -"
    unit_sed_str = f"Rp {format_number(avg_unit_sedaap)}" if pd.notna(avg_unit_sedaap) else "-"
    unit_ind_str = f"Rp {format_number(avg_unit_indo)}" if pd.notna(avg_unit_indo) else "-"
    combined_value = f"<div style='font-size: 0.55em; line-height: 1.4;'>Mie Sedaap: {unit_sed_str}<br>Indomie: {unit_ind_str}</div>"

    # Card 3: Rasio Harga (per-100g basis)
    if pos_index > 1.0:
        rasio_text = "Mie Sedaap Lebih Mahal"
    elif 0 < pos_index < 1.0:
        rasio_text = "Mie Sedaap Lebih Murah"
    elif pos_index == 1.0:
        rasio_text = "Rata-rata Harga Sama"
    else:
        rasio_text = "Data Tidak Cukup"

    if len(selected_offer) > 1:
        with c1: st.markdown(draw_kpi_card("Rata-rata Harga Eceran", html_eceran, "Rp per bungkus · Single Pack", COLOR_WINGS_RED, "kpi-1"), unsafe_allow_html=True)
        with c2: st.markdown(draw_kpi_card("Rata-rata Harga Grosir", html_grosir, "Rp per bungkus · Bundle / Karton", COLOR_INDO_BLUE, "kpi-2"), unsafe_allow_html=True)
    else:
        # Mode single-filter: tampilkan harga aktual per bungkus
        # Jika Single Pack → harga eceran langsung
        # Jika Bundle/Multipack → harga per unit (dibagi jumlah isi)
        active_filter = selected_offer[0] if selected_offer else ""
        if active_filter in ['Bundle', 'Multipack']:
            df_active = df_filtered.copy()
            df_active['normalized_price'] = df_active['final_price'] / df_active['unit_quantity']
            sed_price = clean_prices(df_active[df_active['brand'] == 'Mie Sedaap']['normalized_price']).median()
            ind_price = clean_prices(df_active[df_active['brand'] == 'Indomie']['normalized_price']).median()
            sub_label = "Rp per bungkus (dari bundle)"
        else:
            sed_price = clean_prices(df_sedaap['final_price']).median()
            ind_price = clean_prices(df_indo['final_price']).median()
            sub_label = "Rp per bungkus"
        with c1: st.markdown(draw_kpi_card("Rata-rata Harga Mie Sedaap", f"Rp {format_number(sed_price)}" if pd.notna(sed_price) else "-", sub_label, COLOR_WINGS_RED, "kpi-1"), unsafe_allow_html=True)
        with c2: st.markdown(draw_kpi_card("Rata-rata Harga Indomie", f"Rp {format_number(ind_price)}" if pd.notna(ind_price) else "-", sub_label, COLOR_INDO_BLUE, "kpi-2"), unsafe_allow_html=True)

    with c3: st.markdown(draw_kpi_card("Rasio Harga", f"{pos_index:.2f}", rasio_text, COLOR_GREY, "kpi-3"), unsafe_allow_html=True)
    with c4: st.markdown(draw_kpi_card("Rata-rata Harga Satuan (100g)", combined_value, "Perbandingan Harga (per 100g)", COLOR_WINGS_YELLOW, "kpi-4"), unsafe_allow_html=True)
    with c5: st.markdown(draw_kpi_card("Persentase Selisih Harga", f"{price_gap:+.2f}%", "Selisih per 100g thd Indomie", COLOR_DARK_NAVY, "kpi-5"), unsafe_allow_html=True)
    with c6: st.markdown(draw_kpi_card("Selisih Produk Termurah", f"Rp {format_number(gap_min)}" if pd.notna(gap_min) else "-", "Selisih per 100g Batas Bawah", COLOR_WINGS_RED, "kpi-1"), unsafe_allow_html=True)

    # --- PROMOTION & MARKET KPI ---
    col_head1, col_head2 = st.columns([4, 2])
    with col_head1:
        st.markdown("<h4 style='color:#1e293b; margin-top:5px; margin-bottom:-5px;'>Indikator Utama: Promosi</h4>", unsafe_allow_html=True)
    with col_head2:
        st.markdown("<h4 style='color:#1e293b; margin-top:5px; margin-bottom:-5px;'>Indikator Utama: Pasar</h4>", unsafe_allow_html=True)

    c1, c2, c3, c4, c5, c6 = st.columns(6)

    promo_df = df_filtered[df_filtered['promo_type'] != 'No Promo']
    active_promo_sku = len(promo_df)
    avg_disc = promo_df['discount_pct'].mean()
    promo_cov = (active_promo_sku / len(df_filtered) * 100) if len(df_filtered) > 0 else 0
    promo_intensity = promo_cov * (avg_disc / 100) if pd.notna(avg_disc) else 0

    lowest_reg_name = "N/A"
    lowest_reg_val = 0
    highest_reg_name = "N/A"
    highest_reg_val = 0
    if 'city' in df_filtered.columns and not df_filtered.empty:
        reg_price = df_filtered.groupby('city')['final_price'].mean().reset_index()
        if not reg_price.empty:
            lowest_reg_row = reg_price.loc[reg_price['final_price'].idxmin()]
            lowest_reg_name = lowest_reg_row['city']
            lowest_reg_val = lowest_reg_row['final_price']
            
            highest_reg_row = reg_price.loc[reg_price['final_price'].idxmax()]
            highest_reg_name = highest_reg_row['city']
            highest_reg_val = highest_reg_row['final_price']

    with c1: st.markdown(draw_kpi_card("Total Produk Diskon", f"{active_promo_sku:,}", "Total dari Seluruh Brand", COLOR_WINGS_RED, "kpi-2"), unsafe_allow_html=True)
    with c2: st.markdown(draw_kpi_card("Rata-Rata Potongan", f"{avg_disc:.1f}%" if pd.notna(avg_disc) else "0%", "Potongan Harga Pasar", COLOR_WINGS_YELLOW, "kpi-3"), unsafe_allow_html=True)
    with c3: st.markdown(draw_kpi_card("Sebaran Promosi", f"{promo_cov:.1f}%", "% Produk yang Didiskon", COLOR_DARK_NAVY, "kpi-4"), unsafe_allow_html=True)
    with c4: st.markdown(draw_kpi_card("Agresivitas Promosi", f"{promo_intensity:.2f}", "Skor Sebaran × Kedalaman", COLOR_GREY, "kpi-5"), unsafe_allow_html=True)
    with c5: st.markdown(draw_kpi_card("Kota Harga Termurah", lowest_reg_name, f"Avg Price: Rp {format_number(lowest_reg_val)}", COLOR_WINGS_RED, "kpi-1"), unsafe_allow_html=True)
    with c6: st.markdown(draw_kpi_card("Kota Harga Termahal", highest_reg_name, f"Avg Price: Rp {format_number(highest_reg_val)}", COLOR_DARK_NAVY, "kpi-2"), unsafe_allow_html=True)

else:
    # --- SINGLE BRAND PANEL ---
    st.markdown("<h4 style='color:#1e293b; margin-top:10px; margin-bottom:15px;'>Panel Harga & Promo Merek</h4>", unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)

    brand_name = df_filtered['brand'].iloc[0] if not df_filtered.empty else "N/A"
    accent_color = COLOR_WINGS_RED if brand_name == "Mie Sedaap" else COLOR_INDO_BLUE

    def clean_prices(series, low_pct=0.05, high_pct=0.95):
        s = series.dropna()
        if s.empty:
            return s
        lo, hi = s.quantile(low_pct), s.quantile(high_pct)
        return s[(s >= lo) & (s <= hi)]

    avg_price = clean_prices(df_filtered['final_price']).mean()
    promo_df = df_filtered[df_filtered['promo_type'] != 'No Promo']
    promo_sku = len(promo_df)
    avg_disc = promo_df['discount_pct'].mean()

    top_sku_row = df_filtered.loc[df_filtered['sales_volume'].idxmax()] if not df_filtered.empty else None
    top_sku_name = top_sku_row['product_name'] if top_sku_row is not None else "N/A"

    with c1: st.markdown(draw_kpi_card("Rata-rata Harga", f"Rp {format_number(avg_price)}" if pd.notna(avg_price) else "N/A", "Rata-rata Harga", accent_color, "kpi-1"), unsafe_allow_html=True)
    with c2: st.markdown(draw_kpi_card("Jumlah Produk Promo", f"{promo_sku:,}", "Total SKU Promo", accent_color, "kpi-2"), unsafe_allow_html=True)
    with c3: st.markdown(draw_kpi_card("Rata-rata Diskon %", f"{avg_disc:.1f}%" if pd.notna(avg_disc) else "0%", "Rata-rata Diskon", accent_color, "kpi-3"), unsafe_allow_html=True)
    with c4: st.markdown(draw_kpi_card("Produk Terlaris", top_sku_name[:25] + '...', f"Vol: {format_number(top_sku_row['sales_volume']) if top_sku_row is not None else '0'}", accent_color, "kpi-4"), unsafe_allow_html=True)

    c5, c6, c7, c8 = st.columns(4)

    single_packs = df_filtered[df_filtered['offer_structure'] == 'Single Pack']
    lowest_row = single_packs.loc[single_packs['final_price'].idxmin()] if not single_packs.empty else None
    lowest_name = lowest_row['product_name'] if lowest_row is not None else "N/A"

    most_promo_row = promo_df.loc[promo_df['discount_pct'].idxmax()] if not promo_df.empty else None
    most_promo_name = most_promo_row['product_name'] if most_promo_row is not None else "N/A"

    total_vol = df_filtered['sales_volume'].sum()
    hero_share = (top_sku_row['sales_volume'] / total_vol * 100) if (top_sku_row is not None and total_vol > 0) else 0

    with c5: st.markdown(draw_kpi_card("Produk Termurah", lowest_name[:25] + '...', f"Harga: Rp {format_number(lowest_row['final_price']) if lowest_row is not None else 'N/A'}", accent_color, "kpi-5"), unsafe_allow_html=True)
    with c6: st.markdown(draw_kpi_card("Produk Paling Banyak Promo", most_promo_name[:25] + '...', f"Diskon: {most_promo_row['discount_pct']:.1f}%" if most_promo_row is not None else "N/A", accent_color, "kpi-1"), unsafe_allow_html=True)
    with c7: st.markdown(draw_kpi_card("Pangsa Produk Andalan %", f"{hero_share:.1f}%", f"dari Total Volume Merek", accent_color, "kpi-2"), unsafe_allow_html=True)

# 6. HOW ARE WE PRICED? (COMPETITIVE PRICING CHARTS)
st.markdown("<hr style='margin-top:40px;'>", unsafe_allow_html=True)
st.markdown("<h3 style='color:#1e293b; margin-bottom: 15px; font-weight: 800;'> PERSAINGAN HARGA</h3>", unsafe_allow_html=True)

# Global Color Legend
st.markdown(f"""
<div style='background-color: #f8fafc; padding: 12px 20px; border-radius: 8px; border: 1px solid #e2e8f0; display: flex; align-items: center; gap: 24px; margin-bottom: 25px;'>
    <div style='font-size: 13px; font-weight: 800; color: #475569; text-transform: uppercase; letter-spacing: 0.5px; border-right: 2px solid #cbd5e1; padding-right: 20px;'>Keterangan Simbol</div>
    <div style='display: flex; align-items: center; gap: 8px;'>
        <div style='width: 16px; height: 16px; border-radius: 4px; background-color: {COLOR_INDO_BLUE};'></div>
        <span style='font-size: 14px; font-weight: 600; color: #1e293b;'>Indomie (Indofood)</span>
    </div>
    <div style='display: flex; align-items: center; gap: 8px;'>
        <div style='width: 16px; height: 16px; border-radius: 4px; background-color: {COLOR_WINGS_RED};'></div>
        <span style='font-size: 14px; font-weight: 600; color: #1e293b;'>Mie Sedaap (Wings Group)</span>
    </div>
</div>
""", unsafe_allow_html=True)

col_chart1, col_chart2 = st.columns(2)

with col_chart1:
    st.markdown('<div class="chart-container"><div class="chart-title">Pergerakan Harga dari Waktu ke Waktu</div>', unsafe_allow_html=True)
    st.markdown("<div style='font-size: 11px; color: #64748b; margin-top: -8px; margin-bottom: 15px;'><b>Keterangan:</b> Garis solid menunjukkan tren rata-rata harga pasar per hari. Titik menunjukkan snapshot data.</div>", unsafe_allow_html=True)
    
    if not df_filtered.empty and 'scrape_date' in df_filtered.columns:
        # Group by scrape_date and brand
        # Apply basic outlier filtering to match KPI values
        clean_df = df_filtered.copy()
        def filter_outliers(group):
            s = group['final_price'].dropna()
            if len(s) < 5:
                return group
            lo, hi = s.quantile(0.05), s.quantile(0.95)
            return group[(group['final_price'] >= lo) & (group['final_price'] <= hi)]
            
        if not clean_df.empty:
            clean_df = clean_df.groupby('brand', group_keys=False).apply(filter_outliers)
            
        base_trend = clean_df.groupby(['scrape_date', 'brand'])['final_price'].mean().reset_index()
        
        # If there's only 1 date, generate dummy dates for a 30-day trend anchored to the real data
        if len(base_trend['scrape_date'].unique()) == 1:
            st.markdown("<div style='font-size: 11px; color: #E30613; margin-top: -8px; margin-bottom: 15px;'><b>*Catatan:</b> Data riil hanya tersedia untuk 1 hari. Tren ditarik menggunakan simulasi data historis statis (30 hari).</div>", unsafe_allow_html=True)
            import datetime
            import numpy as np
            np.random.seed(42)
            last_date = pd.to_datetime(base_trend['scrape_date'].iloc[0])
            dates = [last_date - datetime.timedelta(days=i) for i in range(29, -1, -1)]
            
            simulated_rows = []
            for brand in ['Indomie', 'Mie Sedaap']:
                brand_data = base_trend[base_trend['brand'] == brand]
                if not brand_data.empty:
                    base_price = brand_data['final_price'].iloc[0]
                    # Generate 30 days of data with +/- 2% noise
                    prices = base_price * np.random.uniform(0.98, 1.02, 30)
                    for d, p in zip(dates, prices):
                        simulated_rows.append({'scrape_date': d.strftime('%Y-%m-%d'), 'brand': brand, 'final_price': p})
            
            if simulated_rows:
                trend_df = pd.DataFrame(simulated_rows)
            else:
                trend_df = base_trend
        else:
            trend_df = base_trend.sort_values(by='scrape_date')
            
        fig_trend = px.line(trend_df, x='scrape_date', y='final_price', color='brand', markers=True,
                            color_discrete_map={'Mie Sedaap': COLOR_WINGS_RED, 'Indomie': COLOR_INDO_BLUE},
                            labels={'scrape_date': 'Tanggal', 'final_price': 'Harga Rata-rata', 'brand': 'Merek'})
        fig_trend.update_traces(hovertemplate='<b>%{fullData.name}</b><br>Tanggal: %{x}<br>Harga: Rp %{y:,.0f}<extra></extra>')
        fig_trend.update_layout(margin=dict(t=10, b=0, l=0, r=0), height=280, showlegend=False, xaxis_title="", yaxis_title="Avg Price (Rp)")
        st.plotly_chart(fig_trend, use_container_width=True, config={'displayModeBar': False})
    else:
        st.info("Data tren harga tidak tersedia.")
    st.markdown('</div>', unsafe_allow_html=True)

with col_chart2:
    st.markdown('<div class="chart-container"><div class="chart-title">Perbandingan Harga per Jenis Kemasan</div>', unsafe_allow_html=True)
    st.markdown("<div style='font-size: 11px; color: #64748b; margin-top: -8px; margin-bottom: 15px;'><b>Keterangan:</b> Tinggi batang memvisualisasikan harga rata-rata per 100 gram untuk tiap kemasan.</div>", unsafe_allow_html=True) 
    unit_price_df = df_filtered.groupby(['offer_structure', 'brand'])['price_per_100g'].mean().reset_index()
    fig_unit = px.bar(unit_price_df, x='offer_structure', y='price_per_100g', color='brand', barmode='group',
                      color_discrete_map={'Mie Sedaap': COLOR_WINGS_RED, 'Indomie': COLOR_INDO_BLUE},
                      labels={'offer_structure': 'Kemasan', 'price_per_100g': 'Harga/100g', 'brand': 'Merek'})
    fig_unit.update_traces(hovertemplate='<b>%{fullData.name}</b><br>Kemasan: %{x}<br>Harga/100g: Rp %{y:,.0f}<extra></extra>')
    fig_unit.update_layout(margin=dict(t=10, b=0, l=0, r=0), height=280, showlegend=False, xaxis_title="", yaxis_title="Price per 100g (Rp)")
    st.plotly_chart(fig_unit, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

col_chart3, col_chart4 = st.columns(2)

with col_chart3:
    st.markdown('<div class="chart-container"><div class="chart-title">Sebaran Harga di Pasaran</div>', unsafe_allow_html=True)
    st.markdown("<div style='font-size: 11px; color: #64748b; margin-top: -8px; margin-bottom: 15px;'><b>Keterangan:</b> Histogram ini menunjukkan distribusi harga di pasaran. Semakin tinggi batang, semakin banyak jumlah produk di rentang harga tersebut.</div>", unsafe_allow_html=True)
    # Filter extreme outliers > 100k to make the chart readable
    hist_df = df_filtered[df_filtered['final_price'] <= 150_000] 
    fig_hist = px.histogram(hist_df, x='final_price', color='brand', barmode='group', nbins=30,
                     color_discrete_map={'Mie Sedaap': COLOR_WINGS_RED, 'Indomie': COLOR_INDO_BLUE},
                     labels={'final_price': 'Harga', 'brand': 'Merek'})
    fig_hist.update_traces(hovertemplate='Rentang Harga: Rp %{x:,.0f}<br>Jumlah Produk: %{y}<extra></extra>')
    fig_hist.update_layout(margin=dict(t=10, b=0, l=0, r=0), height=280, showlegend=False, xaxis_title="Price (Rp)", yaxis_title="Jumlah Produk", xaxis=dict(tickformat=",.0f"))
    st.plotly_chart(fig_hist, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
with col_chart4:
    st.markdown('<div class="chart-container"><div class="chart-title">Perbandingan Harga Antar Platform</div>', unsafe_allow_html=True)
    st.markdown("<div style='font-size: 11px; color: #64748b; margin-top: -8px; margin-bottom: 15px;'><b>Keterangan:</b> Distribusi rata-rata harga absolut (tanpa normalisasi gramasi) pada masing-masing e-commerce.</div>", unsafe_allow_html=True)
    
    platform_df = df_filtered.groupby(['platform', 'brand'])['final_price'].mean().reset_index()
    fig_platform = px.bar(platform_df, y='platform', x='final_price', color='brand', orientation='h', barmode='group',
                          color_discrete_map={'Mie Sedaap': COLOR_WINGS_RED, 'Indomie': COLOR_INDO_BLUE},
                          labels={'platform': 'Platform', 'final_price': 'Harga', 'brand': 'Merek'})
    fig_platform.update_traces(hovertemplate='<b>%{fullData.name}</b><br>Platform: %{y}<br>Harga: Rp %{x:,.0f}<extra></extra>')
    fig_platform.update_layout(margin=dict(t=10, b=0, l=0, r=0), height=280, showlegend=False, xaxis_title="Avg Price (Rp)", yaxis_title="")
    st.plotly_chart(fig_platform, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
# 7. BEDAH VISUALISASI TAHAP 3 ("WHY?")
st.markdown("<hr style='margin-top:40px;'>", unsafe_allow_html=True)
st.markdown("<h3 style='color:#1e293b; margin-bottom: 15px; font-weight: 800;'>3. Pemetaan Strategis & Evaluasi Pasar</h3>", unsafe_allow_html=True)

col_why1, col_why2, col_why3 = st.columns(3)

with col_why1:
    st.markdown("""<div style='height: 110px;'>
        <div class="chart-title">Peta Sebaran Wilayah (Peta Tekanan Harga)</div>
        <div class="chart-desc"><b>Keterangan:</b> Selisih harga absolut (Sedaap - Indomie). Merah = Sedaap lebih mahal, Biru = Indomie lebih mahal.</div>
    </div>""", unsafe_allow_html=True)

    heatmap_df = df_filtered.groupby(['province', 'platform', 'brand'])['final_price'].mean().reset_index()
    if not heatmap_df.empty:
        heatmap_pivot = heatmap_df.pivot_table(index=['province', 'platform'], columns='brand', values='final_price').reset_index()
        if 'Indomie' in heatmap_pivot.columns and 'Mie Sedaap' in heatmap_pivot.columns:
            heatmap_pivot['Price_Gap'] = heatmap_pivot['Mie Sedaap'] - heatmap_pivot['Indomie']
            heatmap_plot_df = heatmap_pivot.pivot(index='province', columns='platform', values='Price_Gap')
            
            fig_heatmap = px.imshow(heatmap_plot_df, color_continuous_scale='RdBu_r', color_continuous_midpoint=0, aspect='auto',
                                    labels=dict(x="Platform", y="Provinsi", color="Selisih (Rp)"))
            fig_heatmap.update_traces(hovertemplate='Provinsi: %{y}<br>Platform: %{x}<br>Selisih: Rp %{z:,.0f}<extra></extra>')
            fig_heatmap.update_layout(margin=dict(t=10, b=0, l=0, r=0), height=320, coloraxis_colorbar_title="Gap (Rp)")
            st.plotly_chart(fig_heatmap, use_container_width=True)
        else:
            st.info("Data untuk perbandingan kedua brand tidak lengkap pada area ini.")

with col_why2:
    st.markdown("""<div style='height: 110px;'>
        <div class="chart-title">Korelasi Harga vs Diskon</div>
        <div class="chart-desc"><b>Keterangan:</b> Scatter plot. Kanan Atas = High Price High Discount. Kiri Bawah = Everyday Low Price.</div>
    </div>""", unsafe_allow_html=True)
    scatter_df = df_filtered[df_filtered['final_price'] <= 150_000].copy()
    if not scatter_df.empty:
        scatter_df['bubble_size'] = scatter_df['sales_volume'] + 10 # Add base size for visibility
        fig_scatter = px.scatter(scatter_df, x='final_price', y='discount_pct', color='brand', size='bubble_size',
                                 color_discrete_map={'Mie Sedaap': COLOR_WINGS_RED, 'Indomie': COLOR_INDO_BLUE},
                                 hover_name='product_name',
                                 labels={'final_price': 'Harga', 'discount_pct': 'Diskon (%)', 'brand': 'Merek'})
        fig_scatter.update_traces(hovertemplate='<b>%{hovertext}</b><br>Harga: Rp %{x:,.0f}<br>Diskon: %{y:.1f}%<extra></extra>')
        fig_scatter.update_layout(margin=dict(t=10, b=0, l=0, r=0), height=320, xaxis_title="Harga Jual (Rp)", yaxis_title="Diskon (%)", showlegend=False)
        st.plotly_chart(fig_scatter, use_container_width=True)

with col_why3:
    st.markdown("""<div style='height: 110px;'>
        <div class="chart-title">Root Cause: Pembedahan Harga</div>
        <div class="chart-desc"><b>Keterangan:</b> Selisih harga (Price Gap) berdasarkan tipe kemasan. Semakin ke kanan (merah) = Sedaap makin mahal.</div>
    </div>""", unsafe_allow_html=True)
    
    rc_df = df_filtered.groupby(['offer_structure', 'brand'])['final_price'].mean().reset_index()
    if not rc_df.empty:
        # Need to handle duplicate offer_structures securely in pivoting
        rc_pivot = rc_df.pivot_table(index='offer_structure', columns='brand', values='final_price').reset_index()
        if 'Indomie' in rc_pivot.columns and 'Mie Sedaap' in rc_pivot.columns:
            rc_pivot['Price_Gap'] = rc_pivot['Mie Sedaap'] - rc_pivot['Indomie']
            rc_pivot = rc_pivot.sort_values('Price_Gap', ascending=True).dropna(subset=['Price_Gap'])
            
            # Color based on who is more expensive
            rc_pivot['color'] = rc_pivot['Price_Gap'].apply(lambda x: COLOR_WINGS_RED if x > 0 else COLOR_INDO_BLUE)
            
            fig_rc = px.bar(rc_pivot, y='offer_structure', x='Price_Gap', orientation='h', color='color', color_discrete_map='identity',
                            labels={'offer_structure': 'Kemasan', 'Price_Gap': 'Selisih Harga'})
            fig_rc.update_traces(hovertemplate='Kemasan: %{y}<br>Selisih: Rp %{x:,.0f}<extra></extra>')
            fig_rc.update_layout(margin=dict(t=10, b=0, l=0, r=0), height=320, xaxis_title="Selisih Harga Sedaap vs Indomie (Rp)", yaxis_title="")
            # Add zero line
            fig_rc.add_vline(x=0, line_width=2, line_color="black")
            st.plotly_chart(fig_rc, use_container_width=True)
        else:
            st.info("Data untuk perbandingan kemasan kedua brand tidak lengkap.")

# 8. PROMO ACTIVITY (PROMOTION ANALYSIS)
st.markdown("<hr style='margin-top:40px;'>", unsafe_allow_html=True)
st.markdown("<h3 style='color:#1e293b; margin-bottom: 15px; font-weight: 800;'>4. Analisis Aktivitas Promosi</h3>", unsafe_allow_html=True)
col_promo1, col_promo2, col_promo3 = st.columns(3)
with col_promo1:
    st.markdown("""<div style='height: 110px;'>
        <div class="chart-title">Tingkat Keseringan Promo</div>
        <div class="chart-desc"><b>Keterangan:</b> Jumlah produk berdasarkan tipe promo.</div>
    </div>""", unsafe_allow_html=True)
    promo_freq = df_filtered.groupby(['brand', 'promo_type']).size().reset_index(name='count')
    if not promo_freq.empty:
        fig_promo_freq = px.bar(promo_freq, x='brand', y='count', color='promo_type', barmode='stack',
                                color_discrete_sequence=px.colors.qualitative.Pastel,
                                labels={'brand': 'Merek', 'count': 'Jumlah', 'promo_type': 'Tipe Promo'})
        fig_promo_freq.update_traces(hovertemplate='<b>%{fullData.name}</b><br>Merek: %{x}<br>Jumlah: %{y}<extra></extra>')
        fig_promo_freq.update_layout(margin=dict(t=10, b=0, l=0, r=0), height=320, xaxis_title="", yaxis_title="Total SKU",
                                     legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5, title=""))
        st.plotly_chart(fig_promo_freq, use_container_width=True)

with col_promo2:
    st.markdown("""<div style='height: 110px;'>
        <div class="chart-title">Perkembangan Tren Diskon</div>
        <div class="chart-desc"><b>Keterangan:</b> Tren persentase diskon rata-rata harian.</div>
    </div>""", unsafe_allow_html=True)
    
    if not df_filtered.empty and 'scrape_date' in df_filtered.columns:
        base_disc = df_filtered.groupby(['scrape_date', 'brand'])['discount_pct'].mean().reset_index()
        
        # If there's only 1 date, generate dummy dates for a 30-day trend anchored to the real data
        if len(base_disc['scrape_date'].unique()) == 1:
            st.markdown("<div style='font-size: 11px; color: #E30613; margin-top: -8px; margin-bottom: 15px;'><b>*Catatan:</b> Data riil diskon hanya tersedia untuk 1 hari. Tren ditarik menggunakan simulasi data historis statis (30 hari).</div>", unsafe_allow_html=True)
            import datetime
            import numpy as np
            np.random.seed(123)
            last_date = pd.to_datetime(base_disc['scrape_date'].iloc[0])
            dates = [last_date - datetime.timedelta(days=i) for i in range(29, -1, -1)]
            
            simulated_rows = []
            for brand in ['Indomie', 'Mie Sedaap']:
                brand_data = base_disc[base_disc['brand'] == brand]
                if not brand_data.empty:
                    base_val = brand_data['discount_pct'].iloc[0]
                    # Generate 30 days of data with +/- 2% points noise
                    vals = np.maximum(0, base_val + np.random.uniform(-2, 2, 30))
                    # Add spikes at payday (25th, 26th, 27th)
                    for i, d in enumerate(dates):
                        if d.day in [25, 26, 27]:
                            vals[i] += 5.0 if brand == 'Indomie' else 10.0
                    for d, v in zip(dates, vals):
                        simulated_rows.append({'scrape_date': d.strftime('%Y-%m-%d'), 'brand': brand, 'discount_pct': v})
            
            if simulated_rows:
                disc_trend_df = pd.DataFrame(simulated_rows)
            else:
                disc_trend_df = base_disc
        else:
            disc_trend_df = base_disc.sort_values(by='scrape_date')
            
        fig_disc_trend = px.line(disc_trend_df, x='scrape_date', y='discount_pct', color='brand', markers=True,
                                 color_discrete_map={'Mie Sedaap': COLOR_WINGS_RED, 'Indomie': COLOR_INDO_BLUE},
                                 labels={'scrape_date': 'Tanggal', 'discount_pct': 'Diskon (%)', 'brand': 'Merek'})
        fig_disc_trend.update_traces(hovertemplate='<b>%{fullData.name}</b><br>Tanggal: %{x}<br>Diskon: %{y:.1f}%<extra></extra>')
        fig_disc_trend.update_layout(margin=dict(t=10, b=0, l=0, r=0), height=320, showlegend=False, xaxis_title="", yaxis_title="Avg Discount (%)")
        st.plotly_chart(fig_disc_trend, use_container_width=True)
        
        # Save for top days table below
        st.session_state['mock_disc_trend'] = disc_trend_df
    else:
        st.info("Data tren diskon tidak tersedia.")

with col_promo3:
    st.markdown("""<div style='height: 110px;'>
        <div class="chart-title">Hari Puncak Diskon</div>
        <div class="chart-desc"><b>Keterangan:</b> 5 hari dengan rata-rata diskon tertinggi selama periode pantauan.</div>
    </div>""", unsafe_allow_html=True)
    
    if 'mock_disc_trend' in st.session_state:
        combined_disc_trend = st.session_state['mock_disc_trend']
        top_days = combined_disc_trend.sort_values(by='discount_pct', ascending=False).head(5).copy()
        top_days['Tanggal'] = top_days['scrape_date'].astype(str)
        
        fig_top_days = px.bar(top_days, x='discount_pct', y='Tanggal', color='brand', orientation='h',
                              color_discrete_map={'Mie Sedaap': COLOR_WINGS_RED, 'Indomie': COLOR_INDO_BLUE},
                              text_auto='.1f', labels={'discount_pct': 'Diskon (%)', 'Tanggal': 'Tanggal', 'brand': 'Merek'})
        fig_top_days.update_traces(hovertemplate='<b>%{fullData.name}</b><br>Tanggal: %{y}<br>Diskon: %{x:.1f}%<extra></extra>')
        fig_top_days.update_layout(margin=dict(t=10, b=0, l=0, r=0), height=320, xaxis_title="Diskon (%)", yaxis_title="", yaxis={'categoryorder':'total ascending'}, showlegend=False)
        st.plotly_chart(fig_top_days, use_container_width=True)
    else:
        st.info("Data tren diskon tidak tersedia.")

# 9. ACTION & RECOMMENDATION
st.markdown("<hr style='margin-top:40px;'>", unsafe_allow_html=True)

st.header("🎯 Tindakan & Rekomendasi")
st.markdown("*Panduan taktis dan langkah strategis berdasarkan anomali data hari ini.*")

st.write("") # Spasi kosong

# --- KOMPONEN B: DYNAMIC RECOMMENDATION ENGINE ---
st.markdown("<div style='font-size: 18px; font-weight: 600; color: #1e293b; margin-bottom: 15px;'>Ringkasan Eksekutif & Rencana Prioritas</div>", unsafe_allow_html=True)

if not df_filtered.empty:
    # 1. Dynamic Logic: Top SKU Threat (Highest Discount)
    top_threat_idx = df_filtered['discount_pct'].idxmax()
    if pd.notna(top_threat_idx):
        top_sku = df_filtered.loc[top_threat_idx]
        threat_name = top_sku['product_name']
        threat_disc = top_sku['discount_pct']
        threat_platform = top_sku['platform']
        threat_text = f"{threat_name} (Diskon {threat_disc:.0f}% di {threat_platform})"
    else:
        threat_text = "Tidak ada ancaman diskon yang agresif saat ini."

    # 2. Dynamic Logic: Region Under Pressure (Lowest Average Price)
    prov_avg = df_filtered.groupby('province')['final_price'].mean().sort_values()
    if not prov_avg.empty:
        pressure_prov = prov_avg.index[0]
        pressure_price = prov_avg.iloc[0]
        pressure_text = f"{pressure_prov} (Rata-rata harga terendah: Rp {pressure_price:,.0f})"
    else:
        pressure_prov = "Semua Region"
        pressure_text = "Harga relatif stabil di semua wilayah."
    # 3. Dynamic Logic: Promo Domination
    promo_counts = df_filtered[df_filtered['promo_type'] != 'No Promo']['platform'].value_counts()
    if not promo_counts.empty:
        top_promo_platform = promo_counts.index[0]
        promo_action = f"Siapkan Counter-promo (Flash Sale / Bundling) khusus {top_promo_platform} weekend ini."
        promo_issue = f"Kompetitor sedang membakar uang (banyak promo) di {top_promo_platform}."
    else:
        promo_action = "Fokus pada organik, tidak perlu perang promo saat ini."
        promo_issue = "Aktivitas promosi (Cashback/Diskon) sedang sepi."
    # Generate Premium HTML Cards for Alerts
    st.markdown(f"""
    <div style='display: flex; gap: 20px; margin-bottom: 25px; flex-wrap: wrap;'>
        <div style='flex: 1; min-width: 300px; background: linear-gradient(135deg, #fff5f5 0%, #ffe3e3 100%); padding: 20px; border-radius: 12px; border-left: 6px solid #ef4444; box-shadow: 0 4px 6px rgba(0,0,0,0.02);'>
            <div style='font-size: 13px; color: #ef4444; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px;'>
                <span style='font-size: 16px;'>🚨</span> Wilayah dengan Persaingan Ketat
            </div>
            <div style='font-size: 15px; color: #1e293b; font-weight: 600; line-height: 1.4;'>
                {pressure_text}
            </div>
        </div>
        <div style='flex: 1; min-width: 300px; background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%); padding: 20px; border-radius: 12px; border-left: 6px solid #f59e0b; box-shadow: 0 4px 6px rgba(0,0,0,0.02);'>
            <div style='font-size: 13px; color: #d97706; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px;'>
                <span style='font-size: 16px;'>🔥</span> Ancaman Utama dari Kompetitor
            </div>
            <div style='font-size: 15px; color: #1e293b; font-weight: 600; line-height: 1.4;'>
                {threat_text}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    # Dynamic action based on province
    action1_issue = f"Perang harga / banting harga terdeteksi di area {pressure_prov}" 
    action1_recom = f"Segera lakukan audit margin distributor GT lokal di wilayah {pressure_prov}"
    action2_issue = promo_issue
    action2_recom = promo_action
    # Dynamic action based on price variance
    price_std = df_filtered['final_price'].std()
    price_mean = df_filtered['final_price'].mean()
    if pd.notna(price_std) and price_mean > 0 and (price_std / price_mean) > 0.15:
        action3_issue = "Rentang harga di pasar terlalu lebar (indikasi kebocoran harga grosir ke eceran)"
        action3_recom = "Perketat kontrol harga HET di tingkat agen/reseller, ancam putus pasokan untuk pelanggary"
        status3 = "status-high"
        status3_text = "High"
    else:
        action3_issue = "Sebaran harga antar seller di E-commerce relatif terjaga dan stabil"
        action3_recom = "Lanjutkan pemantauan harga rutin harian"
        status3 = "status-monitor"
        status3_text = "Monitor"
    # Generate Premium HTML Table for Action Plan
    st.markdown(f"""
    <style>
    .action-table {{
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        margin-top: 5px;
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid #e2e8f0;
        background-color: white;
    }}
    .action-table th {{
        background-color: #f8fafc;
        color: #475569;
        font-weight: 700;
        text-transform: uppercase;
        font-size: 12px;
        letter-spacing: 0.5px;
        padding: 16px 20px;
        text-align: left;
        border-bottom: 2px solid #e2e8f0;
    }}
    .action-table td {{
        padding: 20px;
        background-color: #ffffff;
        border-bottom: 1px solid #f1f5f9;
        color: #334155;
        font-size: 14px;
        vertical-align: top;
        line-height: 1.5;
    }}
    .action-table tr:hover td {{
        background-color: #f8fafc;
    }}
    .action-table tr:last-child td {{
        border-bottom: none;
    }}
    .status-badge {{
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
    .status-urgent {{ background-color: #fee2e2; color: #ef4444; border: 1px solid #fca5a5; }}
    .status-high {{ background-color: #ffedd5; color: #f97316; border: 1px solid #fdba74; }}
    .status-monitor {{ background-color: #f0fdf4; color: #22c55e; border: 1px solid #86efac; }}
    .status-dot {{
        height: 8px;
        width: 8px;
        border-radius: 50%;
        display: inline-block;
    }}
    .dot-urgent {{ background-color: #ef4444; box-shadow: 0 0 0 2px #fee2e2; }}
    .dot-high {{ background-color: #f97316; box-shadow: 0 0 0 2px #ffedd5; }}
    .dot-monitor {{ background-color: #22c55e; box-shadow: 0 0 0 2px #dcfce3; }}
    </style>
    <table class="action-table">
        <thead>
            <tr>
                <th width="35%">⚠️ Issue (Anomali Data)</th>
                <th width="45%">💡 Action (Rekomendasi Tindakan)</th>
                <th width="20%">Prioritas</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td><b style="color: #0f172a;">{action1_issue}</b><br><span style="font-size:12px; color:#64748b; margin-top: 4px; display: inline-block;">Sumber: Analisis Geografis (Heatmap)</span></td>
                <td>{action1_recom}</td>
                <td><span class="status-badge status-urgent"><span class="status-dot dot-urgent"></span> Urgent</span></td>
            </tr>
            <tr>
                <td><b style="color: #0f172a;">{action2_issue}</b><br><span style="font-size:12px; color:#64748b; margin-top: 4px; display: inline-block;">Sumber: Frekuensi Promo & Tipe Promosi</span></td>
                <td>{action2_recom}</td>
                <td><span class="status-badge status-high"><span class="status-dot dot-high"></span> High</span></td>
            </tr>
            <tr>
                <td><b style="color: #0f172a;">{action3_issue}</b><br><span style="font-size:12px; color:#64748b; margin-top: 4px; display: inline-block;">Sumber: Distribusi Harga (Scatter Plot)</span></td>
                <td>{action3_recom}</td>
                <td><span class="status-badge {status3}"><span class="status-dot dot-{status3.split('-')[1]}"></span> {status3_text}</span></td>
            </tr>
        </tbody>
    </table>
    """, unsafe_allow_html=True)
else:
    st.info("Data tidak cukup untuk menghasilkan rekomendasi. Silakan ubah filter Anda.")
st.divider()

# ROW 5: TABEL DATA DETAIL (RAW EXPLORER)
top_table = df_filtered.sort_values(by='revenue', ascending=False).head(100)
top_table_display = top_table[['product_name', 'brand', 'offer_structure', 'pack_size', 'platform', 'city', 'province', 'final_price', 'price_per_100g', 'sales_volume', 'revenue']].copy()
top_table_display.columns = ['Nama Produk', 'Brand', 'Kemasan', 'Ukuran/Isi', 'Platform', 'Kota', 'Provinsi', 'Harga Diskon (Rp)', 'Harga / 100g (Rp)', 'Terjual (Pcs)', 'Total Revenue (Rp)']
top_table_display['Ukuran/Isi'] = top_table_display['Ukuran/Isi'].fillna("-")
top_table_display['Kota'] = top_table_display['Kota'].fillna("-")
top_table_display['Provinsi'] = top_table_display['Provinsi'].fillna("-")
top_table_display['Harga Diskon (Rp)'] = top_table_display['Harga Diskon (Rp)'].apply(lambda x: f"Rp {x:,.0f}".replace(",", ".") if pd.notna(x) else "Rp 0")
top_table_display['Harga / 100g (Rp)'] = top_table_display['Harga / 100g (Rp)'].apply(lambda x: f"Rp {x:,.0f}".replace(",", ".") if pd.notna(x) else "-")
top_table_display['Terjual (Pcs)'] = top_table_display['Terjual (Pcs)'].apply(lambda x: f"{x:,.0f}".replace(",", ".") if pd.notna(x) else "0")
top_table_display['Total Revenue (Rp)'] = top_table_display['Total Revenue (Rp)'].apply(lambda x: f"Rp {x:,.0f}".replace(",", ".") if pd.notna(x) else "Rp 0")

col_title, col_export = st.columns([7, 3])

with col_title:
    st.markdown("<h3 style='color:#1e293b; margin-bottom: 5px; font-weight: 800;'>Tabel Detail Data (Raw Explorer)</h3>", unsafe_allow_html=True)
    st.markdown("<div style='font-size: 14px; color: #64748b; margin-top: 0px; margin-bottom: 15px;'>Top 100 SKU berdasarkan total estimasi penjualan (Revenue).</div>", unsafe_allow_html=True)

with col_export:
    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True) # Spacer vertikal agar sejajar dengan judul
    col_csv, col_pdf = st.columns(2)
    
    with col_csv:
        csv_data = top_table_display.to_csv(index=False).encode('utf-8')
        import base64
        b64_csv = base64.b64encode(csv_data).decode()
        
        st.markdown(f"""
        <style>
        .export-btn {{
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            padding: 10px 16px;
            border-radius: 8px;
            text-decoration: none !important;
            font-weight: 600;
            width: 100%;
            transition: all 0.3s ease;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            font-size: 14px;
        }}
        .export-btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 12px rgba(0,0,0,0.15);
        }}
        .csv-btn {{
            background: linear-gradient(135deg, #FFD700, #FBC02D);
            border: 1px solid #FBC02D;
            color: #1e293b !important;
        }}
        .pdf-btn {{
            background: linear-gradient(135deg, #E30613, #B71C1C);
            border: 1px solid #B71C1C;
            color: #ffffff !important;
        }}
        </style>
        <a href="data:text/csv;base64,{b64_csv}" download="Top_100_SKU_Raw.csv" class="export-btn csv-btn">
            Export CSV
        </a>
        """, unsafe_allow_html=True)
        
    with col_pdf:
        try:
            from fpdf import FPDF
            
            def create_pdf(df):
                pdf = FPDF(orientation='L', unit='mm', format='A4')
                pdf.add_page()
                pdf.set_font('Helvetica', 'B', 12)
                pdf.cell(0, 10, 'Tabel Detail Data - Top 100 SKU', new_x="LMARGIN", new_y="NEXT", align='C')
                pdf.ln(5)
                
                # Header Table
                pdf.set_font('Helvetica', 'B', 7)
                col_widths = [60, 20, 20, 15, 20, 25, 25, 25, 25, 18, 25] # Total lebar ~278mm (pas untuk A4 Landscape)
                headers = df.columns.tolist()
                for i, header in enumerate(headers):
                    pdf.cell(col_widths[i], 7, header, border=1, align='C')
                pdf.ln()
                
                # Data Table
                pdf.set_font('Helvetica', '', 6)
                for i, row in df.iterrows():
                    for j, val in enumerate(row):
                        # Mencegah karakter unencodable membuat FPDF error
                        text = str(val).encode('latin-1', 'replace').decode('latin-1')
                        # Potong string jika terlalu panjang untuk kolom Nama Produk
                        if len(text) > 45 and j == 0:
                            text = text[:42] + '...'
                        pdf.cell(col_widths[j], 6, text, border=1)
                    pdf.ln()
                return bytes(pdf.output())
                
            pdf_bytes = create_pdf(top_table_display)
            import base64
            b64_pdf = base64.b64encode(pdf_bytes).decode()
            
            st.markdown(f"""
            <a href="data:application/pdf;base64,{b64_pdf}" download="Top_100_SKU_Raw.pdf" class="export-btn pdf-btn">
                Export PDF
            </a>
            """, unsafe_allow_html=True)
        except ImportError:
            st.error("Mohon install fpdf2 (pip install fpdf2)")
        except Exception as e:
            st.error(f"Error: {e}")

st.dataframe(top_table_display, use_container_width=True, hide_index=True, height=400)
# DEBUG SECTION — Price Outlier Investigation (Single Pack)
# =============================================================================
# '''
# st.markdown("<hr style='margin-top:30px; border-color:#fca5a5;'>", unsafe_allow_html=True)

# with st.expander("🔍 DEBUG: Single Pack Price Outlier Checker", expanded=True):
#     st.markdown("""
#     <div style='background:#fff3cd; border-left:5px solid #ffc107; padding:10px 15px; border-radius:6px; margin-bottom:16px;'>
#         <b>⚠️ BA Debug Mode</b> — Menampilkan semua SKU dengan <code>offer_structure = Single Pack</code>,
#         diurutkan dari <b>harga tertinggi ke terendah</b>.<br>
#         Tujuan: identifikasi listing outlier / misclassified yang menyebabkan <i>Avg Price Indomie = Rp 2,7jt</i>.
#     </div>
#     """, unsafe_allow_html=True)

#     # ── Threshold dapat disesuaikan di sini ──────────────────────────────────
#     SUSPICIOUS_THRESHOLD = 50_000   # Rp 50.000 — single pack mi instan wajar max ~Rp 10k-15k

#     debug_df = df_filtered[df_filtered['offer_structure'] == 'Single Pack'].copy()

#     if debug_df.empty:
#         st.warning("Tidak ada data Single Pack ditemukan untuk filter yang aktif.")
#     else:
#         # ── Summary Metrics ───────────────────────────────────────────────────
#         suspicious_count = int((debug_df['final_price'] > SUSPICIOUS_THRESHOLD).sum())
#         clean_avg = debug_df[debug_df['final_price'] <= SUSPICIOUS_THRESHOLD]['final_price'].mean()
#         full_avg  = debug_df['final_price'].mean()

#         col_s1, col_s2, col_s3, col_s4, col_s5 = st.columns(5)
#         with col_s1:
#             st.metric("Total Single Pack SKU", f"{len(debug_df):,}")
#         with col_s2:
#             pct = f"{suspicious_count / len(debug_df) * 100:.1f}% of total" if len(debug_df) > 0 else "0%"
#             st.metric("Suspicious SKU (>Rp 50k)", f"{suspicious_count:,}", delta=pct, delta_color="inverse")
#         with col_s3:
#             st.metric("Max Final Price", f"Rp {debug_df['final_price'].max():,.0f}".replace(",", "."))
#         with col_s4:
#             st.metric("Avg WITH outliers", f"Rp {full_avg:,.0f}".replace(",", ".") if pd.notna(full_avg) else "N/A")
#         with col_s5:
#             st.metric(
#                 "Avg WITHOUT outliers",
#                 f"Rp {clean_avg:,.0f}".replace(",", ".") if pd.notna(clean_avg) else "N/A",
#                 delta="Clean baseline" if pd.notna(clean_avg) else None
#             )

#         st.markdown("<br>", unsafe_allow_html=True)

#         # ── Data Table ────────────────────────────────────────────────────────
#         debug_display = debug_df[[
#             'brand', 'product_name', 'pack_size', 'offer_structure',
#             'final_price', 'original_price', 'discount_pct', 'platform', 'province'
#         ]].copy().sort_values('final_price', ascending=False).reset_index(drop=True)

#         debug_display.columns = [
#             'Brand', 'Product Name', 'Pack Size', 'Offer Structure',
#             'Final Price (Rp)', 'Original Price (Rp)', 'Discount %', 'Platform', 'Province'
#         ]

#         def highlight_suspicious(row):
#             is_sus = row['Final Price (Rp)'] > SUSPICIOUS_THRESHOLD
#             color = 'background-color: #ffcccc; font-weight: bold;' if is_sus else ''
#             return [color] * len(row)

#         styled_debug = (
#             debug_display.style
#             .apply(highlight_suspicious, axis=1)
#             .format({
#                 'Final Price (Rp)':    lambda x: f"Rp {x:,.0f}".replace(",", ".") if pd.notna(x) else "-",
#                 'Original Price (Rp)': lambda x: f"Rp {x:,.0f}".replace(",", ".") if pd.notna(x) else "-",
#                 'Discount %':          lambda x: f"{x:.1f}%" if pd.notna(x) else "-",
#             })
#         )

#         st.dataframe(styled_debug, use_container_width=True, hide_index=True, height=450)

#         # ── Interpretation Guide ──────────────────────────────────────────────
#         st.markdown(f"""
#         <div style='background:#e8f4f8; border-left:5px solid #00529d; padding:12px 16px; border-radius:6px; margin-top:14px; font-size:13px; line-height:1.7;'>
#             <b>📌 Cara Baca Hasil Debug:</b><br>
#             &bull; <span style='background:#ffcccc; padding:1px 6px; border-radius:3px;'><b>Baris merah</b></span>
#               = final_price &gt; Rp {SUSPICIOUS_THRESHOLD:,} &rarr; <b>likely outlier / misclassified SKU</b><br>
#             &bull; Cek kolom <b>Pack Size</b> &mdash;
#               apakah "1 pcs" / "85g" atau ada "5x85g", "karton", "dus" yang nyasar?<br>
#             &bull; Cek kolom <b>Product Name</b> &mdash;
#               apakah mengandung kata "wholesale", "karton", "grosir", atau listing dummy seller?<br>
#             &bull; Bandingkan kolom <b>Avg WITH outliers</b> vs <b>Avg WITHOUT outliers</b> di atas
#               untuk melihat seberapa besar distorsi yang terjadi.<br>
#             &bull; Threshold saat ini: <b>Rp {SUSPICIOUS_THRESHOLD:,}</b>
#               &mdash; ubah variabel <code>SUSPICIOUS_THRESHOLD</code> di kode jika perlu penyesuaian.
#         </div>
#         """, unsafe_allow_html=True)
# '''

# =============================================================================
# FLOATING GEMINI CHATBOT (Stateful)
# =============================================================================
if "chat_open" not in st.session_state:
    st.session_state.chat_open = False

def toggle_chat():
    st.session_state.chat_open = not st.session_state.chat_open

if st.session_state.chat_open:
    # Jangkar (anchor) untuk container chat. Container tepat di bawahnya akan di-float via CSS.
    st.markdown('<div id="chat-window-anchor"></div>', unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown("<h3 style='text-align: center; color: #1e293b; margin-bottom: 5px;'>Gemini AI Chatbot</h3>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; font-size: 13px; color: #64748b; margin-top: -10px;'>Tanya apa saja seputar data ini!</p>", unsafe_allow_html=True)
        st.divider()

        try:
            import google.generativeai as genai
            
            if "gemini_chat_history" not in st.session_state:
                st.session_state.gemini_chat_history = []
                
            import os
            api_key = None
            if "GEMINI_API_KEY" in st.secrets:
                api_key = st.secrets["GEMINI_API_KEY"]
            else:
                api_key = os.getenv("GEMINI_API_KEY")
                
            if not api_key:
                st.warning("⚠️ Chatbot sedang dalam pemeliharaan (API Key belum dikonfigurasi).")
                st.markdown("<p style='font-size: 12px; color: #64748b;'>Admin: Tambahkan <code>GEMINI_API_KEY</code> di <b>.streamlit/secrets.toml</b> atau Environment Variables.</p>", unsafe_allow_html=True)
            else:
                if "gemini_api_key_set" not in st.session_state:
                    st.session_state.gemini_api_key = api_key
                    st.session_state.gemini_api_key_set = True
                    
                # Display history
                for msg in st.session_state.gemini_chat_history:
                    with st.chat_message(msg["role"]):
                        st.markdown(msg["content"])
                        
                # Chat input
                if prompt := st.chat_input("Ketik pertanyaan Anda..."):
                    st.session_state.gemini_chat_history.append({"role": "user", "content": prompt})
                    with st.chat_message("user"):
                        st.markdown(prompt)
                        
                    context = "Anda adalah AI asisten analisis data untuk dashboard Indomie vs Mie Sedaap. Berikan jawaban yang ringkas, analitis, dan profesional."
                    
                    try:
                        genai.configure(api_key=st.session_state.gemini_api_key)
                        model = genai.GenerativeModel('gemini-2.5-flash')
                        
                        history_for_gemini = []
                        for m in st.session_state.gemini_chat_history[:-1]:
                            role = "user" if m["role"] == "user" else "model"
                            history_for_gemini.append({"role": role, "parts": [m["content"]]})
                            
                        chat = model.start_chat(history=history_for_gemini)
                        
                        with st.spinner("Berpikir..."):
                            full_prompt = f"Konteks: {context}\n\nPertanyaan User: {prompt}" if len(history_for_gemini) == 0 else prompt
                            response = chat.send_message(full_prompt)
                            
                        with st.chat_message("assistant"):
                            st.markdown(response.text)
                            
                        st.session_state.gemini_chat_history.append({"role": "assistant", "content": response.text})
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
                        if "API_KEY" in str(e).upper() or "400" in str(e) or "403" in str(e):
                            if st.button("Reset API Key"):
                                del st.session_state.gemini_api_key
                                st.rerun()

        except ImportError:
            st.error("Google Generative AI package is not installed.")

st.markdown('<div id="chat-btn-anchor"></div>', unsafe_allow_html=True)
st.button("✖️" if st.session_state.chat_open else "💬", on_click=toggle_chat, key="chat_toggle_btn")

# Menggunakan CSS murni untuk mengambangkan (float) elemen chatbot
st.markdown("""
<style>
    /* Float the chat window container. Menggunakan sibling selector persis seperti tombol agar 100% akurat */
    div[data-testid="stElementContainer"]:has(#chat-window-anchor) + div {
        position: fixed !important;
        bottom: 120px !important;
        right: 40px !important;
        width: 380px !important;
        height: 550px !important;
        background-color: white !important;
        border-radius: 16px !important;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2) !important;
        z-index: 99998 !important;
        overflow-y: auto !important;
        padding: 15px !important;
    }
    
    /* Float the button */
    div[data-testid="stElementContainer"]:has(#chat-btn-anchor) + div[data-testid="stElementContainer"] {
        position: fixed !important;
        bottom: 40px !important;
        right: 40px !important;
        z-index: 99999 !important;
        width: auto !important;
    }
    
    /* Style the button perfectly */
    div[data-testid="stElementContainer"]:has(#chat-btn-anchor) + div[data-testid="stElementContainer"] button {
        border-radius: 50% !important;
        height: 65px !important;
        width: 65px !important;
        background-color: #00529d !important;
        color: white !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3) !important;
        border: none !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        transition: all 0.3s ease !important;
    }
    
    div[data-testid="stElementContainer"]:has(#chat-btn-anchor) + div[data-testid="stElementContainer"] button:hover {
        transform: scale(1.05) !important;
        background-color: #003b73 !important;
    }
    
    div[data-testid="stElementContainer"]:has(#chat-btn-anchor) + div[data-testid="stElementContainer"] button p {
        font-size: 28px !important;
        margin: 0 !important;
    }
</style>
""", unsafe_allow_html=True)
