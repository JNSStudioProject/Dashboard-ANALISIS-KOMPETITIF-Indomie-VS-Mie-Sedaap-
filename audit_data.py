import pandas as pd
import re

cols=['scrape_date','company','brand','product_name','sku_id','pack_size',
      'original_price','final_price','discount_pct','retailer','platform',
      'province','city','promo_type','promo_text','variant','flavor',
      'offer_structure','promo_start','promo_end','sales_volume']

df = pd.read_csv('final_normalized_data.csv', header=None, names=cols, na_values=['NULL'])
df['final_price'] = pd.to_numeric(df['final_price'], errors='coerce')
df['original_price'] = pd.to_numeric(df['original_price'], errors='coerce')

print("=== SHAPE ===")
print(df.shape)

print("\n=== OFFER STRUCTURE COUNTS ===")
print(df['offer_structure'].value_counts())

print("\n=== BRAND COUNTS ===")
print(df['brand'].value_counts())

print("\n=== PACK_SIZE SAMPLES per offer_structure ===")
for os_val in df['offer_structure'].unique():
    sub = df[df['offer_structure']==os_val]
    price_min = sub['final_price'].min()
    price_max = sub['final_price'].max()
    price_mean = sub['final_price'].mean()
    print(f"\n--- {os_val} (n={len(sub)}) ---")
    print(f"  price range: {price_min:.0f} - {price_max:.0f}, mean: {price_mean:.0f}")
    print(f"  pack_size samples: {list(sub['pack_size'].dropna().unique()[:10])}")

# Check per brand per offer_structure
print("\n\n=== PRICE STATS: Brand x Offer Structure ===")
pivot = df.groupby(['brand','offer_structure'])['final_price'].agg(['count','mean','median','min','max'])
print(pivot.to_string())

# Check what happens with weight extraction
BRAND_AVG_WEIGHT = {
    'Mie Sedaap': 82,
    'Indomie': 80,
}

def extract_total_weight(row):
    ps = row.get('pack_size', None)
    brand = row.get('brand', None)
    if pd.isna(ps):
        return None
    ps_str = str(ps).lower()
    m = re.match(r'(\d+)\s*x\s*(\d+)g', ps_str)
    if m:
        return int(m.group(1)) * int(m.group(2))
    m2 = re.match(r'^(\d+)g$', ps_str)
    if m2:
        return int(m2.group(1))
    m3 = re.match(r'(\d+)\s*pcs', ps_str)
    if m3:
        qty = int(m3.group(1))
        avg_w = BRAND_AVG_WEIGHT.get(brand, 81)
        return qty * avg_w
    return None

df['total_weight_g'] = df.apply(extract_total_weight, axis=1)
df['price_per_100g'] = (df['final_price'] / df['total_weight_g']) * 100

print("\n\n=== WEIGHT EXTRACTION FAILURES ===")
no_weight = df[df['total_weight_g'].isna()]
print(f"Total rows with no weight: {len(no_weight)} / {len(df)}")
print(f"pack_size values with no weight: {list(no_weight['pack_size'].unique()[:20])}")

print("\n\n=== PRICE PER 100G STATS by Brand (Single Pack only) ===")
sp = df[df['offer_structure']=='Single Pack']
for brand in sp['brand'].unique():
    b = sp[sp['brand']==brand]['price_per_100g'].dropna()
    print(f"\n{brand}: count={len(b)}, median={b.median():.0f}, mean={b.mean():.0f}, min={b.min():.0f}, max={b.max():.0f}")

print("\n\n=== PRICE PER 100G STATS by Brand (ALL data) ===")
for brand in df['brand'].unique():
    b = df[df['brand']==brand]['price_per_100g'].dropna()
    print(f"\n{brand}: count={len(b)}, median={b.median():.0f}, mean={b.mean():.0f}, min={b.min():.0f}, max={b.max():.0f}")

# Check suspicious data
def validate_price_per_unit(row):
    price = row['final_price']
    pack_type = row['offer_structure']
    weight = row['total_weight_g']
    suspicious = False
    if pd.notna(weight) and weight > 0:
        p100g = (price / weight) * 100
        if p100g > 25000 or p100g < 300:
            suspicious = True
    if pack_type == 'Single Pack' and price > 25000:
        suspicious = True
    return suspicious

df['price_flag'] = df.apply(validate_price_per_unit, axis=1)
print(f"\n\n=== VALIDATION RESULTS ===")
print(f"Flagged: {df['price_flag'].sum()} / {len(df)}")
print(f"Clean: {(~df['price_flag']).sum()}")

df_clean = df[~df['price_flag']]
print(f"\n=== CLEAN DATA: Price per 100g by Brand ===")
for brand in df_clean['brand'].unique():
    b = df_clean[df_clean['brand']==brand]['price_per_100g'].dropna()
    print(f"{brand}: count={len(b)}, median={b.median():.0f}, mean={b.mean():.0f}")

print(f"\n=== CLEAN DATA: Single Pack avg price by Brand ===")
sp_clean = df_clean[df_clean['offer_structure']=='Single Pack']
for brand in sp_clean['brand'].unique():
    b = sp_clean[sp_clean['brand']==brand]['final_price'].dropna()
    print(f"{brand}: count={len(b)}, mean={b.mean():.0f}, median={b.median():.0f}")

print(f"\n=== CLEAN DATA: Grosir (Bundle+Multipack) normalized price by Brand ===")
grosir = df_clean[df_clean['offer_structure'].str.contains('Bundle|Multipack', case=False, na=False)].copy()

def extract_unit_quantity(ps):
    if pd.isna(ps): return 1
    ps = str(ps).lower()
    m = re.match(r'(\d+)\s*x\s*', ps)
    if m: return int(m.group(1))
    m2 = re.match(r'(\d+)\s*pcs', ps)
    if m2: return int(m2.group(1))
    return 1

grosir['unit_qty'] = grosir['pack_size'].apply(extract_unit_quantity)
grosir['norm_price'] = grosir['final_price'] / grosir['unit_qty']
for brand in grosir['brand'].unique():
    b = grosir[grosir['brand']==brand]['norm_price'].dropna()
    print(f"{brand}: count={len(b)}, mean={b.mean():.0f}, median={b.median():.0f}")

# What does the % selisih look like?
sed_p100 = df_clean[df_clean['brand']=='Mie Sedaap']['price_per_100g'].median()
ind_p100 = df_clean[df_clean['brand']=='Indomie']['price_per_100g'].median()
pct = ((sed_p100 - ind_p100) / ind_p100) * 100 if ind_p100 > 0 else 0
print(f"\n=== % SELISIH (based on median price_per_100g, ALL data) ===")
print(f"Sedaap median p100g: {sed_p100:.0f}")
print(f"Indomie median p100g: {ind_p100:.0f}")
print(f"% Selisih: {pct:.2f}%")

# Single pack only
sed_sp = df_clean[(df_clean['brand']=='Mie Sedaap') & (df_clean['offer_structure']=='Single Pack')]['price_per_100g'].median()
ind_sp = df_clean[(df_clean['brand']=='Indomie') & (df_clean['offer_structure']=='Single Pack')]['price_per_100g'].median()
pct_sp = ((sed_sp - ind_sp) / ind_sp) * 100 if ind_sp > 0 else 0
print(f"\n=== % SELISIH (Single Pack only) ===")
print(f"Sedaap median p100g (SP): {sed_sp:.0f}")
print(f"Indomie median p100g (SP): {ind_sp:.0f}")
print(f"% Selisih (SP): {pct_sp:.2f}%")
