# 🚀 Quick Start - Inizia in 5 minuti!

## ⚡ Setup Veloce

### Windows:
```batch
1. Scarica e installa Python da python.org (se non ce l'hai già)
2. Estrai tutti i file in una cartella
3. Doppio click su: run.bat
4. Seleziona opzione 1 (Installa dipendenze)
5. Seleziona opzione 3 (Download database)
6. Aspetta... ☕
7. Seleziona opzione 4 (Parsa i dati)
```

### Linux / Mac:
```bash
# Assicurati di avere Python 3.7+
python3 --version

# Installa dipendenze
pip3 install -r requirements.txt

# Scarica tutto
python3 dnd_scraper_advanced.py

# Parsa i dati
python3 dnd_parser.py
```

## 📦 Cosa otterrai:

Dopo l'esecuzione avrai due cartelle:

### `dnd_4e_database/` 
File JavaScript originali scaricati dal sito, organizzati per categoria:
```
dnd_4e_database/
├── monster/
│   ├── data_0.js
│   ├── data_1.js
│   └── ...
├── power/
├── race/
└── ...
```

### `dnd_4e_parsed_data/`
Dati puliti in formato JSON, pronti per essere usati:
```
dnd_4e_parsed_data/
├── monster.json      ← Tutti i mostri in JSON
├── power.json        ← Tutti i poteri in JSON
├── race.json         ← Tutte le razze in JSON
├── weapon.json       ← Tutte le armi in JSON
└── _summary.json     ← Statistiche generali
```

## 🎯 Quanto tempo ci vuole?

- **Download completo**: ~10-30 minuti (dipende dalla connessione)
- **Parsing**: ~1-5 minuti
- **Totale**: < 1 ora

## 💡 Tips:

1. **Lo script si è interrotto?** 
   Nessun problema! Rilancia lo script avanzato e riprenderà da dove si era fermato.

2. **Vuoi vedere i log?**
   Controlla i file `scraper_advanced.log` e `scraper.log`

3. **Errori durante il download?**
   - Controlla la connessione internet
   - Prova ad aumentare `DELAY_SECONDS` negli script
   - Alcuni file potrebbero essere temporaneamente non disponibili

## 📊 Cosa fare dopo?

Una volta scaricato e parsato tutto:

1. **Esplora i JSON** in `dnd_4e_parsed_data/`
2. **Leggi `PIANO_COMPLETO.md`** per i prossimi passi
3. **Decidi** che tipo di app vuoi sviluppare
4. **Chiedi aiuto** per la fase successiva (database, UI, etc.)

## 🆘 Problemi comuni:

### "ModuleNotFoundError: No module named 'requests'"
```bash
pip install -r requirements.txt
```

### "Permission denied" 
- Windows: Esegui come amministratore
- Linux/Mac: Usa `sudo` o cambia cartella di output

### "Connection timeout"
Aumenta il timeout negli script:
```python
response = requests.get(url, timeout=60)  # Da 30 a 60 secondi
```

### Download lentissimo?
Riduci il delay:
```python
DELAY_SECONDS = 0.2  # Invece di 0.5
```
(Ma sii gentile con il server! 😊)

## ✅ Checklist:

- [ ] Python installato
- [ ] Dipendenze installate (`pip install -r requirements.txt`)
- [ ] Script eseguito (`dnd_scraper_advanced.py`)
- [ ] Dati parsati (`dnd_parser.py`)
- [ ] File JSON verificati in `dnd_4e_parsed_data/`
- [ ] Letto `PIANO_COMPLETO.md` per next steps

## 🎉 Pronto per la fase 2?

Quando hai finito lo scraping, dimmi:
- Quanti file hai scaricato?
- Che tipo di app vuoi creare?
- Preferisci web, mobile o desktop?

E procederemo con il database e lo sviluppo! 🚀
