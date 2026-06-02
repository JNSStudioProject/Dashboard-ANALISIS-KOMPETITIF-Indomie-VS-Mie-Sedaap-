"""
Final Normalization Patch
- Fix 1: Replace all empty string fields with NULL
- Fix 2: Standardize pack_size to "N x Mg" format (with spaces around x)
- Fix 3: discount_pct format (0.0 → 0, keep 2 decimals for non-zero)
"""
import re

def fix_pack_size(ps: str) -> str:
    ps = ps.strip()
    if not ps or ps == 'NULL':
        return 'NULL'

    # Normalize gr/gram → g
    ps = re.sub(r'\bgramme?\b', 'g', ps, flags=re.IGNORECASE)
    ps = re.sub(r'(?<=\d)gr\b', 'g', ps, flags=re.IGNORECASE)

    # Pattern: "NxMg" or "Nx Mg" or "N xMg" → "N x Mg"
    m = re.match(r'^(\d+)\s*[xX]\s*(\d+)\s*g$', ps)
    if m:
        return f"{m.group(1)} x {m.group(2)}g"

    # Pattern: "N pcs" already correct (only qty)
    m = re.match(r'^(\d+)\s*pcs$', ps)
    if m:
        return f"{m.group(1)} pcs"

    # Pattern: "Ng" already correct (only weight)
    m = re.match(r'^(\d+)g$', ps)
    if m:
        return ps  # already clean

    # Anything else: return as-is after normalizing gr
    return ps

def fix_discount(dc: str) -> str:
    dc = dc.strip()
    try:
        v = float(dc)
        if v == 0.0:
            return '0'
        return f"{v:.2f}"
    except:
        return dc if dc else 'NULL'

def patch_row(line: str) -> str:
    # Split carefully — preserve quoted fields with commas
    # Use simple split since we control the format (no quotes expected in clean data)
    parts = line.rstrip('\n').split(',')

    if len(parts) != 21:
        # skip malformed lines
        return line

    # Column indices (0-indexed):
    # 0  scrape_date
    # 1  company
    # 2  brand
    # 3  product_name
    # 4  sku_id
    # 5  pack_size        ← format fix
    # 6  original_price
    # 7  final_price
    # 8  discount_pct     ← format fix
    # 9  retailer
    # 10 platform
    # 11 province
    # 12 city
    # 13 promo_type
    # 14 promo_text       ← NULL fix
    # 15 variant          ← NULL fix
    # 16 flavor           ← NULL fix
    # 17 offer_structure
    # 18 promo_start      ← NULL fix
    # 19 promo_end        ← NULL fix
    # 20 sales_volume     ← NULL fix

    NULL_COLS = {5, 11, 12, 14, 15, 16, 18, 19, 20}

    for i in range(len(parts)):
        parts[i] = parts[i].strip()
        # Replace blank/empty with NULL for nullable columns
        if i in NULL_COLS and parts[i] == '':
            parts[i] = 'NULL'

    # Fix pack_size (col 5)
    parts[5] = fix_pack_size(parts[5])

    # Fix discount_pct (col 8)
    parts[8] = fix_discount(parts[8])

    return ','.join(parts)

def main():
    input_file  = 'final_normalized_data.csv'
    output_file = 'final_normalized_data.csv'

    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    patched = []
    empty_fixed   = 0
    packsize_fixed = 0

    for line in lines:
        if not line.strip():
            continue

        original = line.strip()
        fixed    = patch_row(original)

        # Count changes
        if fixed != original:
            orig_parts  = original.split(',')
            fixed_parts = fixed.split(',')
            if len(orig_parts) == len(fixed_parts) == 21:
                for i in range(21):
                    if orig_parts[i] != fixed_parts[i]:
                        if orig_parts[i] == '' and fixed_parts[i] == 'NULL':
                            empty_fixed += 1
                        elif i == 5 and orig_parts[i] != fixed_parts[i]:
                            packsize_fixed += 1

        patched.append(fixed)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(patched) + '\n')

    print(f"[PATCH COMPLETE]")
    print(f"  Rows processed  : {len(patched)}")
    print(f"  Empty -> NULL   : {empty_fixed} fields fixed")
    print(f"  pack_size fmt   : {packsize_fixed} fields reformatted")
    print(f"\n--- SAMPLE (first 5 rows) ---")
    for r in patched[:5]:
        print(r)

if __name__ == '__main__':
    main()
