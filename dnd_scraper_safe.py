#!/usr/bin/env python3
"""
D&D 4e Database Scraper - Safe Edition
Scarica SOLO le categorie sotto 4e_database_files senza navigazione parent
"""

import requests
from bs4 import BeautifulSoup
from pathlib import Path
import time
from urllib.parse import urljoin
import logging
from tqdm import tqdm
import json

# Configurazione
BASE_URL = "https://iws.mx/dnd/4e_database_files/"
OUTPUT_DIR = Path("dnd_4e_database")
PROGRESS_FILE = OUTPUT_DIR / ".download_progress.json"
DELAY_SECONDS = 0.5
MAX_RETRIES = 3

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper_safe.log'),
        logging.StreamHandler()
    ]
)

class DownloadTracker:
    """Traccia i file già scaricati per permettere resume"""
    
    def __init__(self, progress_file):
        self.progress_file = Path(progress_file)
        self.downloaded = self.load_progress()
    
    def load_progress(self):
        if self.progress_file.exists():
            with open(self.progress_file, 'r') as f:
                return set(json.load(f))
        return set()
    
    def save_progress(self):
        self.progress_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.progress_file, 'w') as f:
            json.dump(list(self.downloaded), f, indent=2)
    
    def is_downloaded(self, url):
        return url in self.downloaded
    
    def mark_downloaded(self, url):
        self.downloaded.add(url)
        self.save_progress()

def download_file_with_retry(url, local_path, tracker, max_retries=MAX_RETRIES):
    """Scarica un file con retry automatico"""
    
    if tracker.is_downloaded(url):
        return True
    
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=30, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            
            local_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(local_path, 'wb') as f:
                if total_size:
                    with tqdm(total=total_size, unit='B', unit_scale=True, 
                             desc=local_path.name, leave=False) as pbar:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                            pbar.update(len(chunk))
                else:
                    f.write(response.content)
            
            tracker.mark_downloaded(url)
            logging.info(f"✓ {local_path.name} ({total_size} bytes)")
            return True
            
        except Exception as e:
            if attempt < max_retries - 1:
                logging.warning(f"⚠ Tentativo {attempt + 1} fallito per {url}: {e}")
                time.sleep(2 ** attempt)
            else:
                logging.error(f"✗ Errore definitivo per {url}: {e}")
                return False
    
    return False

def get_categories():
    """Ottiene solo le categorie principali (subdirectory di 4e_database_files)"""
    try:
        response = requests.get(BASE_URL, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        categories = []
        
        for link in soup.find_all('a'):
            href = link.get('href', '')
            
            # Solo directory (finiscono con /)
            if not href.endswith('/'):
                continue
            
            # Skip parent
            if href in ['..', '/', '../']:
                continue
            
            # Skip protocolli non-http
            if ':' in href and not href.startswith(('http://', 'https://')):
                continue

            if "https://raw.githubusercontent.com/Sheep-y/" in href:
                continue

            if "https://github.com/Sheep-y/" in href:
                continue
            
            category_name = href.rstrip('/')
            category_url = urljoin(BASE_URL, href)
            
            categories.append((category_name, category_url))
        
        return categories
    
    except Exception as e:
        logging.error(f"Errore ottenendo categorie: {e}")
        return []

def get_files_in_category(category_url):
    """Ottiene tutti i file in una categoria (non ricorsivo)"""
    try:
        response = requests.get(category_url, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        files = []
        
        for link in soup.find_all('a'):
            href = link.get('href', '')
            
            # Solo file (non directory)
            if href.endswith('/'):
                continue
            
            # Skip parent
            if href in ['..', '/', '../']:
                continue
            
            # Skip protocolli non-http
            if ':' in href and not href.startswith(('http://', 'https://')):
                continue

            if "raw.githubusercontent.com/Sheep-y/" in href:
                continue

            if "github.com/Sheep-y/" in href:
                continue

            if "play.google.com/store/apps/" in href:
                continue

            if "www.youtube.com/" in href:
                continue

            if "en.wikipedia.org" in href:
                continue

            if "jquerymobile.com/" in href:
                continue
            
            file_url = urljoin(category_url, href)
            files.append((href, file_url))
        
        return files
    
    except Exception as e:
        logging.error(f"Errore leggendo categoria {category_url}: {e}")
        return []

def format_bytes(bytes_value):
    """Formatta i bytes in formato leggibile"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.2f} TB"

def main():
    print("""
╔═══════════════════════════════════════════════════════════╗
║      D&D 4e Database Scraper - SAFE Edition              ║
║          Solo categorie principali (no loop!)            ║
╚═══════════════════════════════════════════════════════════╝
    """)
    
    tracker = DownloadTracker(PROGRESS_FILE)
    
    if tracker.downloaded:
        print(f"📝 Trovati {len(tracker.downloaded)} file già scaricati\n")
    
    logging.info(f"Inizio download da: {BASE_URL}")
    logging.info(f"Directory di output: {OUTPUT_DIR.absolute()}")
    
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    # Ottieni categorie principali
    print("🔍 Ricerca categorie...")
    categories = get_categories()
    
    if not categories:
        print("❌ Nessuna categoria trovata!")
        return
    
    print(f"✓ Trovate {len(categories)} categorie:\n")
    for cat_name, _ in categories:
        print(f"   • {cat_name}")
    
    # Statistiche
    stats = {
        'files': 0,
        'categories': 0,
        'bytes': 0,
        'errors': 0
    }
    
    start_time = time.time()
    
    # Scarica file per ogni categoria
    for cat_name, cat_url in categories:
        print(f"\n{'='*60}")
        print(f"📁 Categoria: {cat_name}")
        print(f"{'='*60}")
        
        files = get_files_in_category(cat_url)
        
        if not files:
            print(f"   ⊘ Nessun file trovato")
            continue
        
        print(f"   Trovati {len(files)} file")
        stats['categories'] += 1
        
        # Scarica i file
        for filename, file_url in tqdm(files, desc=f"Download {cat_name}"):
            local_path = OUTPUT_DIR / cat_name / filename
            
            if download_file_with_retry(file_url, local_path, tracker):
                stats['files'] += 1
                if local_path.exists():
                    stats['bytes'] += local_path.stat().st_size
            else:
                stats['errors'] += 1
            
            time.sleep(DELAY_SECONDS)
    
    # Scarica anche i file root (catalog.js, index.js)
    print(f"\n{'='*60}")
    print("📋 Download file root...")
    print(f"{'='*60}")
    
    root_files = get_files_in_category(BASE_URL)
    for filename, file_url in tqdm(root_files, desc="File root"):
        local_path = OUTPUT_DIR / filename
        
        if download_file_with_retry(file_url, local_path, tracker):
            stats['files'] += 1
            if local_path.exists():
                stats['bytes'] += local_path.stat().st_size
        else:
            stats['errors'] += 1
        
        time.sleep(DELAY_SECONDS)
    
    elapsed = time.time() - start_time
    
    # Stampa risultati
    print(f"\n{'='*60}")
    print("✓ Download completato!")
    print(f"{'='*60}")
    print(f"📊 Statistiche:")
    print(f"   • File scaricati: {stats['files']}")
    print(f"   • Categorie processate: {stats['categories']}")
    print(f"   • Dimensione totale: {format_bytes(stats['bytes'])}")
    print(f"   • Errori: {stats['errors']}")
    print(f"   • Tempo impiegato: {elapsed/60:.2f} minuti")
    print(f"   • Path: {OUTPUT_DIR.absolute()}")
    print(f"{'='*60}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠ Download interrotto dall'utente")
        print("   Esegui di nuovo lo script per riprendere")
    except Exception as e:
        logging.error(f"Errore durante lo scraping: {e}")
        raise
