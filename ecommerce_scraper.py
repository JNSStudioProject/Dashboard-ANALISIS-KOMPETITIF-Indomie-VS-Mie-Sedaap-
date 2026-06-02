import time
import random
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class ECommerceScraper:
    def __init__(self, search_query=""):
        self.search_query = search_query
        self.base_url = "https://shopee.co.id/search?keyword="
        self.driver = self._setup_driver()

    def _setup_driver(self):
        """Setup konfigurasi WebDriver dengan perlindungan anti-bot."""
        options = Options()
        
        # 1. PENGATURAN PENTING: Mencegah browser langsung tertutup (detach = True)
        options.add_experimental_option("detach", True)
        
        # 2. Menyamarkan automation (Anti-bot detection)
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # 3. PENGATURAN SESI (PENTING UNTUK SHOPEE)
        # Menyimpan profil Chrome lokal agar kita bisa login secara manual satu kali
        # dan bot akan mengingat sesi tersebut (cookies) untuk run berikutnya.
        import os
        profile_path = os.path.join(os.getcwd(), "chrome_profile")
        options.add_argument(f"user-data-dir={profile_path}")
        
        # Inisialisasi WebDriver
        driver = webdriver.Chrome(options=options)
        
        # Mengubah navigator.webdriver menjadi undefined melalui CDP (Chrome DevTools Protocol)
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })
            """
        })
        
        driver.maximize_window()
        return driver

    def _random_sleep(self, min_time=2, max_time=5):
        """
        Fungsi untuk menambahkan jeda waktu yang realistis/acak, 
        sangat penting untuk menghindari pemblokiran (Rate Limiting).
        """
        sleep_time = random.uniform(min_time, max_time)
        print(f"[Bot] Menunggu {sleep_time:.2f} detik seperti manusia normal...")
        time.sleep(sleep_time)

    def _scroll_down_slowly(self):
        """
        Scroll perlahan untuk memuat lazy-loaded images dan elements.
        Dibatasi maksimal 15 kali scroll agar tidak nyangkut (stuck) jika halaman error.
        """
        print("[Bot] Mulai scrolling perlahan ke bawah halaman...")
        for _ in range(15):
            self.driver.execute_script("window.scrollBy(0, 600);")
            self._random_sleep(0.5, 1.0)

    def search_product(self, page_index=0):
        """Membuka halaman pencarian berdasarkan query."""
        # Shopee menggunakan sistem &page=0 untuk halaman 1, &page=1 untuk halaman 2, dst.
        url = f"{self.base_url}{self.search_query}&page={page_index}"
        print(f"[Bot] Membuka URL: {url}")
        self.driver.get(url)
        
        # Tunggu cukup lama di awal untuk melewati loading screen / captcha yang mungkin ada
        self._random_sleep(5, 8)
        
        # Lakukan scroll agar semua elemen ter-render di DOM
        self._scroll_down_slowly()

    def extract_data(self):
        """Mengekstrak informasi produk dari kartu (product card)."""
        print("[Bot] Mengekstrak data elemen produk...")
        products_data = []
        
        try:
            # Tunggu maksimal 10 detik sampai elemen nama produk muncul
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.whitespace-normal.line-clamp-2"))
            )
        except Exception:
            print("[Warning] Tidak ada produk ditemukan atau memuat terlalu lama (mungkin halaman kosong).")
            return []
            
        try:
            # Ekstraksi Super Cepat menggunakan eksekusi JavaScript secara langsung di browser
            script = """
            let results = [];
            let nameElements = document.querySelectorAll('div.whitespace-normal.line-clamp-2');
            
            nameElements.forEach(nameElem => {
                // Mundur 3 tingkat ke elemen pembungkus (parent)
                let card = nameElem.parentElement.parentElement.parentElement;
                if(card) {
                    results.push({
                        name: nameElem.innerText,
                        cardText: card.innerText
                    });
                }
            });
            return results;
            """
            
            # Selenium mengambil seluruh data sekaligus dalam hitungan milidetik
            raw_data = self.driver.execute_script(script)
            print(f"[Bot] Ekstraksi kilat berhasil. Memproses {len(raw_data)} produk...")
            
            import re
            
            for item in raw_data:
                try:
                    name = item['name']
                    card_text = item['cardText']
                    
                    # 2. Harga Coret & Diskon 
                    prices = re.findall(r'Rp[\s\n]*([\d\.]+)', card_text)
                    
                    if len(prices) >= 2:
                        strikethrough_price = "Rp " + prices[0]
                        discount_price = "Rp " + prices[1]
                    elif len(prices) == 1:
                        strikethrough_price = "N/A"
                        discount_price = "Rp " + prices[0]
                    else:
                        strikethrough_price = "N/A"
                        discount_price = "N/A"
                        
                    # 3. Jumlah Terjual
                    sold_match = re.search(r'([0-9\.,KkMRB\+]+)[\s\n]*Terjual', card_text, re.IGNORECASE)
                    if sold_match:
                        sold_count = sold_match.group(1) + " Terjual"
                    else:
                        sold_count = "N/A"
                        
                    products_data.append({
                        "Brand": self.search_query, # Kolom baru untuk penanda Mie Sedaap vs Indomie
                        "Nama Produk": name,
                        "Harga Coret": strikethrough_price,
                        "Harga Diskon": discount_price,
                        "Jumlah Terjual": sold_count
                    })
                    
                except Exception as inner_e:
                    continue
                    
        except Exception as e:
            print(f"[Error] Gagal menemukan elemen produk. Kemungkinan struktur HTML berubah. Detail: {e}")
            
        return products_data

    def get_total_pages(self):
        """Mendeteksi total halaman pencarian dari UI Shopee (misal angka 16 dari 1/16)."""
        try:
            # Elemen ini biasanya berisi angka total halaman di pojok kanan atas grid produk
            total_elem = self.driver.find_element(By.CSS_SELECTOR, ".shopee-mini-page-controller__total")
            total_pages = int(total_elem.text)
            print(f"[Bot] Berhasil mendeteksi total {total_pages} halaman yang sebenarnya.")
            return total_pages
        except Exception:
            print("[Warning] Gagal mendeteksi total halaman dari UI. Menggunakan batas aman 5 halaman.")
            return 5

    def save_to_csv(self, data, filename="raw_data.csv"):
        """Menyimpan dictionary/list of dict menjadi file CSV menggunakan Pandas."""
        if not data:
            print("[Warning] Data kosong, tidak ada file CSV yang disimpan.")
            return
            
        print(f"[Bot] Menyimpan {len(data)} baris data ke {filename}...")
        df = pd.DataFrame(data)
        df.to_csv(filename, index=False, encoding='utf-8')
        print("[Bot] Proses penyimpanan berhasil!")

    def quit(self):
        """Menutup webdriver secara manual. Berguna jika detach diset ke False nantinya."""
        self.driver.quit()

# --- MAIN EXECUTION (Phase 1: Task 1, 2, 3) ---
if __name__ == "__main__":
    # Target kompetitor yang ingin dibandingkan
    keywords = ["Mie Sedaap", "Indomie"]
    
    # Inisiasi scraper bot SATU KALI agar browser tidak membuka banyak jendela baru
    scraper = ECommerceScraper(search_query="")
    
    master_data = []
    
    for keyword in keywords:
        print(f"\n=================================================")
        print(f" MULAI MENCARI: {keyword.upper()}")
        print(f"=================================================")
        
        # Ubah kata kunci pencariannya
        scraper.search_query = keyword
        
        try:
            scraper.search_product(page_index=0)
            max_pages = scraper.get_total_pages()
            
            # Bot akan otomatis mengambil SEMUA halaman yang terdeteksi secara dinamis.
            # Tidak ada batasan halaman — bot berhenti sendiri ketika halaman sudah habis.
                
            all_extracted_data = []
            
            for current_page_index in range(0, max_pages):
                real_page_number = current_page_index + 1
                print(f"\n--- [{keyword}] Halaman {real_page_number}/{max_pages} ---")
                
                if current_page_index > 0:
                    scraper.search_product(page_index=current_page_index)
                
                page_data = scraper.extract_data()
                
                if not page_data:
                    break
                    
                all_extracted_data.extend(page_data)
                
                # Simpan terus setiap 1 halaman selesai
                # Agar CSV langsung terupdate dengan gabungan kedua brand
                scraper.save_to_csv(master_data + all_extracted_data, filename="data_kompetitor_raw.csv")
            
            # Setelah 1 brand selesai, satukan ke master data
            master_data.extend(all_extracted_data)
            
        except Exception as e:
            print(f"\n[Terjadi Kesalahan pada {keyword}] {e}")
            
    print(f"\n[SELESAI] Total data gabungan: {len(master_data)} baris.")
    print("Silakan jalankan data_processor.py untuk memasukkan ke database.")
        # Opsional: Tutup browser jika ada error fatal
        # scraper.quit()
