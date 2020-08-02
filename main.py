import time
import urllib.request
import signal

import requests
from bs4 import BeautifulSoup
import dryscrape
import webkit_server

# Pagina principale da cui fare scraping
url = 'http://iws.mx/dnd/?list'
# URL di base per le varie pagine
baseUrl = 'http://iws.mx/dnd/'

# Lista di categorie da ignorare
categorieDaSaltare = ['Everything', 'Glossary']
categorieEstratte = []

# Configurazione del server in modo da evitare memory leak
dryscrape.start_xvfb()
server = webkit_server.Server()
server_conn = webkit_server.ServerConnection(server=server)
driver = dryscrape.driver.webkit.Driver(connection=server_conn)
session = dryscrape.Session(driver=driver)


def main():
    # Avvio la sessione
    session = dryscrape.Session()
    # Apro la pagina
    session.visit(url)
    # Attendo il caricamento
    print("[", time.asctime(time.localtime(time.time())),
          "] Attendo che venga caricata la pagina ", url)
    time.sleep(15)  # Serve a non far crashare (vedi FIXME seguente)

    # Recupero il corpo della richiesta, cioé il codice della pagina
    response = session.body()
    # Uso il parser per formattare in HTML
    soup = BeautifulSoup(response, 'html.parser')

    # FIXME: Se la pagina non è caricata, genera errore e scoppia tutto

    # Ricerca degli elementi

    # Div contenente l'elenco dei tasti che sarebbero le categorie
    divs = soup.find('div', id='act_list_pnl_category')
    divs = divs.children
    for div in divs:
        if (div.b.get_text() not in categorieDaSaltare):
            text = div.b.get_text()
            # Elimino gli spazi consecutivi, all'inizio ed alla fine
            text = text.strip()
            # Elimino gli spazi intermedi
            text = text.replace(' ', '')
            # Elimino la parte destra dello slash
            if ('/' in text):
                text = text[0:text.index('/')]
                # Elimino gli spazi intermedi
                text = text.replace(' ', '')
            # Converto tutto in minuscole
            text = text.lower()
            text = text.strip()
            categorieEstratte.append(text)
    print('Categorie estratte: \n', categorieEstratte)

    # Apro una pagina per ogni categoria
    for categoria in categorieEstratte:
        link = url + '.name.' + categoria
        # TODO: Fare scraping di ogni categoria
    # DEBUG: Per ora provo su una sola categoria
    link = url + '.name.' + categorieEstratte[0]
    scrapingPagina(link)


def scrapingPagina(link):
    pagineElementi = []
    session = dryscrape.Session()
    session.visit(link)
    time.sleep(5)
    response = session.body()
    soup = BeautifulSoup(response, 'html.parser')
    tbody = soup.select('table#act_list_table tbody')
    tbody = tbody[0]
    tbody = tbody.children
    for tr in tbody:
        pagineElementi.append(baseUrl + tr.td.a['href'])
    print('Elementi ricavati:\n', pagineElementi)


try:
    main()
finally:
    print("[", time.asctime(time.localtime(time.time())),
          "] Killo il server")
    server.kill()  # Altrimenti resta attivo
