#!/usr/bin/python3
# -*- coding: utf-8 -*-

import urllib.request
import yaml
import json
import sys
import html
import re
from bs4 import BeautifulSoup
from lxml import html

from libhtml import mergeNedb


URLs = [#{'URL': "http://www.pathfinder-fr.org/Wiki/Pathfinder-RPG.Liste%20des%20formules%20dalchimiste.ashx", 'classe': 'Alc'},
        #{'URL': "http://www.pathfinder-fr.org/Wiki/Pathfinder-RPG.Liste%20des%20sorts%20dantipaladin.ashx", 'classe': 'Ant'},
        #{'URL': "http://www.pathfinder-fr.org/Wiki/Pathfinder-RPG.Liste%20des%20sorts%20de%20bardes.ashx", 'classe': 'Bar'},
        #{'URL': "http://www.pathfinder-fr.org/Wiki/Pathfinder-RPG.liste%20des%20sorts%20de%20chaman.ashx", 'classe': 'Chm'},
        #{'URL': "http://www.pathfinder-fr.org/Wiki/Pathfinder-RPG.Liste%20des%20sorts%20de%20conjurateurs.ashx", 'classe': 'Con'},
        #{'URL': "http://www.pathfinder-fr.org/Wiki/Pathfinder-RPG.Liste%20des%20sorts%20de%20druides.ashx", 'classe': 'Dru'},
        {'URL': "http://www.pathfinder-fr.org/Wiki/Pathfinder-RPG.Liste%20des%20sorts%20densorceleursmagiciens.ashx", 'classe': 'Ens/Mag'},
        #{'URL': "http://www.pathfinder-fr.org/Wiki/Pathfinder-RPG.liste%20des%20sorts%20dhypnotiseur.ashx", 'classe': 'Hyp'},
        #{'URL': "http://www.pathfinder-fr.org/Wiki/Pathfinder-RPG.Liste%20des%20sorts%20dinquisiteur.ashx", 'classe': 'Inq'},
        ##{'URL': "http://www.pathfinder-fr.org/Wiki/Pathfinder-RPG.Liste%20des%20sorts%20d%c3%a9l%c3%a9mentaliste.ashx", 'classe': '},
        #{'URL': "http://www.pathfinder-fr.org/Wiki/Pathfinder-RPG.Liste%20des%20sorts%20de%20magus.ashx", 'classe': 'Mgs'},
        #{'URL': "http://www.pathfinder-fr.org/Wiki/Pathfinder-RPG.Liste%20des%20sorts%20de%20m%c3%a9dium.ashx", 'classe': 'Méd'},
        #{'URL': "http://www.pathfinder-fr.org/Wiki/Pathfinder-RPG.Sorts%20doccultiste.ashx", 'classe': 'Occ'},
        #{'URL': "http://www.pathfinder-fr.org/Wiki/Pathfinder-RPG.Liste%20des%20sorts%20de%20paladins.ashx", 'classe': 'Pal'},
        {'URL': "http://www.pathfinder-fr.org/Wiki/Pathfinder-RPG.Liste%20des%20sorts%20de%20pr%c3%aatres.ashx", 'classe': 'Prê'},
        #{'URL': "http://www.pathfinder-fr.org/Wiki/Pathfinder-RPG.Sorts%20de%20psychiste.ashx", 'classe': 'Psy'},
        #{'URL': "http://www.pathfinder-fr.org/Wiki/Pathfinder-RPG.Liste%20des%20sorts%20de%20r%c3%b4deurs.ashx", 'classe': 'Rôd'},
        #{'URL': "http://www.pathfinder-fr.org/Wiki/Pathfinder-RPG.Liste%20des%20sorts%20de%20Sanguin.ashx", 'classe': 'San'},
        #{'URL': "http://www.pathfinder-fr.org/Wiki/Pathfinder-RPG.Liste%20des%20sorts%20de%20sorci%c3%a8re.ashx", 'classe': 'Sor'},
        #{'URL': "http://www.pathfinder-fr.org/Wiki/Pathfinder-RPG.Sorts%20de%20spirite.ashx", 'classe': 'Spi'},
        ]

FIELDS = ['nom', 'ecole', 'niveau', 'portee', 'cible', 'tempsIncantation', 'composantes', 'duree', 'jds', 'rm', 'description', 'descriptionHTML', 'source', 'reference', '_id' ]
MATCH = ['_id']

## Configurations pour le lancement
MOCK_SL = None
#MOCK_SL = "mocks/sorts-chaman.html"       # décommenter pour tester avec les sorts pré-téléchargées

print("Importation des sorts...")

sorts = []
db = '../data/sorts.db'
try:
    nedbFile = open(db, 'r', encoding='utf8')
except IOError:
    nedbFile = open(db, 'w', encoding='utf8')
    nedbFile = open(db, 'r', encoding='utf8')

with nedbFile as stream:
    for line in stream:
        if line.strip():
            sorts.append(json.loads(line))

##
## Recherche un sort basé sur l'adresse spécifiée
##
def findSpell(url):
    url = url.lower()
    for s in sorts:
        if url in s['reference'].lower():
            return s
    print("Not found: " + url)
    ## Ne pas quitter : permet de continuer tout en affichant les sorts en erreur pour traiter au moins ceux qui ont été trouvés

##
## Ajoute une classe au sort (niveau)
##
def addSpellLevel(classe, level, spell):
    try:
        for el in spell['niveau']:
            # check if spell already listed for given class
            if el['Class'] == classe:
                if el['Level'] != level:
                    print("Something wrong with spell %s" % spell['nom'])
                    ## Ne pas quitter : permet de continuer tout en affichant les sorts en erreur pour traiter au moins ceux qui ont été trouvés
                    
                return
        spell['niveau'].append({'Class': classe, 'Level': level})
    except:
        pass
        ## Ne pas quitter : permet de continuer tout en affichant les sorts en erreur pour traiter au moins ceux qui ont été trouvés


##
## Transforme la liste en string (format final pour l'import)
##
def levelToString(liste):
    text = ""
    for el in liste:
        text += el['Class'] + " " + str(el['Level']) + ", "
    if len(text) > 0:
        text = text[:-2]
    return text

# réinitialiser les niveaux
for s in sorts:
    s['niveau'] = []

# itération sur chaque page
for data in URLs:
    cl = {}
    
    link = data['URL']
    
    print("Traitement %s" % link)
    pageURL = link
    
    if MOCK_SL:
        content = BeautifulSoup(open(MOCK_SL),features="lxml").body
    else:
        content = BeautifulSoup(urllib.request.urlopen(pageURL).read(),features="lxml").body

    levels = []
    for s in content.find_all('h2', {'class':'separator'}):
        m = re.search(' de niveau (\d+)', s.text)
        if not m:
            continue
        
        lvl = int(m.group(1))
        levels.append(lvl)
        
        for s in s.next_siblings:
            if s.name == "h1" or s.name == "h2":
                break
            elif s.name == "ul":
                for li in s.find_all("li"):
                    ref = li.find("a")['href']
                    
                    if "pagelink" not in li.find("a").attrs['class']:
                        print("Skipping unkown link: %s" % li.find("a").text)
                        continue
                    
                    spell = findSpell(ref)
                    addSpellLevel(data['classe'], lvl, spell)
                    
    print("Niveaux traités: %s" % levels)

    if MOCK_SL:
        break

# Hot fixes for special cases
spell = findSpell("http://www.pathfinder-fr.org/Wiki/Pathfinder-RPG.Forme%20de%20vase%20I.ashx")
addSpellLevel("Ens/Mag", 5, spell)
spell = findSpell("http://www.pathfinder-fr.org/Wiki/Pathfinder-RPG.Forme%20de%20vase%20II.ashx")
addSpellLevel("Ens/Mag", 6, spell)
spell = findSpell("http://www.pathfinder-fr.org/Wiki/Pathfinder-RPG.Forme%20de%20vase%20III.ashx")
addSpellLevel("Ens/Mag", 7, spell)

# initialiser les niveaux
for s in sorts:
    s['niveau'] = levelToString(s['niveau'])
    
mergeNedb(db, MATCH, FIELDS, sorts)
