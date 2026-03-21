# D&D 4e Database Scraper

Script Python per scaricare l'intero database di D&D 4a edizione da iws.mx

## 🚀 Installazione Rapida

### 1. Installa Python
Assicurati di avere Python 3.7 o superiore installato.

Verifica con:
```bash
python --version
# oppure
python3 --version
```

### 2. Installa le dipendenze
```bash
pip install -r requirements.txt
# oppure
pip3 install -r requirements.txt
```

## 📦 Script Disponibili

### Script Base (`dnd_scraper.py`)
Versione semplice e diretta. Ideale per iniziare.

```bash
python dnd_scraper.py
```

**Caratteristiche:**
- Download ricorsivo di tutti i file
- Logging dettagliato
- Pausa automatica tra le richieste

### Script Avanzato (`dnd_scraper_advanced.py`) ⭐ CONSIGLIATO
Versione con funzionalità aggiuntive.

```bash
python dnd_scraper_advanced.py
```

**Caratteristiche:**
- ✅ **Resume automatico**: se interrompi, riprende da dove si era fermato
- ✅ **Progress bar** per ogni file
- ✅ **Retry automatico** in caso di errori temporanei
- ✅ **Statistiche finali** complete
- ✅ **Gestione errori** migliorata

## 📁 Struttura Output

I file verranno salvati in questa struttura:

```
dnd_4e_database/
├── armor/
│   ├── file1.js
│   └── file2.js
├── monster/
│   ├── monster_0.js
│   ├── monster_1.js
│   └── ...
├── power/
├── race/
├── weapon/
└── ...
```

## 🎮 Come Usare

### Opzione 1: Download Base
```bash
python dnd_scraper.py
```

Lo script:
1. Si connette a `https://iws.mx/dnd/4e_database_files/`
2. Esplora tutte le cartelle (armor, monster, power, etc.)
3. Scarica tutti i file .js e altri formati
4. Li salva in `dnd_4e_database/`

### Opzione 2: Download Avanzato (Consigliato)
```bash
python dnd_scraper_advanced.py
```

**Vantaggi:**
- Se il download viene interrotto (Ctrl+C, perdita connessione, etc.), 
  puoi rilanciare lo script e riprenderà da dove si era fermato
- Mostra progress bar per ogni file
- Statistiche finali dettagliate

### Interrompere il Download
Premi `Ctrl+C` per interrompere.

Con lo script avanzato, puoi riprendere in qualsiasi momento semplicemente 
rilanciando il comando!

## ⚙️ Configurazione

Puoi modificare questi parametri negli script:

```python
BASE_URL = "https://iws.mx/dnd/4e_database_files/"  # URL di partenza
OUTPUT_DIR = Path("dnd_4e_database")                # Dove salvare i file
DELAY_SECONDS = 0.5                                  # Pausa tra le richieste
MAX_RETRIES = 3                                      # Tentativi in caso di errore
```

## 📊 Cosa Scarica?

Lo script scarica **tutte** le seguenti categorie:

- 🛡️ **armor/** - Armature
- 🎨 **background/** - Background dei personaggi
- ⚔️ **class/** - Classi
- 🐾 **companion/** - Companion
- ⛪ **deity/** - Divinità
- 🦠 **disease/** - Malattie
- 🏆 **epicdestiny/** - Destini Epici
- 🎯 **feat/** - Talenti
- 📖 **glossary/** - Glossario
- 🔧 **implement/** - Implement
- 🎒 **item/** - Oggetti
- 🐉 **monster/** - Mostri
- 🛤️ **paragonpath/** - Paragon Path
- ☠️ **poison/** - Veleni
- ⚡ **power/** - Poteri
- 👥 **race/** - Razze
- 📜 **ritual/** - Rituali
- 🎭 **theme/** - Temi
- 🪤 **trap/** - Trappole
- 🗡️ **weapon/** - Armi

Più i file indice:
- 📋 **catalog.js** - Catalogo generale
- 📋 **index.js** - Indice principale (933KB!)

## 🐛 Risoluzione Problemi

### Errore: "ModuleNotFoundError"
```bash
pip install -r requirements.txt
```

### Errore: "Permission denied"
Esegui con permessi da amministratore oppure cambia `OUTPUT_DIR`

### Download molto lento
Aumenta `DELAY_SECONDS` per essere più "gentile" con il server

### Script si blocca
- Premi Ctrl+C per interrompere
- Usa lo script avanzato per il resume automatico

## 📝 Log

Tutti gli script creano file di log:
- `scraper.log` - Script base
- `scraper_advanced.log` - Script avanzato

Utili per debug e per vedere cosa è stato scaricato.

## 🎯 Prossimi Passi

Una volta scaricati tutti i file, potrai:

1. **Parsare i dati**: Estrarre JSON dai file .js
2. **Creare un database**: Importare in SQLite/PostgreSQL
3. **Sviluppare un'app**: Usare i dati per la tua applicazione

Vuoi che prepari anche gli script per queste fasi successive? 😊

## ⚖️ Note Legali

Questi script sono per uso educativo e personale. Rispetta i termini di 
servizio del sito e il copyright dei contenuti di D&D.

## 🤝 Supporto

Per problemi o domande, consulta i log generati dagli script.
