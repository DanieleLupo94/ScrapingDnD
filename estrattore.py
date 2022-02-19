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

    return contenuto[contenuto.find(">")+1:contenuto.find("<", 2)].strip()

def estraiTipo(contenuto):
    """ Estrae la tipologia dallo span
    """
    if "<span class=type>" not in contenuto:
        return "-"
    return contenuto[contenuto.find("<span class=type>")+17 : contenuto.find("</span>")].strip()

def estraiEXP(contenuto):
    """ Estrai l'esperienza ottenuta con l'uccisione del mostro
    """
    if "<span class=xp>" not in contenuto:
        return "-"
    contenuto = contenuto[contenuto.find("<span class=xp>")+15 :]
    contenuto = contenuto[0 : contenuto.find("</span>")]
    return contenuto.replace("XP", "").strip()

def estraiLivello(contenuto):
    """ Estrae il livello
    """

    if "<span class=level>" not in contenuto:
        return "-"
    k = len("<span class=level>")
    contenuto = contenuto[contenuto.find("<span class=level>")+k :]
    contenuto = contenuto[0 : contenuto.find("<")]
    return contenuto.strip()

def estraiIniziativa(contenuto):

    if "Initiative" not in contenuto:
        return "-"
    k = len("Inizitiative") + 4
    contenuto = contenuto[contenuto.find("Initiative") + k : ]
    contenuto = contenuto[0 : contenuto.find("<")].strip().replace("\xa0", "")
    return contenuto

def estraiSensi(contenuto):

    if "Senses" not in contenuto:
        return "-"
    k = len("Senses")+4
    contenuto = contenuto[contenuto.find("Senses") + k : ]
    contenuto = contenuto[0 : contenuto.find("<br>")]
    return contenuto

def estraiHP(contenuto):

    if "HP" not in contenuto:
        return "-"
    k = len("HP</b>")
    contenuto = contenuto[contenuto.find("HP") + k : ]
    contenuto = contenuto[0 : contenuto.find(";")]
    return contenuto.strip()

def estraiAC(contenuto):
    if "AC" not in contenuto:
        return "-"
    if "class=bodytable" in contenuto:
        stop = ","
    else:
        stop = ";"
    k = len("AC</b>")
    contenuto = contenuto[contenuto.find("AC</b>") + k : ]
    contenuto = contenuto[0 : contenuto.find(stop)]
    return contenuto.strip()

def estraiFor(contenuto):
    if "Fortitude" not in contenuto:
        return "-"
    stop = ","
    k = len("Fortitude</b>")
    contenuto = contenuto[contenuto.find("Fortitude</b>") + k : ]
    contenuto = contenuto[0 : contenuto.find(stop)]
    return contenuto.strip()

def estraiRef(contenuto):
    if "Reflex" not in contenuto:
        return "-"
    stop = ","
    k = len("Reflex</b>")
    contenuto = contenuto[contenuto.find("Reflex</b>") + k : ]
    contenuto = contenuto[0 : contenuto.find(stop)]
    return contenuto.strip()

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
    mostro["Tipo"] = estraiTipo(contenuto)
    mostro["XP"] = estraiEXP(contenuto)
    mostro["Livello"] = estraiLivello(contenuto)
    mostro["Iniziativa"] = estraiIniziativa(contenuto)
    mostro["Sensi"] = estraiSensi(contenuto)
    mostro["HP"] = estraiHP(contenuto)
    mostro["AC"] = estraiAC(contenuto)
    mostro["Tempra"] = estraiFor(contenuto)
    mostro["Riflessi"] = estraiRef(contenuto)
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