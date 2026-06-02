"""
Price Sanity Check & Auto-Correction
Rule: Single Pack + pack_size <= 100g + final_price > THRESHOLD → flag & re-examine
"""
import pandas as pd
import re

# Reasonable max price for a SINGLE instant noodle pack in Indonesia
SINGLE_PACK_PRICE_THRESHOLD = 10000  # Rp 10,000

def parse_weight_grams(pack_size: str):
    """Extract per-unit weight in grams from pack_size string. Returns None if not found."""
    if not pack_size or pack_size == 'NULL':
        return None
    # NxMg → return M (per-unit weight)
    m = re.match(r'\d+[xX](\d+)g$', pack_size.strip())
    if m:
        return int(m.group(1))
    # Mg (single weight)
    m = re.match(r'(\d+)g$', pack_size.strip())
    if m:
        return int(m.group(1))
    return None

def detect_hidden_multipack(raw_name: str):
    """Scan raw product title for hidden multipack/bundle evidence."""
    nl = str(raw_name).lower()
    signals = []
    # trailing xN multiplier
    if re.search(r'\b[xX]\s*\d+\b', nl): signals.append('trailing_xN')
    if re.search(r'\bisi\s+\d+\b', nl):  signals.append('isi_N')
    if re.search(r'\d+\s*(?:pcs|bungkus|bks|pack)\b', nl): signals.append('N_pcs')
    if re.search(r'\d+\s*[xX]\s*\d+', nl): signals.append('NxM')
    if any(w in nl for w in ['dus', 'karton', 'carton', 'kardus', 'box']): signals.append('carton')
    if any(w in nl for w in ['bundle', 'bundling', 'paket', 'hemat']): signals.append('bundle_text')
    return signals

def extract_corrected_pack_size(raw_name: str):
    """Re-extract pack_size with full NxMg logic from original raw name."""
    s = str(raw_name)
    # Full NxMg
    m = re.search(r'(\d+)\s*[xX]\s*(\d+)\s*(?:g|gr|gram)', s, re.IGNORECASE)
    if m:
        return f"{m.group(1)}x{m.group(2)}g"
    # qty + separate weight
    m_qty = re.search(r'(?:isi\s+)?(\d+)\s*(?:pcs|bungkus|bks|pack)', s, re.IGNORECASE)
    if not m_qty:
        m_qty = re.search(r'isi\s+(\d+)', s, re.IGNORECASE)
    m_wt = re.search(r'(\d+)\s*(?:g|gr|gram)\b', s, re.IGNORECASE)
    if m_qty and m_wt:
        return f"{m_qty.group(1)}x{m_wt.group(1)}g"
    if m_qty:
        return f"{m_qty.group(1)} pcs"
    if m_wt:
        return f"{m_wt.group(1)}g"
    return 'NULL'

def main():
    norm = pd.read_csv('final_normalized_data.csv', header=None, names=[
        'scrape_date','company','brand','product_name','sku_id','pack_size',
        'original_price','final_price','discount_pct','retailer','platform',
        'province','city','promo_type','promo_text','variant','flavor',
        'offer_structure','promo_start','promo_end','sales_volume'
    ], on_bad_lines='skip')
    orig = pd.read_csv('cleaned_competitor_data.csv')

    # Build lookup: sku_id → original product name
    sku_to_raw = {}
    for _, row in orig.iterrows():
        import hashlib
        # re-generate same SKU logic to match
        # We just match by brand + final_price as proxy (since SKU was generated)
        pass  # will use product_name substring match instead

    flags = []
    corrections = 0

    for idx, row in norm.iterrows():
        if row['offer_structure'] != 'Single Pack':
            continue

        wt = parse_weight_grams(str(row['pack_size']))
        if wt is None or wt > 100:
            continue  # can't determine or clearly single

        price = float(row['final_price'])
        if price <= SINGLE_PACK_PRICE_THRESHOLD:
            continue  # price looks fine

        # ── FLAGGED: Single Pack + small weight + high price ──────────────
        # Try to find the original raw listing that maps to this product
        brand_col = 'Wings' if row['company'] == 'Wings Group' else 'Indofood'
        matches = orig[
            (orig['brand'] == brand_col) &
            (orig['harga_diskon'].astype(str) == str(int(price)))
        ]

        signals = []
        corrected_pack = row['pack_size']
        new_offer_str  = row['offer_structure']

        if not matches.empty:
            raw_name = matches.iloc[0]['nama_produk']
            signals  = detect_hidden_multipack(raw_name)
            if signals:
                corrected_pack = extract_corrected_pack_size(raw_name)
                new_offer_str  = 'Multipack'

        flags.append({
            'row_idx':         idx,
            'product_name':    row['product_name'],
            'pack_size':       row['pack_size'],
            'final_price':     price,
            'offer_structure': row['offer_structure'],
            'signals':         ', '.join(signals) if signals else 'NONE — keep Single Pack',
            'corrected_pack':  corrected_pack,
            'new_offer_str':   new_offer_str,
        })

        if signals:
            norm.at[idx, 'pack_size']       = corrected_pack
            norm.at[idx, 'offer_structure'] = new_offer_str
            corrections += 1

    # ── Report ─────────────────────────────────────────────────────────────
    print(f"\n=== PRICE SANITY CHECK REPORT ===")
    print(f"Threshold: Single Pack + weight <= 100g + price > Rp{SINGLE_PACK_PRICE_THRESHOLD:,}")
    print(f"Total flagged : {len(flags)}")
    print(f"Auto-corrected: {corrections}\n")

    for f in flags[:30]:   # show up to 30
        status = 'CORRECTED' if f['signals'] != 'NONE — keep Single Pack' else 'NO EVIDENCE (keep)'
        print(f"[{status}] {f['product_name']}")
        print(f"   pack_size : {f['pack_size']} -> {f['corrected_pack']}")
        print(f"   price     : Rp {f['final_price']:,.0f}")
        print(f"   signals   : {f['signals']}")
        print()

    # Save corrected CSV
    norm.to_csv('final_normalized_data.csv', index=False, header=False)
    print(f"[SAVED] final_normalized_data.csv ({len(norm)} rows, {corrections} offer_structure corrections applied)")

if __name__ == '__main__':
    main()
