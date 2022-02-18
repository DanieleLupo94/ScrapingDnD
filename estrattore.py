import requests as req

urls = ["http://iws.mx/dnd/?view=monster5452"]
"http://iws.mx/dnd/4e_database_files/monster/data19.js"

urlBase = "http://iws.mx/dnd/4e_database_files/monster/data"

def estraiIdentificativoEContenuto(riga):
    """ Restituisce l'identificativo ed il contenuto (codice HTML)

        :param riga: singola riga che rappresenta il dato
        :type riga: string
        :rtype: string, string
        :return: identificativo | HTML con le caratteristiche
    """
    identificativo = riga[0 : riga.find(":")].replace("\"", "").strip()
    contenuto = riga[riga.find(":") + 3 : ]
    contenuto = contenuto[::-1].replace(",\"", "", 1)
    contenuto = contenuto[::-1].strip()
    return identificativo, contenuto

def estraiNomeMostro(contenuto):
    """ Estrae il nome del mostro dal contenuto in HTML

        :param contenuto: codice HTML che rappresenta le caratteristiche del mostro
        :type riga: string
        :rtype: string
        :return: Nome del mostro
    """
    return contenuto[contenuto.find(">")+1:contenuto.find("<", 2)]

def estraiMostro(riga):
    """ Restituisce un dict che rappresenta il mostro

        :param riga: singola riga che rappresenta il mostro
        :type riga: string
        :rtype: dict
        :return: Mostro con le informazioni contenute nella riga in input
    """
    mostro = {}
    mostro["ID"], contenuto = estraiIdentificativoEContenuto(riga)
    mostro["Nome"] = estraiNomeMostro(contenuto)
    return mostro

# TODO: ricavare in modo automatico i numeri per le chiamate
risposta = req.get(urlBase + "19" + ".js")
with open("output", "w+", encoding="utf-8") as f:
    f.write(risposta.content.decode('utf-8'))
#print(risposta.content.decode('utf-8'))
risposta = risposta.content.decode('utf-8')
tipologia = risposta[risposta.find("\"")+1:]
tipologia = tipologia[0: tipologia.find("\"")].strip()
#print(tipologia)

contenuto = risposta[risposta.find("{")+1 : -2]
with open("outputFiltrato", "w+", encoding="utf-8") as f:
    f.write(contenuto)

righe = contenuto.strip().split("\n")
righe = righe[0:3]
for riga in righe:
    tmp = {}
    # Dato che i template cambiano in base al tipo di dato, vanno fatte più funzioni
    if "monster" in riga:
        tmp = estraiMostro(riga)
    print(tmp)