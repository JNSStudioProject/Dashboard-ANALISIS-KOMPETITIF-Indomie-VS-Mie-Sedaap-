import pandas as pd
import re
import hashlib

def clean_name(name):
    noise = ['Murah', 'Best Seller', 'Lezat', 'Higienis', 'Promo', 'Original', 'Diskon Besar', 'Gratis', 'Praktis', 'Termurah', 'Terlaris']
    name_clean = str(name)
    for n in noise:
        name_clean = re.sub(rf'\b{n}\b', '', name_clean, flags=re.IGNORECASE)
    return ' '.join(name_clean.split()).replace('"', '')

def extract_pack_size(name):
    match = re.search(r'(\d+\s*(?:pcs|g|gr|gram|bungkus|bks|pack|kg))', str(name), re.IGNORECASE)
    if match:
        return match.group(1).lower().replace('gr', 'g').replace('gram', 'g')
    return 'NULL'

def get_promo_type(orig, final, name):
    name_lower = str(name).lower()
    if 'flash sale' in name_lower:
        return 'Flash Sale'
    if any(w in name_lower for w in ['paket', 'bundling', 'hemat', 'lebih murah']):
        return 'Bundling'
    if orig > final:
        return 'Discount'
    return 'No Promo'

def get_flavor(name):
    name_lower = str(name).lower()
    flavors = ['ayam bawang', 'goreng spesial', 'kari ayam', 'soto', 'korean spicy', 'singapore laksa', 'ayam geprek', 'rendang', 'ayam bakar limau', 'baso bleduk']
    for f in flavors:
        if f in name_lower:
            return f.title()
    return 'NULL'

def generate_sku(name, idx):
    return f"SKU-{hashlib.md5((str(name)+str(idx)).encode()).hexdigest()[:8].upper()}"

def main():
    df = pd.read_csv('cleaned_competitor_data.csv').head(5)
    
    for idx, row in df.iterrows():
        # company mapping
        company = 'Indofood' if str(row['brand']).lower() == 'indofood' else 'Wings Group'
        
        # product name
        pname = clean_name(row['nama_produk'])
        
        # pack size
        pack_size = extract_pack_size(pname)
        
        # prices
        orig = float(row['harga_coret'])
        final = float(row['harga_diskon'])
        if orig == 0 or orig < final:
            orig = final
            
        # discount pct
        if orig > 0 and orig > final:
            disc = round(((orig - final) / orig) * 100, 2)
        else:
            disc = 0.0
            
        # promo type
        promo_type = get_promo_type(orig, final, pname)
        
        # flavor
        flavor = get_flavor(pname)
        
        # sku
        sku = generate_sku(pname, idx)
        
        # platform
        plat = 'Shopee' if 'shopee' in str(row['e_commerce']).lower() else 'Tokopedia'
        
        row_str = f"2026-05-29,{company},{row['brand']},{pname},{sku},{pack_size},{int(orig)},{int(final)},{disc:.2f},Official Store,{plat},Jawa Timur,Surabaya,{promo_type},NULL,{row['tipe_kemasan']},{flavor},2026-05-01,2026-05-31,{row['jumlah_terjual']}"
        print(row_str)

if __name__ == '__main__':
    main()
