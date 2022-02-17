import requests as req
from lxml import html
import json

urls = ["http://iws.mx/dnd/4e_database_files/monster/_listing.js"]

def decodeMostri(content):
    strMostri = content[len('od.reader.jsonp_data_listing(20130703, "monster", ["ID", "Name", "Level", "CombatRole", "GroupRole", "Size", "CreatureType", "SourceBook"], [') : -2]
    strMostri = strMostri.replace("],", "]|").split("|")
    
    mostri = []
    for mostro in strMostri:
        campiMostro = mostro.strip().split('"')[1::2]
        mostri.append({
            "ID":campiMostro[0],
            "Name":campiMostro[1],
            "Level":campiMostro[2],
            "CombatRole":campiMostro[3],
            "GroupRole":campiMostro[4],
            "Size":campiMostro[5],
            "CreatureType":campiMostro[6],
            "SourceBook":campiMostro[7]
        })

    tmp = []
    with open('jsonMostri.json', 'w+', encoding="utf-8") as f:
        json.dump(mostri, f)
    with open('jsonMostri.json', 'r', encoding='utf-8') as f:
        tmp = json.load(f)
    if mostri == tmp:
        print("Creazione del file dei mostri avvenuta con successo.")
    else:
        print("Errore nel salvataggio dei mostri nel file json.")

def getDati(url):
    response = req.get(url)
    if response.status_code == 200:
        risposta = response.content.decode('UTF-8')
        if 'monster' in risposta:
            decodeMostri(risposta)
    else:
        print("Errore chiamata")

def main():
    for url in urls:
        getDati(url)

main()
