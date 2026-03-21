#!/bin/bash

# Colori per output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║      D&D 4e Database Scraper - Menu Principale           ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Funzione per controllare se Python è installato
check_python() {
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        echo -e "${RED}❌ Python non trovato! Installa Python 3.7 o superiore${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Python trovato: $($PYTHON_CMD --version)${NC}"
}

# Funzione per installare dipendenze
install_deps() {
    echo -e "\n${YELLOW}📦 Installazione dipendenze...${NC}"
    $PYTHON_CMD -m pip install -r requirements.txt
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Dipendenze installate con successo${NC}"
    else
        echo -e "${RED}❌ Errore nell'installazione delle dipendenze${NC}"
        exit 1
    fi
}

# Funzione per eseguire lo scraper base
run_basic_scraper() {
    echo -e "\n${BLUE}🚀 Avvio scraper base...${NC}\n"
    $PYTHON_CMD dnd_scraper.py
}

# Funzione per eseguire lo scraper avanzato
run_advanced_scraper() {
    echo -e "\n${BLUE}🚀 Avvio scraper avanzato (con resume)...${NC}\n"
    $PYTHON_CMD dnd_scraper_advanced.py
}

# Funzione per eseguire lo scraper safe
run_safe_scraper() {
    echo -e "\n${BLUE}🚀 Avvio scraper SAFE (no loop, consigliato)...${NC}\n"
    $PYTHON_CMD dnd_scraper_safe.py
}

# Funzione per parsare i dati
run_parser() {
    echo -e "\n${BLUE}🔍 Avvio parser dei dati...${NC}\n"
    $PYTHON_CMD dnd_parser.py
}

# Menu principale
show_menu() {
    echo -e "\n${YELLOW}Cosa vuoi fare?${NC}"
    echo "1) Installa dipendenze"
    echo "2) Scarica database (scraper SAFE - CONSIGLIATO) ⭐"
    echo "3) Scarica database (scraper avanzato con resume)"
    echo "4) Scarica database (scraper base)"
    echo "5) Parsa i dati scaricati (da JS a JSON)"
    echo "6) Tutto in uno (download SAFE + parsing)"
    echo "7) Esci"
    echo ""
}

# Main
check_python

while true; do
    show_menu
    read -p "Scelta [1-7]: " choice
    
    case $choice in
        1)
            install_deps
            ;;
        2)
            run_safe_scraper
            ;;
        3)
            run_advanced_scraper
            ;;
        4)
            run_basic_scraper
            ;;
        5)
            run_parser
            ;;
        6)
            echo -e "\n${BLUE}🚀 Processo completo in corso...${NC}"
            run_safe_scraper
            if [ $? -eq 0 ]; then
                run_parser
            else
                echo -e "${RED}❌ Download fallito, parsing saltato${NC}"
            fi
            ;;
        7)
            echo -e "\n${GREEN}👋 Arrivederci!${NC}\n"
            exit 0
            ;;
        *)
            echo -e "${RED}❌ Scelta non valida${NC}"
            ;;
    esac
    
    echo ""
    read -p "Premi INVIO per continuare..."
done
