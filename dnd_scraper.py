#!/usr/bin/env python3
"""
D&D 4e Database Scraper
Scarica ricorsivamente tutti i file da iws.mx/dnd/4e_database_files/
"""

import requests
from bs4 import BeautifulSoup
from pathlib import Path
import time
from urllib.parse import urljoin, urlparse
import logging

# Configurazione
BASE_URL = "https://iws.mx/dnd/4e_database_files/"
OUTPUT_DIR = Path("dnd_4e_database")
DELAY_SECONDS = 0.5  # Pausa tra le richieste per non sovraccaricare il server

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)

def download_file(url, local_path):
    """Scarica un singolo file"""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # Crea directory se non esiste
        local_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Salva il file
        with open(local_path, 'wb') as f:
            f.write(response.content)
        
        logging.info(f"✓ Scaricato: {local_path.name} ({len(response.content)} bytes)")
        return True
    except Exception as e:
        logging.error(f"✗ Errore scaricando {url}: {e}")
        return False

def get_directory_listing(url):
    """Ottiene la lista di file e cartelle da una directory Apache"""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        files = []
        directories = []
        
        for link in soup.find_all('a'):
            href = link.get('href', '')
            
            # Ignora parent directory e link assoluti
            if not href or href in ['..', '/', '']:
                continue
            
            # Skip protocolli non-http (mailto:, ftp:, etc.)
            if ':' in href and not href.startswith(('http://', 'https://', './', '../')):
                continue
            
            # Skip link assoluti esterni
            if href.startswith('http') and not href.startswith(BASE_URL):
                continue
            
            full_url = urljoin(url, href)
            
            # Assicurati che il link sia sotto BASE_URL
            if not full_url.startswith(BASE_URL):
                continue
            
            # Se termina con /, è una directory
            if href.endswith('/'):
                directories.append((href.rstrip('/'), full_url))
            else:
                files.append((href, full_url))
        
        return files, directories
    
    except Exception as e:
        logging.error(f"Errore leggendo directory {url}: {e}")
        return [], []

def scrape_recursive(url, base_output_dir, current_path="", visited=None):
    """Scarica ricorsivamente tutti i file"""
    
    if visited is None:
        visited = set()
    
    # Evita loop
    if url in visited:
        logging.debug(f"⊘ Directory già visitata: {url}")
        return
    
    visited.add(url)
    
    logging.info(f"\n{'='*60}")
    logging.info(f"Esplorando: {url}")
    logging.info(f"{'='*60}")
    
    files, directories = get_directory_listing(url)
    
    # Scarica tutti i file nella directory corrente
    for filename, file_url in files:
        local_path = base_output_dir / current_path / filename
        download_file(file_url, local_path)
        time.sleep(DELAY_SECONDS)  # Pausa tra i download
    
    # Esplora ricorsivamente le sottodirectory
    for dirname, dir_url in directories:
        new_path = str(Path(current_path) / dirname) if current_path else dirname
        scrape_recursive(dir_url, base_output_dir, new_path, visited)

def main():
    print("""
╔═══════════════════════════════════════════════════════════╗
║         D&D 4e Database Scraper                          ║
║         Downloading from iws.mx                           ║
╚═══════════════════════════════════════════════════════════╝
    """)
    
    logging.info(f"Inizio download da: {BASE_URL}")
    logging.info(f"Directory di output: {OUTPUT_DIR.absolute()}")
    
    # Crea directory di output
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    # Inizia lo scraping ricorsivo
    try:
        scrape_recursive(BASE_URL, OUTPUT_DIR)
        print(f"\n{'='*60}")
        print("✓ Download completato!")
        print(f"✓ File salvati in: {OUTPUT_DIR.absolute()}")
        print(f"{'='*60}")
    except KeyboardInterrupt:
        print("\n\n⚠ Download interrotto dall'utente")
    except Exception as e:
        logging.error(f"Errore durante lo scraping: {e}")

if __name__ == "__main__":
    main()
