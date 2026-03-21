#!/usr/bin/env python3
"""
D&D 4e Database Scraper - Versione Avanzata
Con supporto per resume, progress tracking e statistiche
"""

import requests
from bs4 import BeautifulSoup
from pathlib import Path
import time
from urllib.parse import urljoin
import logging
import json
from tqdm import tqdm
import hashlib

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
        logging.FileHandler('scraper_advanced.log'),
        logging.StreamHandler()
    ]
)

class DownloadTracker:
    """Traccia i file già scaricati per permettere resume"""
    
    def __init__(self, progress_file):
        self.progress_file = Path(progress_file)
        self.downloaded = self.load_progress()
    
    def load_progress(self):
        """Carica il progresso salvato"""
        if self.progress_file.exists():
            with open(self.progress_file, 'r') as f:
                return set(json.load(f))
        return set()
    
    def save_progress(self):
        """Salva il progresso corrente"""
        self.progress_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.progress_file, 'w') as f:
            json.dump(list(self.downloaded), f, indent=2)
    
    def is_downloaded(self, url):
        """Controlla se un URL è già stato scaricato"""
        return url in self.downloaded
    
    def mark_downloaded(self, url):
        """Marca un URL come scaricato"""
        self.downloaded.add(url)
        self.save_progress()

def download_file_with_retry(url, local_path, tracker, max_retries=MAX_RETRIES):
    """Scarica un file con retry automatico"""
    
    # Skip se già scaricato
    if tracker.is_downloaded(url):
        logging.debug(f"⊘ Già scaricato: {local_path.name}")
        return True
    
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=30, stream=True)
            response.raise_for_status()
            
            # Ottieni dimensione file
            total_size = int(response.headers.get('content-length', 0))
            
            # Crea directory se non esiste
            local_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Scarica con progress bar
            with open(local_path, 'wb') as f:
                if total_size:
                    with tqdm(total=total_size, unit='B', unit_scale=True, 
                             desc=local_path.name, leave=False) as pbar:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                            pbar.update(len(chunk))
                else:
                    f.write(response.content)
            
            # Marca come scaricato
            tracker.mark_downloaded(url)
            
            logging.info(f"✓ {local_path.name} ({total_size} bytes)")
            return True
            
        except Exception as e:
            if attempt < max_retries - 1:
                logging.warning(f"⚠ Tentativo {attempt + 1} fallito per {url}: {e}")
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                logging.error(f"✗ Errore definitivo per {url}: {e}")
                return False
    
    return False

def get_directory_listing(url):
    """Ottiene la lista di file e cartelle"""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        files = []
        directories = []
        
        for link in soup.find_all('a'):
            href = link.get('href', '')
            
            # Skip link non validi
            if not href or href in ['..', '/', '']:
                continue
            
            # Skip protocolli non-http (mailto:, ftp:, etc.)
            if ':' in href and not href.startswith(('http://', 'https://', './', '../')):
                logging.debug(f"Skipping non-http link: {href}")
                continue
            
            # Skip link assoluti esterni
            if href.startswith('http') and not href.startswith(BASE_URL):
                continue
            
            full_url = urljoin(url, href)
            
            # Assicurati che il link sia sotto BASE_URL
            if not full_url.startswith(BASE_URL):
                continue
            
            if href.endswith('/'):
                directories.append((href.rstrip('/'), full_url))
            else:
                files.append((href, full_url))
        
        return files, directories
    
    except Exception as e:
        logging.error(f"Errore leggendo directory {url}: {e}")
        return [], []

def scrape_recursive(url, base_output_dir, tracker, current_path="", stats=None, visited=None):
    """Scarica ricorsivamente con tracking"""
    
    if stats is None:
        stats = {'files': 0, 'dirs': 0, 'bytes': 0, 'errors': 0}
    
    if visited is None:
        visited = set()
    
    # Evita loop - controlla se abbiamo già visitato questo URL
    if url in visited:
        logging.debug(f"⊘ Directory già visitata: {url}")
        return stats
    
    visited.add(url)
    
    logging.info(f"\n📁 Esplorando: {current_path or 'root'}")
    
    files, directories = get_directory_listing(url)
    
    stats['dirs'] += 1
    
    # Scarica file
    for filename, file_url in tqdm(files, desc=f"Files in {current_path or 'root'}", 
                                    leave=False):
        local_path = base_output_dir / current_path / filename
        
        if download_file_with_retry(file_url, local_path, tracker):
            stats['files'] += 1
            if local_path.exists():
                stats['bytes'] += local_path.stat().st_size
        else:
            stats['errors'] += 1
        
        time.sleep(DELAY_SECONDS)
    
    # Esplora sottodirectory
    for dirname, dir_url in directories:
        new_path = str(Path(current_path) / dirname) if current_path else dirname
        scrape_recursive(dir_url, base_output_dir, tracker, new_path, stats, visited)
    
    return stats

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
║      D&D 4e Database Scraper - Advanced Edition          ║
║              Downloading from iws.mx                      ║
╚═══════════════════════════════════════════════════════════╝
    """)
    
    # Inizializza tracker
    tracker = DownloadTracker(PROGRESS_FILE)
    
    if tracker.downloaded:
        print(f"📝 Trovati {len(tracker.downloaded)} file già scaricati")
        print("   Il download riprenderà da dove si era interrotto\n")
    
    logging.info(f"Inizio download da: {BASE_URL}")
    logging.info(f"Directory di output: {OUTPUT_DIR.absolute()}")
    
    # Crea directory di output
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    # Inizia lo scraping
    start_time = time.time()
    
    try:
        stats = scrape_recursive(BASE_URL, OUTPUT_DIR, tracker)
        
        elapsed = time.time() - start_time
        
        print(f"\n{'='*60}")
        print("✓ Download completato!")
        print(f"{'='*60}")
        print(f"📊 Statistiche:")
        print(f"   • File scaricati: {stats['files']}")
        print(f"   • Directory esplorate: {stats['dirs']}")
        print(f"   • Dimensione totale: {format_bytes(stats['bytes'])}")
        print(f"   • Errori: {stats['errors']}")
        print(f"   • Tempo impiegato: {elapsed/60:.2f} minuti")
        print(f"   • Path: {OUTPUT_DIR.absolute()}")
        print(f"{'='*60}")
        
    except KeyboardInterrupt:
        print("\n\n⚠ Download interrotto dall'utente")
        print("   Esegui di nuovo lo script per riprendere il download")
    except Exception as e:
        logging.error(f"Errore durante lo scraping: {e}")
        raise

if __name__ == "__main__":
    main()
