import pandas as pd
import re
import hashlib
import random

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────

BUY_GET_WORDS   = ['beli 2 gratis 1', 'buy 2 get 1', 'beli 1 gratis 1', 'gratis 1', 'bonus']
BUNDLE_WORDS    = ['bundle', 'bundling', 'paket', 'combo']

NOISE_WORDS = [
    'Murah', 'Best Seller', 'Lezat', 'Higienis', 'Promo', 'Original',
    'Diskon Besar', 'Gratis', 'Termurah', 'Berkualitas', 'Praktis',
    'Kenyal', 'Gurih', 'Nikmat', 'Enak', 'Terlaris', 'Terbaru',
    'Mantap', 'Spesial offer', 'Harga Spesial', 'COD',
    'Ready Stock', '100%', 'Terbaik', 'Terpercaya',
]

# ── Brand contamination blocklist ────────────────────────────────────────────
# Products whose names contain these strings are NOT Indomie or Mie Sedaap
# and must be dropped regardless of how the scraper tagged them.
CONTAMINATION_BLOCKLIST = [
    'intermie', 'intermi', 'ekomie', 'ekomi', 'mie sakura', 'sakura',
    'mie gaga', 'mie sarimi', 'sarimi', 'wow spaghetti', 'spageti',
    'pop mie', 'pop noodle',
    'logam mulia', 'antam', 'emas', 'certicard',   # gold listings
    'bahan kue', 'gula',                            # pantry items
    'kecap sedaap', 'kecap manis',                  # condiments (not noodle)
    'bumbu kaldu', 'penyedap rasa',                 # seasonings
    'rockzillastore', 'sembako&agen', 'kab. pasuruan',  # seller-name noise
    'toko mishamasha', 'tiza bundanya',             # seller-name noise
]

# Price per-unit sanity bounds (Rp) — a single pack of instant noodle in ID
SINGLE_PACK_MIN = 2_000
SINGLE_PACK_MAX = 12_000  # upper bound for a true single pack

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def normalize_brand_prefix(s: str) -> str:
    s = re.sub(r'(?i)\bSEDAAP\s+MIE\b',         'Mie Sedaap', s)
    s = re.sub(r'(?i)\bSedaap\s+Mie\b',          'Mie Sedaap', s)
    s = re.sub(r'(?i)\bMie\s+Instan\s+Sedaap\b', 'Mie Sedaap', s)
    s = re.sub(r'(?i)\bMie\s+Instant\s+Sedaap\b','Mie Sedaap', s)
    s = re.sub(r'(?i)\bIndomie\s+Mie\b',         'Indomie', s)
    s = re.sub(r'(?i)\bMie\s+Instan\s+Indomie\b','Indomie', s)
    return s

def is_contaminated(raw_name: str) -> bool:
    """Return True if the product is NOT a target brand product."""
    nl = raw_name.lower()
    for kw in CONTAMINATION_BLOCKLIST:
        if kw in nl:
            return True
    return False

def get_unit_qty(raw_name: str) -> int:
    """
    Extract the explicit unit quantity from a listing name.
    Examples: '10 pcs', 'isi 40', '1 dus isi 40', '5 bungkus', '1 karton'
    Returns 1 if no multi-unit signal found.
    """
    nl = raw_name.lower()

    # Explicit NxM pattern (e.g. "5 x 90g", "10x85gr")
    m = re.search(r'(\d+)\s*[xX]\s*\d+\s*(?:g|gr|gram)', nl)
    if m:
        return int(m.group(1))

    # Explicit "isi N" or "N pcs/bungkus/bks/pack"
    m = re.search(r'isi\s+(\d+)', nl)
    if m:
        return int(m.group(1))

    m = re.search(r'(\d+)\s*(?:pcs|bungkus|bks)\b', nl)
    if m:
        qty = int(m.group(1))
        if qty > 1:
            return qty

    # Karton / 1 dus (implied 40 pcs unless stated otherwise)
    if re.search(r'\b(?:karton|kardus|carton|dus|box)\b', nl):
        # Try to find explicit count after
        m = re.search(r'(?:karton|kardus|carton|dus|box)\s*(?:isi)?\s*(\d+)', nl)
        if m:
            return int(m.group(1))
        return 40  # standard assumption for 1 dus mi instan

    # "N dus" pattern
    m = re.search(r'(\d+)\s*dus', nl)
    if m:
        n = int(m.group(1))
        return n * 40   # e.g. "3 dus" = 120 pcs

    # pack-count patterns like "5 pack" where pack != single
    m = re.search(r'(\d+)\s*pack\b', nl)
    if m:
        qty = int(m.group(1))
        if qty > 1:
            return qty

    return 1

def get_offer_structure(raw_name: str, final_price: float) -> str:
    """
    Determine offer structure using BOTH name signals AND price heuristic.
    A Single Pack of instant noodle in Indonesia costs Rp 2.000–12.000.
    Anything above that is almost certainly a multi-unit listing.
    """
    nl = raw_name.lower()

    # Priority 1: Price Rule (Ratusan ribu = Pasti Karton / Multipack)
    if pd.notna(final_price) and final_price >= 80000:
        return 'Multipack'

    # Priority 2: Explicit Karton/Dus words
    if re.search(r'\b(?:dus|karton|kardus|carton|box)\b', nl):
        return 'Multipack'

    # Priority 3: BuyXGetY
    if any(w in nl for w in BUY_GET_WORDS):
        return 'BuyXGetY'

    # Priority 4: Bundle words
    if any(w in nl for w in BUNDLE_WORDS):
        return 'Bundle'

    # Priority 5: Multipack signals from name
    if re.search(r'isi\s+\d+', nl):
        return 'Multipack'
    if re.search(r'\d+\s*(?:pcs|bungkus|bks)\b', nl):
        qty = re.search(r'(\d+)\s*(?:pcs|bungkus|bks)\b', nl)
        if qty and int(qty.group(1)) > 1:
            return 'Multipack'
    if re.search(r'\d+\s*[xX]\s*\d+', nl):
        return 'Multipack'
    if re.search(r'\d+\s*pack\b', nl):
        qty = re.search(r'(\d+)\s*pack', nl)
        if qty and int(qty.group(1)) > 1:
            return 'Multipack'

    # Priority 6: Price sanity check — even if name looks like Single Pack,
    if pd.notna(final_price) and final_price > SINGLE_PACK_MAX:
        return 'Multipack'

    return 'Single Pack'

def clean_name(name: str) -> str:
    s = str(name).replace(',', ' ')
    for w in BUY_GET_WORDS:
        s = re.sub(re.escape(w), '', s, flags=re.IGNORECASE)
    for w in BUNDLE_WORDS:
        s = re.sub(rf'(?<!\w){re.escape(w)}(?!\w)', '', s, flags=re.IGNORECASE)
    for w in NOISE_WORDS:
        s = re.sub(rf'(?<!\w){re.escape(w)}(?!\w)', '', s, flags=re.IGNORECASE)
    s = normalize_brand_prefix(s)
    s = re.sub(r'\d+\s*(?:g|gr|gram)\b', '', s, flags=re.IGNORECASE)
    s = re.sub(r'\bisi\s+\d+\b', '', s, flags=re.IGNORECASE)
    s = re.sub(r'\d+\s*(?:pcs|bungkus|bks|pack)\b', '', s, flags=re.IGNORECASE)
    s = re.sub(r'\d+\s*[xX]\s*\d*', '', s, flags=re.IGNORECASE)
    s = re.sub(r'\s+[xX]\d+\b', '', s)
    s = re.sub(r'\s+\d+\s*[xX]\b', '', s)
    s = re.sub(r'\b(?:Bag|Carton|Kardus|Box|Dus)\b', '', s, flags=re.IGNORECASE)
    s = re.sub(r'\b(?:Instan|Instant|Rasa)\b', '', s, flags=re.IGNORECASE)
    s = re.sub(r'[\[\]\(\)]+', ' ', s)
    s = re.sub(r'[,\-\.]+\s*$', '', s)
    s = re.sub(r'\s+\d+\s*$', '', s)
    s = re.sub(r'\s+[xX]\s*$', '', s, flags=re.IGNORECASE)
    s = re.sub(r'\s{2,}', ' ', s)
    s = s.strip().title()
    s = re.sub(r'(?i)\bMie Sedaap\b', 'Mie Sedaap', s)
    s = re.sub(r'(?i)\bIndomie\b',    'Indomie',    s)
    return s.strip()

def extract_pack_size(name: str) -> str:
    s = str(name)
    # NxMg pattern
    m = re.search(r'(\d+)\s*[xX]\s*(\d+)\s*(g|gr|gram)', s, re.IGNORECASE)
    if m:
        return f"{m.group(1)} x {m.group(2)}g"
    # qty + separate weight
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
        return f"{qty} x {wt}g"
    if qty:
        return f"{qty} pcs"
    if wt:
        return f"{wt}g"
    # Carton
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

VARIANT_FLAVOR_MAP = [
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
    return None, None

PROVINCE_CITY = {
    'DKI Jakarta':    ['Jakarta Selatan','Jakarta Barat','Jakarta Pusat','Jakarta Timur','Jakarta Utara'],
    'Jawa Barat':     ['Bandung','Bekasi','Depok','Bogor'],
    'Jawa Timur':     ['Surabaya','Malang','Sidoarjo'],
    'Jawa Tengah':    ['Semarang','Surakarta','Magelang'],
    'Banten':         ['Tangerang','Tangerang Selatan'],
    'Sumatera Utara': ['Medan'],
}
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


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    df = pd.read_csv('cleaned_competitor_data.csv')

    rows              = []
    skipped_contam    = 0
    skipped_brand     = 0
    reclassified_os   = 0

    for idx, row in df.iterrows():
        raw_brand = str(row['brand'])
        raw_name  = str(row['nama_produk'])

        # ── 1. Drop contaminated / off-target products ────────────────────
        if is_contaminated(raw_name):
            skipped_contam += 1
            continue

        # ── 2. Company / Brand mapping (strict) ──────────────────────────
        company, brand = map_company_brand(raw_brand, raw_name)
        if company is None:
            skipped_brand += 1
            continue

        # ── 3. Prices ─────────────────────────────────────────────────────
        def to_num(v):
            s = str(v).replace('Rp','').replace('.','').replace(',','').replace(' ','')
            try:    return float(s)
            except: return 0.0

        orig  = to_num(row['harga_coret'])
        final = to_num(row['harga_diskon'])
        if orig == 0 or orig < final:
            orig = final

        # Drop listings with clearly insane prices (> Rp 10 million for noodles)
        if final > 10_000_000:
            skipped_contam += 1
            continue

        # ── 4. Offer structure — price-aware ──────────────────────────────
        offer_structure_old = _get_offer_structure_name_only(raw_name)
        offer_structure     = get_offer_structure(raw_name, final)
        if offer_structure_old != offer_structure:
            reclassified_os += 1

        # ── 5. Unit qty — used to normalise price reporting ───────────────
        unit_qty = get_unit_qty(raw_name)

        # ── 6. Per-unit price (for reference; stored in price_per_unit) ──
        price_per_unit = round(final / unit_qty, 0) if unit_qty > 0 else final

        # ── 7. Clean product_name ─────────────────────────────────────────
        product_name = clean_name(raw_name)

        # ── 8. SKU ────────────────────────────────────────────────────────
        sku = make_sku(product_name, idx)

        # ── 9. Pack size ──────────────────────────────────────────────────
        pack_size = extract_pack_size(raw_name)

        # ── 10. Discount ──────────────────────────────────────────────────
        disc = round(((orig - final) / orig) * 100, 2) if orig > final else 0.0

        # ── 11. Platform ──────────────────────────────────────────────────
        plat = 'Shopee' if 'shopee' in str(row['e_commerce']).lower() else 'Tokopedia'

        # ── 12. Promo ─────────────────────────────────────────────────────
        promo_type = get_promo_type(orig, final, raw_name)
        if promo_type == 'Bundling':
            promo_text = 'Beli Banyak Lebih Murah'
        elif promo_type == 'Discount':
            promo_text = 'Diskon Spesial'
        elif promo_type == 'Flash Sale':
            promo_text = 'Flash Sale'
        else:
            promo_text = 'NULL'

        # ── 13. Province / City ───────────────────────────────────────────
        prov, city = rand_loc()

        # ── 14. Variant & Flavor ──────────────────────────────────────────
        variant, flavor = get_variant_flavor(raw_name)

        # ── 15. Sales volume ──────────────────────────────────────────────
        sv = str(row['jumlah_terjual'])
        sv = re.sub(r'(?i)rb\+', '000', sv)
        sv = re.sub(r'(?i)rb',   '000', sv)
        sv = re.sub(r'[^\d]', '', sv)
        sales_volume = sv if sv else 'NULL'

        # ── 16. Promo dates ───────────────────────────────────────────────
        promo_start = 'NULL' if promo_type == 'No Promo' else '2026-05-01'
        promo_end   = 'NULL' if promo_type == 'No Promo' else '2026-05-31'

        # ── 17. Retailer ──────────────────────────────────────────────────
        retailer = rand_retailer()

        # ── 18. Assemble row ──────────────────────────────────────────────
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

    # ── Deduplication ──────────────────────────────────────────────────────
    seen   = set()
    deduped = []
    for r in rows:
        parts = r.split(',')
        key   = (parts[1], parts[2], parts[3], parts[7])   # company+brand+name+price
        if key not in seen:
            seen.add(key)
            deduped.append(r)
    rows = deduped

    # ── Save ───────────────────────────────────────────────────────────────
    with open('final_normalized_data.csv', 'w', encoding='utf-8') as f:
        f.write('\n'.join(rows) + '\n')

    total_input = len(df)
    print(f"\n{'='*55}")
    print(f"  NORMALIZATION COMPLETE")
    print(f"{'='*55}")
    print(f"  Input rows          : {total_input:,}")
    print(f"  Skipped (contaminated/insane price): {skipped_contam:,}")
    print(f"  Skipped (brand mismatch): {skipped_brand:,}")
    print(f"  Offer struct re-classified: {reclassified_os:,}")
    print(f"  Output rows (deduped): {len(rows):,}")
    print(f"\n--- SAMPLE: first 5 rows ---")
    for r in rows[:5]:
        print(r)

    # ── Quick sanity check: Single Pack price distribution ─────────────────
    print(f"\n--- SINGLE PACK PRICE SANITY ---")
    sp_prices = []
    for r in rows:
        p = r.split(',')
        if len(p) == 21 and p[17] == 'Single Pack':
            try:
                sp_prices.append(float(p[7]))
            except:
                pass
    if sp_prices:
        sp_prices.sort()
        print(f"  Count   : {len(sp_prices)}")
        print(f"  Min     : Rp {min(sp_prices):,.0f}")
        print(f"  Max     : Rp {max(sp_prices):,.0f}")
        print(f"  Median  : Rp {sp_prices[len(sp_prices)//2]:,.0f}")
        suspicious = [p for p in sp_prices if p > 12_000]
        print(f"  >Rp12k  : {len(suspicious)} rows  ← should be 0 or near-0")


def _get_offer_structure_name_only(name: str) -> str:
    """Original name-only version — used only for counting reclassifications."""
    nl = name.lower()
    if any(w in nl for w in BUY_GET_WORDS):
        return 'BuyXGetY'
    if any(w in nl for w in BUNDLE_WORDS):
        return 'Bundle'
    if re.search(r'isi\s+\d+', nl):                       return 'Multipack'
    if re.search(r'\d+\s*(pcs|bungkus|bks|pack)', nl):    return 'Multipack'
    if re.search(r'\d+\s*[xX]\s*\d+', nl):                return 'Multipack'
    if 'dus' in nl or 'carton' in nl or 'kardus' in nl:   return 'Multipack'
    return 'Single Pack'


if __name__ == '__main__':
    main()