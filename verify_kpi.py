"""Verification script: simulates exactly what dashboard.py does after the fix."""
import pandas as pd
import re

cols=['scrape_date','company','brand','product_name','sku_id','pack_size',
      'original_price','final_price','discount_pct','retailer','platform',
      'province','city','promo_type','promo_text','variant','flavor',
      'offer_structure','promo_start','promo_end','sales_volume']

df = pd.read_csv('final_normalized_data.csv', header=None, names=cols, na_values=['NULL'])
df['final_price'] = pd.to_numeric(df['final_price'], errors='coerce')

BRAND_AVG_WEIGHT = {'Mie Sedaap': 82, 'Indomie': 80}

def extract_total_weight(row):
    ps = row.get('pack_size', None)
    brand = row.get('brand', None)
    if pd.isna(ps): return None
    ps_str = str(ps).lower()
    m = re.match(r'(\d+)\s*x\s*(\d+)g', ps_str)
    if m: return int(m.group(1)) * int(m.group(2))
    m2 = re.match(r'^(\d+)g$', ps_str)
    if m2: return int(m2.group(1))
    m3 = re.match(r'(\d+)\s*pcs', ps_str)
    if m3:
        qty = int(m3.group(1))
        return qty * BRAND_AVG_WEIGHT.get(brand, 81)
    return None

df['total_weight_g'] = df.apply(extract_total_weight, axis=1)
df['price_per_100g'] = (df['final_price'] / df['total_weight_g']) * 100

def validate_price_per_unit(row):
    price = row['final_price']
    weight = row['total_weight_g']
    pack_type = row['offer_structure']
    suspicious = False
    if pd.notna(weight) and weight > 0:
        p100g = (price / weight) * 100
        if p100g > 25000 or p100g < 300:
            suspicious = True
    if pack_type == 'Single Pack' and price > 25000:
        suspicious = True
    return suspicious

df['price_flag'] = df.apply(validate_price_per_unit, axis=1)
df = df[~df['price_flag']].copy()

def clean_prices(series, low_pct=0.05, high_pct=0.95):
    s = series.dropna()
    if s.empty: return s
    lo, hi = s.quantile(low_pct), s.quantile(high_pct)
    return s[(s >= lo) & (s <= hi)]

print("=" * 60)
print("SKENARIO 1: Hanya Single Pack")
print("=" * 60)
sp = df[df['offer_structure'] == 'Single Pack']
for brand in ['Mie Sedaap', 'Indomie']:
    b = clean_prices(sp[sp['brand'] == brand]['price_per_100g'])
    print(f"  {brand}: median p100g = Rp {b.median():.0f}, count = {len(b)}")
sed_sp = clean_prices(sp[sp['brand'] == 'Mie Sedaap']['price_per_100g']).median()
ind_sp = clean_prices(sp[sp['brand'] == 'Indomie']['price_per_100g']).median()
pct_sp = ((sed_sp - ind_sp) / ind_sp * 100)
pos_sp = sed_sp / ind_sp
print(f"  % Selisih: {pct_sp:+.2f}%")
print(f"  Rasio Harga: {pos_sp:.2f}")

print()
print("=" * 60)
print("SKENARIO 2: Hanya Bundle")
print("=" * 60)
bu = df[df['offer_structure'] == 'Bundle']
for brand in ['Mie Sedaap', 'Indomie']:
    b = clean_prices(bu[bu['brand'] == brand]['price_per_100g'])
    print(f"  {brand}: median p100g = Rp {b.median():.0f}, count = {len(b)}")
sed_bu = clean_prices(bu[bu['brand'] == 'Mie Sedaap']['price_per_100g']).median()
ind_bu = clean_prices(bu[bu['brand'] == 'Indomie']['price_per_100g']).median()
if pd.notna(sed_bu) and pd.notna(ind_bu) and ind_bu > 0:
    pct_bu = ((sed_bu - ind_bu) / ind_bu * 100)
    pos_bu = sed_bu / ind_bu
    print(f"  % Selisih: {pct_bu:+.2f}%")
    print(f"  Rasio Harga: {pos_bu:.2f}")
else:
    print("  Insufficient data")

print()
print("=" * 60)
print("SKENARIO 3: Semua kemasan aktif (SP + Multipack + Bundle)")
print("=" * 60)
for brand in ['Mie Sedaap', 'Indomie']:
    b = clean_prices(df[df['brand'] == brand]['price_per_100g'])
    print(f"  {brand}: median p100g = Rp {b.median():.0f}, count = {len(b)}")
sed_all = clean_prices(df[df['brand'] == 'Mie Sedaap']['price_per_100g']).median()
ind_all = clean_prices(df[df['brand'] == 'Indomie']['price_per_100g']).median()
pct_all = ((sed_all - ind_all) / ind_all * 100)
pos_all = sed_all / ind_all
print(f"  % Selisih: {pct_all:+.2f}%")
print(f"  Rasio Harga: {pos_all:.2f}")

print()
print("=" * 60)
print("ECERAN vs GROSIR (per-100g, semua data)")
print("=" * 60)
eceran = df[df['offer_structure'].str.contains('Single', case=False, na=False)]
grosir = df[df['offer_structure'].str.contains('Bundle|Multipack', case=False, na=False)]
for label, sub in [("Eceran", eceran), ("Grosir", grosir)]:
    for brand in ['Mie Sedaap', 'Indomie']:
        b = clean_prices(sub[sub['brand'] == brand]['price_per_100g'])
        med = b.median() if not b.empty else float('nan')
        print(f"  {label} {brand}: median p100g = Rp {med:.0f}, count = {len(b)}")
