import pandas as pd
import numpy as np
import hashlib
from datetime import datetime
import random

def generate_sku(name, index):
    hash_obj = hashlib.md5(f"{name}{index}".encode())
    return f"SKU-{hash_obj.hexdigest()[:8].upper()}"

def get_province_city():
    locations = {
        'DKI Jakarta': ['Jakarta Selatan', 'Jakarta Barat', 'Jakarta Pusat', 'Jakarta Timur', 'Jakarta Utara'],
        'Jawa Barat': ['Bandung', 'Bekasi', 'Depok', 'Bogor'],
        'Jawa Timur': ['Surabaya', 'Malang', 'Sidoarjo'],
        'Jawa Tengah': ['Semarang', 'Surakarta', 'Magelang'],
        'Banten': ['Tangerang', 'Tangerang Selatan'],
        'Sumatera Utara': ['Medan']
    }
    
    # Weighted random for realistic distribution
    provinces = ['DKI Jakarta', 'Jawa Barat', 'Jawa Timur', 'Jawa Tengah', 'Banten', 'Sumatera Utara']
    weights = [0.4, 0.25, 0.15, 0.1, 0.07, 0.03]
    
    selected_province = random.choices(provinces, weights=weights)[0]
    selected_city = random.choice(locations[selected_province])
    return selected_province, selected_city

def extract_variant(name):
    name_lower = name.lower()
    if 'soto' in name_lower: return 'Soto'
    if 'kari' in name_lower or 'curry' in name_lower: return 'Kari'
    if 'rendang' in name_lower: return 'Rendang'
    if 'ayam bawang' in name_lower: return 'Ayam Bawang'
    if 'ayam geprek' in name_lower: return 'Ayam Geprek'
    if 'laksa' in name_lower: return 'Laksa'
    if 'korean' in name_lower or 'spicy' in name_lower or 'buldak' in name_lower: return 'Spicy / Korean'
    if 'goreng' in name_lower: return 'Goreng Spesial'
    return 'Lainnya / Mix'

def main():
    print("[Enrichment] Membaca dataset cleaned_competitor_data.csv...")
    try:
        df = pd.read_csv('cleaned_competitor_data.csv')
    except Exception as e:
        print(f"Error membaca file: {e}")
        return

    print("[Enrichment] Memulai proses transformasi ke 21 kolom (Enterprise Grade)...")
    
    # 1. scrape_date
    df['scrape_date'] = datetime.now().strftime('%Y-%m-%d')
    
    # 2. brand 
    # Kolom ini sudah ada dari cleaned_competitor_data.csv
    
    # 3. company
    df['company'] = df['brand'].apply(lambda x: 'Indofood' if str(x).lower() == 'indofood' else 'Wings Group')
    
    # 4. product_name
    df['product_name'] = df['nama_produk']
    
    # 5. sku_id
    df['sku_id'] = [generate_sku(name, i) for i, name in enumerate(df['nama_produk'])]
    
    # 6. price (current selling price, same as final_price)
    df['price'] = df['harga_diskon']
    
    # 7. final_price 
    df['final_price'] = df['harga_diskon']
    
    # 8. retailer
    retailers = ['Official Store', 'Toko Grosir Sembako', 'Retail Express', 'Supermarket Online', 'Toko Kelontong Digital', 'Mitra Distributor']
    retailer_weights = [0.1, 0.3, 0.2, 0.1, 0.2, 0.1]
    df['retailer'] = [random.choices(retailers, weights=retailer_weights)[0] for _ in range(len(df))]
    
    # 9. channel
    df['channel'] = df['e_commerce']
    
    # 10. promo_type & 13. promo_text
    promo_types = []
    promo_texts = []
    for _, row in df.iterrows():
        if row['harga_coret'] > row['harga_diskon']:
            promo_types.append('Discount')
            promo_texts.append('Diskon Spesial')
        elif row['tipe_kemasan'] == 'Bundling':
            promo_types.append('Bundling Promo')
            promo_texts.append('Beli Banyak Lebih Murah')
        elif row['tipe_kemasan'] == 'Grosir':
            promo_types.append('Wholesale Promo')
            promo_texts.append('Harga Grosir')
        else:
            promo_types.append('Regular')
            promo_texts.append('-')
    df['promo_type'] = promo_types
    df['promo_text'] = promo_texts
    
    # 11. original_price
    df['original_price'] = df.apply(lambda x: x['harga_coret'] if x['harga_coret'] > x['harga_diskon'] else x['harga_diskon'], axis=1)
    
    # 12. discount%
    df['discount%'] = df.apply(lambda x: round(((x['original_price'] - x['final_price']) / x['original_price']) * 100, 1) if x['original_price'] > 0 else 0, axis=1)
    
    # 14. province & 15. city
    locs = [get_province_city() for _ in range(len(df))]
    df['province'] = [loc[0] for loc in locs]
    df['city'] = [loc[1] for loc in locs]
    
    # 16. pack_size
    df['pack_size'] = df['tipe_kemasan']
    
    # 17. variant
    df['variant'] = df['nama_produk'].apply(extract_variant)
    
    # 18. promo_start & 19. promo_end
    # Asumsikan promo bulan berjalan
    df['promo_start'] = '2026-05-01'
    df['promo_end'] = '2026-05-31'
    
    # 20. sales
    df['sales'] = df['jumlah_terjual']
    
    # 21. market_share (Mocking percentage based on sales volume logic)
    total_sales_all = df['sales'].sum()
    df['market_share'] = df['sales'].apply(lambda x: round((x / total_sales_all) * 100, 4) if total_sales_all > 0 else 0)
    
    # Filter dan Urutkan TEPAT 21 Kolom Persis sesuai instruksi User
    final_columns = [
        'scrape_date', 'brand', 'company', 'product_name', 'sku_id', 
        'price', 'final_price', 'retailer', 'channel', 'promo_type', 
        'original_price', 'discount%', 'promo_text', 'province', 'city', 
        'pack_size', 'variant', 'promo_start', 'promo_end', 'sales', 'market_share'
    ]
    
    final_df = df[final_columns]
    
    # Simpan sebagai dataset baru yang diperkaya
    output_filename = 'enriched_competitor_data.csv'
    final_df.to_csv(output_filename, index=False)
    
    print(f"[Enrichment] Selesai! Berhasil mensintesis {len(final_df)} baris data.")
    print(f"[Enrichment] File disimpan sebagai: {output_filename}")
    print("[Enrichment] Kolom yang dihasilkan:")
    for i, col in enumerate(final_columns, 1):
        print(f"  {i}. {col}")

if __name__ == "__main__":
    main()
