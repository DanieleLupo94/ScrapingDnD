# 🔧 Correzioni Applicate - Version 2.0

## 🐛 Problema Identificato

Durante il primo test, lo script aveva due problemi:

### Problema 1: Tentativi di scaricare link `mailto:`
```
ERROR: No connection adapters for 'mailto:your.sheepy@gmail.com'
```
**Causa:** Lo script stava cercando di scaricare TUTTI i link trovati nelle pagine HTML, inclusi i link email (`mailto:`)

### Problema 2: Loop infinito sulle stesse directory
```
📁 Esplorando: /dnd/4e_database_files/armor
📁 Esplorando: /dnd/4e_database_files
📁 Esplorando: /dnd
📁 Esplorando: /dnd/4e_database_files/armor  ← LOOP!
```
**Causa:** Lo script seguiva anche i link "Parent Directory" (`..\`) risalendo nell'albero e rientrando ciclicamente

---

## ✅ Correzioni Applicate

### Fix 1: Filtro Link Non-HTTP ✅

**File modificati:**
- `dnd_scraper.py`
- `dnd_scraper_advanced.py`

**Cosa fa:**
```python
# Skip protocolli non-http (mailto:, ftp:, etc.)
if ':' in href and not href.startswith(('http://', 'https://', './', '../')):
    logging.debug(f"Skipping non-http link: {href}")
    continue

# Skip link assoluti esterni
if href.startswith('http') and not href.startswith(BASE_URL):
    continue

# Assicurati che il link sia sotto BASE_URL
if not full_url.startswith(BASE_URL):
    continue
```

**Risultato:** Ora ignora completamente:
- Link `mailto:`
- Link `ftp:`
- Link esterni al sito
- Qualsiasi protocollo non HTTP/HTTPS

---

### Fix 2: Tracking Directory Visitate ✅

**File modificati:**
- `dnd_scraper.py`
- `dnd_scraper_advanced.py`

**Cosa fa:**
```python
def scrape_recursive(url, ..., visited=None):
    if visited is None:
        visited = set()
    
    # Evita loop - controlla se abbiamo già visitato questo URL
    if url in visited:
        logging.debug(f"⊘ Directory già visitata: {url}")
        return stats
    
    visited.add(url)
    # ... continua con il download
```

**Risultato:** Ogni directory viene visitata UNA SOLA VOLTA

---

### Fix 3: Nuovo Script SAFE ✅

**File creato:**
- `dnd_scraper_safe.py` ⭐ **CONSIGLIATO**

**Caratteristiche:**
- ✅ **Non usa ricorsione** - elenca prima tutte le categorie, poi scarica
- ✅ **Non può andare in loop** - scarica solo categorie e file diretti
- ✅ **Più veloce** - nessuna navigazione extra
- ✅ **Più sicuro** - impossibile risalire nell'albero
- ✅ **Mantiene resume** - come lo script advanced

**Come funziona:**
1. Ottiene lista categorie da `4e_database_files/`
2. Per ogni categoria, ottiene lista file
3. Scarica tutti i file
4. Fine! Niente ricorsione, niente loop

---

## 📊 Confronto Script

| Feature | Base | Advanced | Safe |
|---------|------|----------|------|
| Resume automatico | ❌ | ✅ | ✅ |
| Progress bar | ❌ | ✅ | ✅ |
| Retry automatico | ❌ | ✅ | ✅ |
| Anti-loop | ✅ | ✅ | ✅✅ |
| Filtra mailto: | ✅ | ✅ | ✅ |
| Ricorsione | ✅ | ✅ | ❌ |
| Velocità | Media | Media | **Veloce** |
| Sicurezza loop | Buona | Buona | **Massima** |

---

## 🎯 Quale Script Usare?

### Usa `dnd_scraper_safe.py` se:
- ✅ Vuoi la massima affidabilità
- ✅ Il sito ha solo categorie dirette (come in questo caso)
- ✅ Vuoi evitare qualsiasi possibile loop
- ✅ **CONSIGLIATO per questo progetto** ⭐

### Usa `dnd_scraper_advanced.py` se:
- Hai bisogno di ricorsione profonda
- Il sito ha sottodirectory nelle sottodirectory
- Vuoi esplorare alberi complessi

### Usa `dnd_scraper.py` se:
- Vuoi lo script più semplice
- Non ti serve il resume

---

## 🚀 Comandi Aggiornati

### Metodo SAFE (Consigliato):
```bash
python dnd_scraper_safe.py
```

### Metodo Advanced (se preferisci):
```bash
python dnd_scraper_advanced.py
```

### Metodo Base:
```bash
python dnd_scraper.py
```

---

## 📝 Note Tecniche

### Pattern di link ignorati:
```python
# Ignorati:
- mailto:email@example.com
- ftp://server.com/file
- http://external-site.com
- javascript:void(0)
- #anchor-links

# Processati:
- file.js
- ./file.js
- ../file.js
- https://iws.mx/dnd/...
```

### Navigazione directory:
```
✅ SAFE: Solo directory dirette
4e_database_files/
├── armor/
├── monster/
└── power/

✅ ADVANCED: Con tracking visite
✗ BASE (old): Poteva loopare
```

---

## 🔍 Testing

Per verificare che tutto funzioni:

1. **Cancella i file già scaricati** (opzionale):
   ```bash
   rm -rf dnd_4e_database/
   rm .download_progress.json
   ```

2. **Lancia lo script safe**:
   ```bash
   python dnd_scraper_safe.py
   ```

3. **Verifica il log**:
   ```bash
   tail -f scraper_safe.log
   ```

4. **Dovresti vedere**:
   - Lista categorie all'inizio
   - Progress bar per ogni categoria
   - NO errori "mailto:"
   - NO loop su stesse directory

---

## ✅ Checklist Post-Fix

- [x] Fix filtro link mailto
- [x] Fix tracking directory visitate
- [x] Creato script safe
- [x] Testato su struttura iws.mx
- [x] Documentato tutte le modifiche
- [x] Aggiornato README

---

## 🆘 Se Hai Ancora Problemi

1. **Controlla i log**: `scraper_safe.log`
2. **Verifica la connessione**: ping iws.mx
3. **Aumenta il timeout**: modifica `timeout=30` → `timeout=60`
4. **Riduci il delay**: modifica `DELAY_SECONDS = 0.5` → `0.2`

---

## 🎉 Risultato Atteso

Dopo il fix dovresti vedere:
```
🔍 Ricerca categorie...
✓ Trovate 20 categorie:
   • armor
   • background
   • class
   ...

============================================================
📁 Categoria: armor
============================================================
   Trovati 3 file
Download armor: 100%|████████████| 3/3 [00:05<00:00]

============================================================
📁 Categoria: monster
============================================================
   Trovati 20 file
Download monster: 100%|████████████| 20/20 [01:30<00:00]

...

✓ Download completato!
```

**Niente loop, niente errori mailto!** 🎊
