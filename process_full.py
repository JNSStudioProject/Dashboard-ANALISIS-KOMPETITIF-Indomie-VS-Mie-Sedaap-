import pandas as pd
import re
import hashlib

# ── helpers ──────────────────────────────────────────────────────────────────

BUY_GET_WORDS = ['beli 2 gratis 1', 'buy 2 get 1', 'beli 1 gratis 1', 'gratis 1', 'bonus']
BUNDLE_WORDS  = ['bundle', 'bundling', 'paket', 'combo']
MULTIPACK_WORDS = ['isi ', ' pcs', ' pack', 'x ', 'dus']


NOISE_WORDS = [
    'Murah', 'Best Seller', 'Lezat', 'Higienis', 'Promo', 'Original',
    'Diskon Besar', 'Gratis', 'Termurah', 'Berkualitas', 'Praktis',
    'Kenyal', 'Gurih', 'Nikmat', 'Enak', 'Terlaris', 'Terbaru',
    'Mantap', 'Spesial offer', 'Harga Spesial', 'COD',
    'Ready Stock', '100%', 'Terbaik', 'Terpercaya',
]

def normalize_brand_prefix(s: str) -> str:
    """Normalize raw marketplace brand prefixes to standard Title Case."""
    # SEDAAP MIE / Sedaap Mie → Mie Sedaap
    s = re.sub(r'(?i)\bSEDAAP\s+MIE\b', 'Mie Sedaap', s)
    s = re.sub(r'(?i)\bSedaap\s+Mie\b', 'Mie Sedaap', s)
    s = re.sub(r'(?i)\bMie\s+Instan\s+Sedaap\b', 'Mie Sedaap', s)
    s = re.sub(r'(?i)\bMie\s+Instant\s+Sedaap\b', 'Mie Sedaap', s)
    # INDOMIE / Indomie Mie → Indomie
    s = re.sub(r'(?i)\bIndomie\s+Mie\b', 'Indomie', s)
    s = re.sub(r'(?i)\bMie\s+Instan\s+Indomie\b', 'Indomie', s)
    return s

def clean_name(name: str) -> str:
    s = str(name)
    # 1. Remove BuyXGetY wording
    for w in BUY_GET_WORDS:
        s = re.sub(re.escape(w), '', s, flags=re.IGNORECASE)
    # 2. Remove bundle wording
    for w in BUNDLE_WORDS:
        s = re.sub(rf'(?<!\w){re.escape(w)}(?!\w)', '', s, flags=re.IGNORECASE)
    # 3. Remove noise marketing words
    for w in NOISE_WORDS:
        s = re.sub(rf'(?<!\w){re.escape(w)}(?!\w)', '', s, flags=re.IGNORECASE)
    # 4. Normalize brand prefix BEFORE stripping
    s = normalize_brand_prefix(s)
    # 5. Remove physical size/weight from name (goes to pack_size)
    s = re.sub(r'\d+\s*(?:g|gr|gram)\b', '', s, flags=re.IGNORECASE)
    # 6. Remove quantity patterns (isi N, N pcs, N x M, etc.) from name
    s = re.sub(r'\bisi\s+\d+\b', '', s, flags=re.IGNORECASE)
    s = re.sub(r'\d+\s*(?:pcs|bungkus|bks|pack)\b', '', s, flags=re.IGNORECASE)
    s = re.sub(r'\d+\s*[xX]\s*\d*', '', s, flags=re.IGNORECASE)
    # 7. Remove trailing standalone multipliers like "x5", "X40", "x 5" at end
    s = re.sub(r'\s+[xX]\d+\b', '', s)
    s = re.sub(r'\s+\d+\s*[xX]\b', '', s)
    # 8. Remove container words
    s = re.sub(r'\b(?:Bag|Carton|Kardus|Box|Dus)\b', '', s, flags=re.IGNORECASE)
    # 9. Remove 'Instan' / 'Instant' and 'Rasa' as noise in name
    s = re.sub(r'\b(?:Instan|Instant|Rasa)\b', '', s, flags=re.IGNORECASE)
    # 10. Remove leftover brackets and punctuation
    s = re.sub(r'[\[\]\(\)]+', ' ', s)
    s = re.sub(r'[,\-\.]+\s*$', '', s)
    # 11. Remove trailing standalone digits or 'X' left over
    s = re.sub(r'\s+\d+\s*$', '', s)
    s = re.sub(r'\s+[xX]\s*$', '', s, flags=re.IGNORECASE)
    s = re.sub(r'\s{2,}', ' ', s)
    # 12. Title Case
    s = s.strip().title()
    # 13. Fix brand names casing
    s = re.sub(r'(?i)\bMie Sedaap\b', 'Mie Sedaap', s)
    s = re.sub(r'(?i)\bIndomie\b', 'Indomie', s)
    return s.strip()

def extract_pack_size(name: str) -> str:
    """Attempt weight+qty combined extraction first, then fallback."""
    s = str(name)
    nl = s.lower()

    # 1. Explicit NxMg pattern already written: "5 x 90g", "5x75g", "5x90gr"
    m = re.search(r'(\d+)\s*[xX]\s*(\d+)\s*(g|gr|gram)', s, re.IGNORECASE)
    if m:
        qty = m.group(1)
        wt  = m.group(2)
        return f"{qty}x{wt}g"

    # 2. Qty from "isi N" or "N pcs/bungkus" AND separate weight Mg
    qty = None
    wt  = None
    m_qty = re.search(r'(?:isi\s+)?(\d+)\s*(?:pcs|bungkus|bks|pack)', s, re.IGNORECASE)
    if not m_qty:
        m_qty = re.search(r'isi\s+(\d+)', s, re.IGNORECASE)
    if m_qty:
        qty = m_qty.group(1)

    m_wt = re.search(r'(\d+)\s*(?:g|gr|gram)\b', s, re.IGNORECASE)
    if m_wt:
        wt = m_wt.group(1)

    if qty and wt:
        return f"{qty}x{wt}g"
    if qty:
        return f"{qty} pcs"
    if wt:
        return f"{wt}g"

    # 3. Carton / Kardus / Dus  — try to get count
    m_carton = re.search(r'(?:carton|kardus|dus)\s*(?:isi)?\s*(\d+)', s, re.IGNORECASE)
    if m_carton:
        return f"{m_carton.group(1)} pcs"

    return 'NULL'

def get_promo_type(orig: float, final: float, name: str) -> str:
    nl = name.lower()
    if 'flash sale' in nl:
        return 'Flash Sale'
    if any(w in nl for w in BUY_GET_WORDS):
        return 'Buy1Get1'
    if any(w in nl for w in ['paket', 'bundling', 'hemat', 'lebih murah']):
        return 'Bundling'
    if orig > final:
        return 'Discount'
    return 'No Promo'

def get_offer_structure(name: str) -> str:
    nl = name.lower()
    # BuyXGetY takes priority
    if any(w in nl for w in BUY_GET_WORDS):
        return 'BuyXGetY'
    # Bundle
    if any(w in nl for w in BUNDLE_WORDS):
        return 'Bundle'
    # Multipack — quantity keywords
    if re.search(r'isi\s+\d+', nl):
        return 'Multipack'
    if re.search(r'\d+\s*(pcs|bungkus|bks|pack)', nl):
        return 'Multipack'
    if re.search(r'\d+\s*[xX]\s*\d+', nl):
        return 'Multipack'
    if 'dus' in nl or 'carton' in nl or 'kardus' in nl:
        return 'Multipack'
    return 'Single Pack'

# Variant → product family/style  |  Flavor → rasa detail
VARIANT_FLAVOR_MAP = [
    # Pattern              variant       flavor
    ('korean spicy chicken', 'Korean',  'Spicy Chicken'),
    ('korean spicy soup',    'Korean',  'Spicy Soup'),
    ('korean cheese buldak', 'Korean',  'Cheese Buldak'),
    ('cheese buldak',        'Korean',  'Cheese Buldak'),
    ('buldak',               'Korean',  'Buldak'),
    ('singapore spicy laksa','Laksa',   'Singapore Spicy Laksa'),
    ('laksa',                'Laksa',   'Laksa'),
    ('white curry',          'Kari',    'White Curry'),
    ('kari kental',          'Kari',    'Kari Kental'),
    ('kari mercon',          'Kari',    'Kari Mercon'),
    ('kari ayam',            'Kari',    'Kari Ayam'),
    ('kari',                 'Kari',    'NULL'),
    ('curry',                'Kari',    'NULL'),
    ('ayam geprek',          'Goreng',  'Ayam Geprek'),
    ('ayam bakar limau',     'Goreng',  'Ayam Bakar Limau'),
    ('goreng spesial',       'Goreng',  'Goreng Spesial'),
    ('ayam krispi',          'Goreng',  'Ayam Krispi'),
    ('goreng kriuk',         'Goreng',  'Goreng Kriuk'),
    ('salero padang',        'Goreng',  'Salero Padang'),
    ('rendang',              'Goreng',  'Rendang'),
    ('goreng',               'Goreng',  'NULL'),
    ('ayam bawang',          'Kuah',    'Ayam Bawang'),
    ('ayam spesial',         'Kuah',    'Ayam Spesial'),
    ('ayam jerit',           'Kuah',    'Ayam Jerit'),
    ('bakso spesial',        'Kuah',    'Bakso Spesial'),
    ('baso bleduk',          'Kuah',    'Baso Bleduk'),
    ('soto banjar',          'Soto',    'Soto Banjar'),
    ('soto madura',          'Soto',    'Soto Madura'),
    ('soto',                 'Soto',    'NULL'),
    ('coto makassar',        'Kuah',    'Coto Makassar'),
    ('celor',                'Kuah',    'Celor Palembang'),
    ('empal gentong',        'Kuah',    'Empal Gentong'),
    ('kuah',                 'Kuah',    'NULL'),
]

def get_variant_flavor(name: str):
    nl = name.lower()
    for pattern, variant, flavor in VARIANT_FLAVOR_MAP:
        if pattern in nl:
            return variant, flavor
    return 'NULL', 'NULL'

def make_sku(name: str, idx: int) -> str:
    return f"SKU-{hashlib.md5((str(name)+str(idx)).encode()).hexdigest()[:8].upper()}"

def map_company_brand(raw_brand: str, product_name: str):
    nl = product_name.lower()
    rb = raw_brand.lower()
    if 'indomie' in nl or rb == 'indofood':
        return 'Indofood', 'Indomie'
    if 'mie sedaap' in nl or 'sedaap' in nl or rb == 'wings':
        return 'Wings Group', 'Mie Sedaap'
    return None, None   # skip unrelated

PROVINCE_CITY = {
    'DKI Jakarta':    ['Jakarta Selatan','Jakarta Barat','Jakarta Pusat','Jakarta Timur','Jakarta Utara'],
    'Jawa Barat':     ['Bandung','Bekasi','Depok','Bogor'],
    'Jawa Timur':     ['Surabaya','Malang','Sidoarjo'],
    'Jawa Tengah':    ['Semarang','Surakarta','Magelang'],
    'Banten':         ['Tangerang','Tangerang Selatan'],
    'Sumatera Utara': ['Medan'],
}
import random
random.seed(42)
def rand_loc():
    provinces = list(PROVINCE_CITY.keys())
    weights   = [0.40, 0.25, 0.15, 0.10, 0.07, 0.03]
    prov = random.choices(provinces, weights=weights)[0]
    city = random.choice(PROVINCE_CITY[prov])
    return prov, city

RETAILERS = ['Official Store','Mitra Distributor','Toko Grosir Sembako',
             'Retail Express','Supermarket Online','Toko Kelontong Digital']
R_WEIGHTS  = [0.10, 0.25, 0.25, 0.15, 0.10, 0.15]

def rand_retailer():
    return random.choices(RETAILERS, weights=R_WEIGHTS)[0]

# ── main ─────────────────────────────────────────────────────────────────────

def main():
    df = pd.read_csv('cleaned_competitor_data.csv')
    rows = []

    for idx, row in df.iterrows():
        raw_brand = str(row['brand'])
        raw_name  = str(row['nama_produk'])

        # 1. Company / Brand mapping (STRICT)
        company, brand = map_company_brand(raw_brand, raw_name)
        if company is None:
            continue    # skip non-target products

        # 2. Clean product_name
        product_name = clean_name(raw_name)

        # 3. SKU
        sku = make_sku(product_name, idx)

        # 4. pack_size  ← extracted properly
        pack_size = extract_pack_size(raw_name)

        # 5. Prices
        def to_num(v):
            s = str(v).replace('Rp','').replace('.','').replace(',','').replace(' ','')
            try: return float(s)
            except: return 0.0

        orig  = to_num(row['harga_coret'])
        final = to_num(row['harga_diskon'])
        if orig == 0 or orig < final:
            orig = final

        # 6. discount_pct  (recalculated)
        disc = round(((orig - final) / orig) * 100, 2) if orig > final else 0.0

        # 7. Platform
        plat = 'Shopee' if 'shopee' in str(row['e_commerce']).lower() else 'Tokopedia'

        # 8. promo_type — EXACT ENUM ONLY
        promo_type = get_promo_type(orig, final, raw_name)

        # 9. promo_text
        if promo_type == 'Bundling':
            promo_text = 'Beli Banyak Lebih Murah'
        elif promo_type == 'Discount':
            promo_text = 'Diskon Spesial'
        elif promo_type == 'Flash Sale':
            promo_text = 'Flash Sale'
        else:
            promo_text = 'NULL'

        # 10. Province / City
        prov, city = rand_loc()

        # 11. Variant & Flavor — properly split
        variant, flavor = get_variant_flavor(raw_name)

        # 12. sales_volume
        sv = str(row['jumlah_terjual'])
        sv = re.sub(r'(?i)rb\+', '000', sv)
        sv = re.sub(r'(?i)rb',   '000', sv)
        sv = re.sub(r'[^\d]', '', sv)
        sales_volume = sv if sv else 'NULL'

        # 13. Retailer
        retailer = rand_retailer()

        # offer_structure — detect from RAW name before cleaning
        offer_structure = get_offer_structure(raw_name)

        # ── Assemble EXACT 21-column schema ──────────────────────────────
        # scrape_date,company,brand,product_name,sku_id,pack_size,
        # original_price,final_price,discount_pct,retailer,platform,
        # province,city,promo_type,promo_text,variant,flavor,
        # offer_structure,promo_start,promo_end,sales_volume
        # promo dates — NULL when No Promo
        if promo_type == 'No Promo':
            promo_start = 'NULL'
            promo_end   = 'NULL'
        else:
            promo_start = '2026-05-01'
            promo_end   = '2026-05-31'

        parts = [
            '2026-05-29',
            company,
            brand,
            product_name,
            sku,
            pack_size,
            str(int(orig)),
            str(int(final)),
            f"{disc:.2f}",
            retailer,
            plat,
            prov,
            city,
            promo_type,
            promo_text,
            variant,
            flavor,
            offer_structure,
            promo_start,
            promo_end,
            sales_volume,
        ]
        rows.append(','.join(parts))

    # Deduplication: drop exact same brand + clean product_name + final_price
    seen = set()
    deduped = []
    for r in rows:
        parts = r.split(',')
        # key = company + brand + product_name + final_price
        key = (parts[0], parts[1], parts[2], parts[3], parts[7])
        if key not in seen:
            seen.add(key)
            deduped.append(r)
    rows = deduped

    # Save
    with open('final_normalized_data.csv', 'w', encoding='utf-8') as f:
        f.write('\n'.join(rows) + '\n')

    print(f"[OK] {len(rows)} rows written to final_normalized_data.csv (after dedup)")
    print("\n--- SAMPLE (first 5 rows) ---")
    for r in rows[:5]:
        print(r)

if __name__ == '__main__':
    main()
