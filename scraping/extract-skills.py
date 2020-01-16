#!/usr/bin/python3
# -*- coding: utf-8 -*-

import urllib.request
import yaml
import sys
import html
from bs4 import BeautifulSoup
from lxml import html

from libhtml import html2text, html2simplehtml, mergeYAML, mergeNedb, extractText

## Configurations pour le lancement
MOCK_LIST = None
MOCK_COMP = None
#MOCK_LIST = "mocks/compsListe.html" # décommenter pour tester avec une liste pré-téléchargée
#MOCK_COMP = "mocks/comp2.html"       # décommenter pour tester avec un sort pré-téléchargé

URL = "http://www.pathfinder-fr.org/Wiki/Pathfinder-RPG.Tableau%20r%c3%a9capitulatif%20des%20comp%c3%a9tences.ashx"

PROPERTIES = [ "Caractéristique associée", "caractéristique associée", "Formation nécessaire", "Formation nécesssaire", "Malus d’armure"]

FIELDS = ['Nom', 'Caractéristique associée', 'Malus d’armure', 'Formation nécessaire', 'Description', 'DescriptionHTML', 'Référence' ]
MATCH = ['Nom']

FIELDSNEDB = ['nom', 'attribut', 'malusArmure', 'formation', 'description', 'descriptionHTML', 'reference', '_id' ]
MATCHNEDB = ['nom']
IGNORENEDB = ['_id']


liste = []
listeNedb = []

print("Extraction des compétences...")

list = []
if MOCK_LIST:
    parsed_html = BeautifulSoup(open(MOCK_LIST),features="lxml")
    list = parsed_html.body.find(id='PageContentDiv').find_next('table',class_="tablo").find_all('tr')
else:
    parsed_html = BeautifulSoup(urllib.request.urlopen(URL).read(),features="lxml")
    list += parsed_html.body.find(id='PageContentDiv').find_next('table',class_="tablo").find_all('tr')

def convert4nedb(sort):
    sortNedb = {}

    sortNedb[u'nom']=sort[u'Nom']
    sortNedb[u'reference']=sort[u'Référence']
    sortNedb['description']=sort['Description']
    sortNedb['descriptionHTML']=sort['DescriptionHTML']

    try:
        sortNedb['attribut']=sort["Caractéristique associée"]
    except:
        pass

    try:
        sortNedb['malusArmure']=sort["Malus d’armure"]
    except:
        pass

    try:
        sortNedb['formation']=sort["Formation nécessaire"]
    except:
        pass

    return sortNedb

# itération sur chaque page
for l in list:
    sort = {}
        
    element = l.find_next('a')
    title = element.text
    link  = element.get('href')
    
    if element.next_sibling != None:
        title += element.next_sibling
    
    # ugly fix to ignore "headers"
    if title == "Barb":
        continue

    
    print("Processing %s" % title)
    pageURL = "http://www.pathfinder-fr.org/Wiki/" + link
    '''pageURL = "https://www.pathfinder-fr.org/Wiki/Pathfinder-RPG.Art%20de%20la%20magie.ashx"
    print(pageURL)
'''
    sort['Nom']=title
    sort['Référence']=pageURL
    
    if MOCK_COMP:
        content = BeautifulSoup(open(MOCK_COMP),features="lxml").body.find(id='PageContentDiv')
    else:
        content = BeautifulSoup(urllib.request.urlopen(pageURL).read(),features="lxml").body.find(id='PageContentDiv')
    
    # lire les attributs
    text = ""
    descr = ""
    for attr in content.find_all('b'):
        key = attr.text.strip()
        
        for s in attr.next_siblings:
            #print("%s %s" % (key,s.name))
            if s.name == 'b' or  s.name == 'br':
                break
            elif s.string:
                text += s.string

        # clean text
        text = text.strip()
        if text.startswith(": "):
            text = text[2:]

        if key in PROPERTIES:
            # merge properties with almost the same name
            if key == "Formation nécesssaire":
                key = "Formation nécessaire"
            elif key == "caractéristique associée":
                key = "Caractéristique associée"
            
            sort[key]=text
            descr = s.next_siblings
            text = ""
        #else:
        #    print("- Skipping unknown property %s" % key)

    # lire la description
    text = extractText(descr)
    
    sort['Description']=text[0].strip()
    sort['DescriptionHTML']=text[1].strip()
    
    # ajouter sort
    liste.append(sort)

    # conversion du sort pour nedb
    listeNedb.append(convert4nedb(sort))
    
    if MOCK_COMP:
        break

HEADER = ""

mergeYAML("../data/competences.yml", MATCH, FIELDS, HEADER, liste)

mergeNedb("../data/competences.db", MATCHNEDB, FIELDSNEDB, listeNedb, IGNORENEDB)