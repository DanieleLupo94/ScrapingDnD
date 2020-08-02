import time
import urllib.request
import signal

import requests
from bs4 import BeautifulSoup
import dryscrape
import webkit_server

# Pagina principale da cui fare scraping
url = 'http://iws.mx/dnd/?list'

# Lista di categorie da ignorare
categorieDaSaltare = ['Everything', 'Glossary']

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
            # Elimino gli spazi
            text = text.replace(' ', '')
            # Elimino la parte destra dello slash
            if ('/' in text):
                text = text[0:text.index('/')]
            # Converto tutto in minuscole
            text = text.lower()
            print(text)


try:
    main()
finally:
    print("[", time.asctime(time.localtime(time.time())),
          "] Killo il server")
    server.kill()  # Altrimenti resta attivo
