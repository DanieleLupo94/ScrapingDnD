#!/usr/bin/env python3
"""
D&D 4e Data Parser
Estrae i dati JSON dai file JavaScript scaricati
"""

import json
import re
from pathlib import Path
from collections import defaultdict
import logging

# Configurazione
INPUT_DIR = Path("dnd_4e_database")
OUTPUT_DIR = Path("dnd_4e_parsed_data")

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)

def extract_json_from_js(js_content):
    """
    Estrae dati JSON da file JavaScript.
    I file hanno pattern tipo: var data_monster_0 = { ... }
    """
    # Prova diversi pattern
    patterns = [
        r'=\s*(\{[\s\S]*\})\s*;?\s*$',  # Pattern generico per oggetti
        r'=\s*(\[[\s\S]*\])\s*;?\s*$',  # Pattern per array
    ]
    
    for pattern in patterns:
        match = re.search(pattern, js_content, re.MULTILINE)
        if match:
            try:
                json_str = match.group(1)
                data = json.loads(json_str)
                return data
            except json.JSONDecodeError as e:
                logging.debug(f"JSONDecodeError con pattern {pattern}: {e}")
                continue
    
    return None

def parse_js_file(file_path):
    """Parsa un singolo file JavaScript"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        data = extract_json_from_js(content)
        
        if data:
            return data
        else:
            logging.warning(f"⚠ Nessun JSON trovato in: {file_path.name}")
            return None
            
    except Exception as e:
        logging.error(f"✗ Errore parsando {file_path}: {e}")
        return None

def parse_category(category_path):
    """Parsa tutti i file in una categoria"""
    logging.info(f"\n📁 Parsing categoria: {category_path.name}")
    
    all_data = []
    js_files = list(category_path.glob("*.js"))
    
    if not js_files:
        logging.info(f"   ⊘ Nessun file .js trovato")
        return None
    
    for js_file in sorted(js_files):
        logging.info(f"   • {js_file.name}")
        data = parse_js_file(js_file)
        
        if data:
            # Se è un oggetto con entries, estrai entries
            if isinstance(data, dict) and 'entries' in data:
                all_data.extend(data['entries'])
            # Se è un array, aggiungilo direttamente
            elif isinstance(data, list):
                all_data.extend(data)
            # Se è un oggetto singolo, aggiungilo
            elif isinstance(data, dict):
                all_data.append(data)
    
    if all_data:
        logging.info(f"   ✓ Trovate {len(all_data)} entries")
        return all_data
    
    return None

def save_parsed_data(category_name, data):
    """Salva i dati parsati in formato JSON"""
    output_path = OUTPUT_DIR / f"{category_name}.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logging.info(f"   ✓ Salvato: {output_path}")
        return True
    except Exception as e:
        logging.error(f"   ✗ Errore salvando {output_path}: {e}")
        return False

def generate_summary(all_categories_data):
    """Genera un file di riepilogo con statistiche"""
    summary = {
        'total_categories': len(all_categories_data),
        'categories': {}
    }
    
    total_entries = 0
    
    for category, data in all_categories_data.items():
        count = len(data) if data else 0
        total_entries += count
        summary['categories'][category] = {
            'entries': count,
            'sample': data[0] if data and len(data) > 0 else None
        }
    
    summary['total_entries'] = total_entries
    
    # Salva summary
    summary_path = OUTPUT_DIR / "_summary.json"
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    return summary

def main():
    print("""
╔═══════════════════════════════════════════════════════════╗
║            D&D 4e Data Parser                             ║
║       Estrae JSON dai file JavaScript                     ║
╚═══════════════════════════════════════════════════════════╝
    """)
    
    if not INPUT_DIR.exists():
        print(f"❌ Errore: Directory {INPUT_DIR} non trovata!")
        print(f"   Prima esegui lo scraper per scaricare i dati.")
        return
    
    logging.info(f"Input directory: {INPUT_DIR.absolute()}")
    logging.info(f"Output directory: {OUTPUT_DIR.absolute()}")
    
    # Trova tutte le categorie (subdirectory)
    categories = [d for d in INPUT_DIR.iterdir() if d.is_dir()]
    
    if not categories:
        print(f"❌ Nessuna categoria trovata in {INPUT_DIR}")
        return
    
    logging.info(f"\n📊 Trovate {len(categories)} categorie da parsare")
    
    all_categories_data = {}
    
    # Parsa ogni categoria
    for category_path in sorted(categories):
        category_name = category_path.name
        data = parse_category(category_path)
        
        if data:
            all_categories_data[category_name] = data
            save_parsed_data(category_name, data)
    
    # Genera summary
    print("\n" + "="*60)
    print("📊 Generazione riepilogo...")
    summary = generate_summary(all_categories_data)
    
    # Stampa statistiche finali
    print("="*60)
    print("✓ Parsing completato!")
    print("="*60)
    print(f"📁 Categorie processate: {summary['total_categories']}")
    print(f"📝 Totale entries: {summary['total_entries']}")
    print(f"\n📂 Output salvato in: {OUTPUT_DIR.absolute()}")
    print("\nDettaglio per categoria:")
    for cat, info in sorted(summary['categories'].items()):
        print(f"   • {cat:20s}: {info['entries']:5d} entries")
    print("="*60)
    
    # Parsa anche i file root (catalog.js, index.js)
    logging.info("\n📋 Parsing file root...")
    root_files = list(INPUT_DIR.glob("*.js"))
    for js_file in root_files:
        logging.info(f"   • {js_file.name}")
        data = parse_js_file(js_file)
        if data:
            save_parsed_data(js_file.stem, data)

if __name__ == "__main__":
    main()
