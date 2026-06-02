import time
import random
import pandas as pd
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class TokopediaScraper:
    def __init__(self, search_query=""):
        self.search_query = search_query
        self.base_url = "https://www.tokopedia.com/search?q="
        self.driver = self._setup_driver()

    def _setup_driver(self):
        """Setup konfigurasi WebDriver dengan perlindungan anti-bot."""
        options = Options()
        
        # 1. PENGATURAN PENTING: Mencegah browser langsung tertutup (detach = True)
        options.add_experimental_option("detach", True)
        
        # 2. Menyamarkan automation (Anti-bot detection Datadome Tokopedia)
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # 3. PENGATURAN SESI (PENTING UNTUK TOKOPEDIA)
        # Menyimpan profil Chrome lokal agar kita bisa login secara manual satu kali
        # dan lolos dari halaman Captcha Datadome untuk run berikutnya.
        import os
        profile_path = os.path.join(os.getcwd(), "chrome_profile_tokped")
        options.add_argument(f"user-data-dir={profile_path}")
        
        # Inisialisasi WebDriver
        driver = webdriver.Chrome(options=options)
        
        # Mengubah navigator.webdriver menjadi undefined
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
        sleep_time = random.uniform(min_time, max_time)
        print(f"[Bot] Menunggu {sleep_time:.2f} detik...")
        time.sleep(sleep_time)

    def _scroll_down_slowly(self, times=12):
        print(f"\\n[Bot] --> Mulai menggulir layar perlahan ke bawah {times} kali...")
        for i in range(times):
            self.driver.execute_script("window.scrollBy(0, 800);")
            self._random_sleep(0.5, 1.2)
            if (i+1) % 5 == 0:
                print(f"[Bot]     (Telah menggulir {i+1}/{times} kali)")

    def _click_load_more(self):
        try:
            print("[Bot] --> Memeriksa tombol 'Muat Lebih Banyak' di ujung halaman...")
            # Menggunakan XPath yang mengabaikan case-sensitivity
            xpath = "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'muat lebih banyak')]"
            load_more_btn = self.driver.find_element(By.XPATH, xpath)
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", load_more_btn)
            time.sleep(1)
            load_more_btn.click()
            print("[Bot] >>> TOMBOL DITEKAN! Memuat produk tambahan dari server Tokopedia...")
            self._random_sleep(4, 6)
            return True
        except:
            print("[Bot] --- Tombol 'Muat Lebih Banyak' tidak ditemukan (belum mentok atau sudah habis).")
            return False

    def search_product(self, page_index=1):
        """Membuka halaman pencarian Tokopedia berdasarkan query."""
        # Tokopedia menggunakan &page=1, 2, dst. dan wajib ada &st=product
        keyword_formatted = self.search_query.replace(" ", "%20")
        url = f"{self.base_url}{keyword_formatted}&st=product&page={page_index}"
        print(f"[Bot] Membuka URL: {url}")
        self.driver.get(url)
        
        # Tunggu cukup lama di awal untuk melewati loading screen / captcha Datadome
        print("[Bot] HARAP PERHATIKAN BROWSER! Jika ada Captcha, selesaikan sekarang secara manual.")
        self._random_sleep(15, 20)
        
        self._scroll_down_slowly()

    def extract_data(self):
        """Mengekstrak informasi produk dari kartu Tokopedia."""
        print("[Bot] Mengekstrak data elemen produk Tokopedia...")
        products_data = []
        
        try:
            # Menggunakan JS untuk mengambil seluruh teks dari kartu produk.
            # Tokopedia sering mengubah class, tapi struktur kartu biasanya berisi link a.
            script = """
            let results = [];
            let cards = [];
            
            // Pendekatan Universal: Cari semua elemen link (a) atau div yang membungkus produk
            let allLinks = document.querySelectorAll('a');
            allLinks.forEach(link => {
                if (link.innerText.includes('Rp') && link.innerText.length < 350) {
                    cards.push(link);
                }
            });
            
            // Fallback jika stuktur dipisah
            if(cards.length === 0) {
                let allDivs = document.querySelectorAll('div');
                allDivs.forEach(div => {
                    let text = div.innerText;
                    if(text && text.includes('Rp') && text.length > 15 && text.length < 350) {
                        if(div.querySelector('img') || div.querySelector('a')) {
                            cards.push(div);
                        }
                    }
                });
            }
            
            let seen = new Set();
            cards.forEach(card => {
                let textContent = card.innerText;
                if(!textContent || !textContent.includes('Rp')) return;
                
                // Hilangkan spasi berlebih untuk ngecek duplikat
                let cleanText = textContent.replace(/\\s+/g, ' ').trim();
                if(seen.has(cleanText)) return;
                seen.add(cleanText);
                
                let lines = textContent.split('\\n').map(l => l.trim()).filter(l => l.length > 0);
                let name = lines[0]; // fallback
                
                let nameElem = card.querySelector('[data-testid="spnSRPProdName"], [data-testid="linkProductName"], .prd_link-product-name');
                if(nameElem) {
                    name = nameElem.innerText;
                } else {
                    for(let line of lines) {
                        if(line.length > 10 && !line.includes('Rp') && !line.toLowerCase().includes('terjual') && !line.toLowerCase().includes('%')) {
                            name = line;
                            break;
                        }
                    }
                }
                
                results.push({
                    name: name,
                    cardText: textContent
                });
            });
            return results;
            """
            
            raw_data = self.driver.execute_script(script)
            print(f"[Bot] Ekstraksi berhasil. Memproses {len(raw_data)} produk...")
            
            for item in raw_data:
                try:
                    name = item['name']
                    card_text = item['cardText']
                    
                    # Cek harga: Tokopedia biasanya menampilkan harga coret dan diskon jika ada promo
                    prices = re.findall(r'Rp[\s\.]*([\d\.]+)', card_text)
                    
                    if len(prices) >= 2:
                        strikethrough_price = "Rp " + prices[0]
                        discount_price = "Rp " + prices[1]
                    elif len(prices) == 1:
                        strikethrough_price = "N/A"
                        discount_price = "Rp " + prices[0]
                    else:
                        strikethrough_price = "N/A"
                        discount_price = "N/A"
                        
                    # Cek Jumlah Terjual
                    # Regex untuk Tokopedia: "10 rb+ terjual", "500 terjual", dsb.
                    sold_match = re.search(r'([\d\.,\+]+)\s*(rb|ribu)?\s*\+?\s*terjual', card_text, re.IGNORECASE)
                    if sold_match:
                        angka = sold_match.group(1)
                        satuan = sold_match.group(2) if sold_match.group(2) else ""
                        sold_count = f"{angka} {satuan} Terjual".strip().replace("  ", " ")
                    else:
                        sold_count = "N/A"
                        
                    products_data.append({
                        "Brand": self.search_query,
                        "Nama Produk": name,
                        "Harga Coret": strikethrough_price,
                        "Harga Diskon": discount_price,
                        "Jumlah Terjual": sold_count
                    })
                    
                except Exception:
                    continue
                    
        except Exception as e:
            print(f"[Error] Gagal menemukan elemen produk Tokopedia. Detail: {e}")
            
        return products_data

    def get_total_pages(self):
        """Mendeteksi jumlah pagination. Tokopedia membatasi pencarian, fallback ke 3 halaman."""
        return 3 # Ambil 3 halaman pertama sebagai sampel aman untuk Tokopedia

    def save_to_csv(self, data, filename="data_tokopedia_raw.csv"):
        if not data:
            print("[Warning] Data kosong, tidak ada file CSV yang disimpan.")
            return
            
        print(f"[Bot] Menyimpan {len(data)} baris data ke {filename}...")
        df = pd.DataFrame(data)
        df.to_csv(filename, index=False, encoding='utf-8')
        print("[Bot] Proses penyimpanan berhasil!")

    def quit(self):
        self.driver.quit()

if __name__ == "__main__":
    keywords = ["Mie Sedaap", "Indomie"]
    scraper = TokopediaScraper(search_query="")
    master_data = []
    
    for keyword in keywords:
        print(f"\\n=================================================")
        print(f" MULAI MENCARI DI TOKOPEDIA: {keyword.upper()}")
        print(f"=================================================")
        
        scraper.search_query = keyword
        
        try:
            print(f"\\n--- [{keyword}] Memulai Mode Infinite Scroll ---")
            scraper.search_product(page_index=1)
            
            all_extracted_data = []
            
            # Ekstraksi dalam 5 batch agar bisa klik "Muat Lebih Banyak" berulang kali
            for scroll_batch in range(5):
                print(f"\\n==========================================")
                print(f" [Bot] EKSPLORASI TAHAP {scroll_batch + 1}/5")
                print(f"==========================================")
                
                scraper._scroll_down_slowly(times=10)
                
                print("[Bot] --> Mengekstrak produk yang ada di layar saat ini...")
                batch_data = scraper.extract_data()
                all_extracted_data.extend(batch_data)
                
                # Coba klik "Muat Lebih Banyak" agar di batch berikutnya produk baru bisa dimuat
                scraper._click_load_more()
                
            # Hapus duplikat dari data yang diekstrak karena kita mengekstrak di halaman yang sama berkali-kali
            unique_data = []
            seen_names = set()
            for item in all_extracted_data:
                if item['Nama Produk'] not in seen_names:
                    seen_names.add(item['Nama Produk'])
                    unique_data.append(item)
            
            print(f"\\n[Bot] YAY! Berhasil mengumpulkan {len(unique_data)} produk unik untuk {keyword}.")
            
            if len(unique_data) == 0:
                print("[Bot] Tidak ada data ditemukan. Mungkin diblokir atau selector salah.")
                continue
                
            scraper.save_to_csv(master_data + unique_data, filename="data_tokopedia_raw.csv")
            master_data.extend(unique_data)
            
        except Exception as e:
            print(f"\\n[Terjadi Kesalahan pada {keyword}] {e}")
            
    print(f"\\n[SELESAI] Total data Tokopedia: {len(master_data)} baris.")
    print("Periksa file data_tokopedia_raw.csv")
