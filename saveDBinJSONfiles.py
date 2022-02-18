import requests as req
from lxml import html
import json

#urls = ["http://iws.mx/dnd/4e_database_files/armor/_listing.js", "http://iws.mx/dnd/4e_database_files/monster/_listing.js"]
#urls = ["http://iws.mx/dnd/4e_database_files/armor/_listing.js"]
urls = ["http://iws.mx/dnd/4e_database_files/monster/_listing.js"]

def problema(riga):
    print("Riga con problema ", riga)

def decodeContent(content):
    inizioCampi = content.find("[")
    fineCampi = content.find("]")
    fineCampi += 1
    header = content[inizioCampi : fineCampi]
    header = header.strip().split('"')[1::2]
    print("Header ", header)
    strMostri = content[fineCampi+3 : -2].strip()
    strMostri = strMostri.replace("\"],\n", "\"]|\n").split("|")
    print("mostro ", strMostri[0].strip().split('"')[1::2])
    
    mostri = []
    for mostro in strMostri:
        campiMostro = mostro.strip().replace("\\\"", "").split('"')[1::2]
        if len(campiMostro) != len(header):
            problema(mostro)
            break
        tmp = {}
        for indice in range(len(header)):
            tmpHeader = header[indice]
            #print("tmp[", tmpHeader, "]=campiMostro[", indice, "]", ", campo prima ", campiMostro[indice-1])
            tmp[tmpHeader] = campiMostro[indice]
        mostri.append(tmp)
    nomeFile = mostri[0]["ID"] + ".json"
    tmp = []
    with open(nomeFile, 'w+', encoding="utf-8") as f:
        json.dump(mostri, f)
    with open(nomeFile, 'r', encoding='utf-8') as f:
        tmp = json.load(f)
    if mostri == tmp:
        print("Creazione del file avvenuta con successo.")
    else:
        print("Errore nel salvataggio nel file json.")

def getDati(url):
    response = req.get(url)
    if response.status_code == 200:
        risposta = response.content.decode('UTF-8')
        with open("risposta", 'w+', encoding="utf-8") as f:
            f.write(risposta)
        decodeContent(risposta)
    else:
        print("Errore chiamata dell'url ", url)

def main():
    for url in urls:
        getDati(url)

main()
