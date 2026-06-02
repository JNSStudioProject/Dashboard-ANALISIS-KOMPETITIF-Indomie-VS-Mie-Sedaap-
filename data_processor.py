import pandas as pd
import sqlite3

def clean_price(price_str):
    """Menghapus 'Rp', titik, dan mengubah 'N/A' menjadi 0."""
    if pd.isna(price_str) or price_str == "N/A":
        return 0
    # Hapus 'Rp', spasi, dan titik ribuan
    clean_str = str(price_str).replace("Rp", "").replace(".", "").strip()
    try:
        return int(clean_str)
    except:
        return 0

def clean_sold(sold_str):
    """Mengubah format teks seperti '10RB+ Terjual' menjadi angka bulat 10000."""
    if pd.isna(sold_str) or sold_str == "N/A":
        return 0
    
    # Ambil teksnya saja, hilangkan tulisan 'TERJUAL'
    sold_str = str(sold_str).upper().replace("TERJUAL", "").strip()
    
    # Tangani suffix 'RB' (Ribu)
    if "RB" in sold_str:
        num_part = sold_str.replace("RB", "").replace("+", "").strip()
        try:
            # Kadang koma ditulis titik, misal 1,5RB -> 1.5RB
            num_part = num_part.replace(",", ".")
            return int(float(num_part) * 1000)
        except:
            return 0
    # Tangani suffix 'JT' (Juta)
    elif "JT" in sold_str:
        num_part = sold_str.replace("JT", "").replace("+", "").strip()
        try:
            num_part = num_part.replace(",", ".")
            return int(float(num_part) * 1000000)
        except:
            return 0
    else:
        # Angka biasa (misal: '54')
        clean_str = sold_str.replace(".", "").replace("+", "")
        try:
            return int(clean_str)
        except:
            return 0

def main():
    print("[Bot] Membaca file CSV mentah...")
    try:
        df_shopee = pd.read_csv("data_kompetitor_raw.csv")
        if not df_shopee.empty:
            df_shopee['e_commerce'] = 'Shopee'
    except FileNotFoundError:
        df_shopee = pd.DataFrame()
        print("[Warning] File data_kompetitor_raw.csv tidak ditemukan.")
        
    try:
        df_tokped = pd.read_csv("data_tokopedia_raw.csv")
        if not df_tokped.empty:
            df_tokped['e_commerce'] = 'Tokopedia'
    except FileNotFoundError:
        df_tokped = pd.DataFrame()
        print("[Warning] File data_tokopedia_raw.csv tidak ditemukan.")
        
    if df_shopee.empty and df_tokped.empty:
        print("[Error] Kedua sumber data kosong!")
        return
        
    df = pd.concat([df_shopee, df_tokped], ignore_index=True)
    print(f"[Bot] Berhasil menggabungkan {len(df)} baris data dari Shopee dan Tokopedia.")

    print("[Bot] Mulai fase Data Transformation (Pembersihan Data)...")
    
    # Membersihkan harga menjadi angka murni
    df['Harga Coret Bersih'] = df['Harga Coret'].apply(clean_price)
    df['Harga Diskon Bersih'] = df['Harga Diskon'].apply(clean_price)
    
    # Membersihkan jumlah terjual menjadi angka murni
    df['Jumlah Terjual Bersih'] = df['Jumlah Terjual'].apply(clean_sold)

    # (Opsional) Menghitung Nominal Diskon (Selisih Harga Coret dan Harga Diskon)
    # Jika Harga Coret 0 (alias tidak diskon), maka nominal diskon = 0
    df['Nominal Diskon'] = df.apply(
        lambda x: x['Harga Coret Bersih'] - x['Harga Diskon Bersih'] 
        if x['Harga Coret Bersih'] > x['Harga Diskon Bersih'] else 0, 
        axis=1
    )
    
    # Memilih kolom-kolom yang sudah bersih untuk dimasukkan ke Database
    final_df = df[['Brand', 'Nama Produk', 'Harga Coret Bersih', 'Harga Diskon Bersih', 'Nominal Diskon', 'Jumlah Terjual Bersih', 'e_commerce']].copy()
    
    # Mengganti nama kolom agar rapi (format snake_case yang disukai database)
    final_df.columns = ['brand', 'nama_produk', 'harga_coret', 'harga_diskon', 'nominal_diskon', 'jumlah_terjual', 'e_commerce']
    
    # Tambahkan kolom Negara karena semua data ini bersumber dari pasar lokal
    final_df['country'] = 'Indonesia'
    
    # Hapus data duplikat (Shopee sering menampilkan produk yang sama di halaman berbeda)
    total_awal = len(final_df)
    final_df = final_df.drop_duplicates(subset=['brand', 'nama_produk', 'harga_diskon'])
    
    # --- FILTER ANTI KEYWORD STUFFING ---
    # Fungsi untuk mendeteksi apakah judul produk memuat kata kunci pesaing
    def is_valid_brand(row):
        brand = str(row['brand']).lower()
        nama = str(row['nama_produk']).lower()
        
        if brand == "indomie":
            # Jika dilabeli Indomie, tapi di judul ada kata "sedaap/sedap", berarti campuran -> BUANG
            if "sedaap" in nama or "sedap" in nama:
                return False
        elif brand == "mie sedaap":
            # Jika dilabeli Mie Sedaap, tapi di judul ada kata "indomie", berarti campuran -> BUANG
            if "indomie" in nama:
                return False
                
        # Filter kata kunci negatif (iklan / produk nyasar)
        negative_keywords = ['emas', 'antam', 'logam mulia', 'certicard', 'iphone', 'laptop', 'baju', 'sepatu', 'kabel', 'panci', 'wajan', 'tas', 'motor', 'mobil', 'voucher', 'pulsa', 'kaos', 'jaket', 'minyak goreng']
        for kw in negative_keywords:
            if kw in nama:
                return False
                
        return True
        
    # Terapkan filter dan buang baris yang menghasilkan False
    final_df = final_df[final_df.apply(is_valid_brand, axis=1)]
    
    total_akhir = len(final_df)
    
    print(f"[Bot] Data dibuang (Duplikat & Produk Palsu/Campuran): {total_awal - total_akhir} baris.")
    print(f"[Bot] Tersisa {total_akhir} produk MURNI yang siap dimasukkan ke Database.")
    
    # =================================================================
    # LANGKAH 1: LABELING - Ubah nama brand ke nama perusahaan induknya
    # =================================================================
    print("\n[Bot] Langkah 1: Relabeling brand ke nama korporat...")
    final_df['brand'] = final_df['brand'].replace({
        'Mie Sedaap': 'Wings',
        'Indomie': 'Indofood'
    })
    
    # =================================================================
    # LANGKAH 3: FEATURE ENGINEERING - Membuat kolom Tipe Kemasan
    # =================================================================
    print("[Bot] Langkah 3: Feature Engineering kolom 'tipe_kemasan'...")
    import re
    
    def get_tipe_kemasan(nama_produk):
        """Mengklasifikasikan produk ke dalam 3 tipe kemasan berdasarkan nama."""
        nama = str(nama_produk).lower()
        
        # Pola GROSIR: produk dalam jumlah besar (dus, karton, kardus, isi 40, dst)
        pola_grosir = r'(karton|carton|kardus|1 dus|1dus|isi 40|x 40|x40|isi 24|x 24|x24|1 box|\bbox\b|per dus|perkarton|per karton)'
        if re.search(pola_grosir, nama):
            return 'Grosir'
        
        # Pola BUNDLING: produk multipack (isi 5, isi 3, bundling, triple pack, dst)
        pola_bundling = r'(isi 5|isi 3|isi 10|isi 12|x5|x 5|5 x|x3|x 3|3 x|x10|x 10|10 x|x12|x 12|12 x|bundling|bundle|triple pack|twin pack|2 pcs|3 pcs|5 pcs|10 pcs|12 pcs|20 pcs|2pcs|3pcs|5pcs|10pcs|12pcs|20pcs|pack isi|4 pack|pack)'
        if re.search(pola_bundling, nama):
            return 'Bundling'
        
        # Sisanya = SATUAN (produk per bungkus / eceran)
        return 'Satuan'
    
    final_df['tipe_kemasan'] = final_df['nama_produk'].apply(get_tipe_kemasan)
    
    # Tampilkan ringkasan distribusi tipe kemasan
    dist = final_df.groupby(['brand', 'tipe_kemasan']).size().reset_index(name='jumlah')
    print("\n[Bot] Distribusi Tipe Kemasan:")
    print(dist.to_string(index=False))
    
    print("[Bot] Membuka koneksi ke SQLite (database_pesaing.db)...")
    conn = sqlite3.connect('database_pesaing.db')
    
    # Simpan SEMUA data ke dalam tabel gabungan
    final_df.to_sql('tbl_competitor_prices', conn, if_exists='replace', index=False)
    
    # Pisahkan ke tabel per brand
    final_df[final_df['brand'] == 'Wings'].to_sql('tbl_mie_sedaap', conn, if_exists='replace', index=False)
    final_df[final_df['brand'] == 'Indofood'].to_sql('tbl_indomie', conn, if_exists='replace', index=False)
    
    conn.close()
    
    # =================================================================
    # LANGKAH 4: EKSPOR KE cleaned_competitor_data.csv
    # =================================================================
    # File utama sesuai rencana awal
    final_df.to_csv('cleaned_competitor_data.csv', index=False)
    
    # File per brand (untuk analisis individual)
    df_wings = final_df[final_df['brand'] == 'Wings']
    df_indofood = final_df[final_df['brand'] == 'Indofood']
    df_wings.to_csv('data_mie_sedaap_bersih.csv', index=False)
    df_indofood.to_csv('data_indomie_bersih.csv', index=False)
    
    print(f"\n[SELESAI] Semua langkah berhasil!")
    print(f"  - Wings (Mie Sedaap): {len(df_wings)} produk")
    print(f"  - Indofood (Indomie): {len(df_indofood)} produk")
    print(f"  - File utama: 'cleaned_competitor_data.csv' ({len(final_df)} produk, {len(final_df.columns)} kolom)")
    print(f"  - Kolom: {list(final_df.columns)}")

if __name__ == "__main__":
    main()
