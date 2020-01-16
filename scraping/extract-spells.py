#!/usr/bin/python3
# -*- coding: utf-8 -*-

import urllib.request
import yaml
import sys
import html
import re
from bs4 import BeautifulSoup
from lxml import html
import hashlib

from libhtml import jumpTo, html2text, html2simplehtml, getValidSource, mergeYAML, mergeNedb

## Configurations pour le lancement
MOCK_LIST = None
MOCK_SORT = None
#MOCK_LIST = "mocks/sortsListeA.html" # décommenter pour tester avec une liste pré-téléchargée
#MOCK_LIST = "mocks/sorts-chaman.html" # décommenter pour tester avec une liste pré-téléchargée
#MOCK_SORT = "mocks/sort1.html"       # décommenter pour tester avec un sort pré-téléchargé

URLs = [{'URL': "http://www.pathfinder-fr.org/Wiki/Pathfinder-RPG.Liste%20des%20sorts.ashx", 'list': False},
        {'URL': "http://www.pathfinder-fr.org/Wiki/Pathfinder-RPG.Liste%20des%20sorts%20(suite).ashx", 'list': False},
        {'URL': "http://www.pathfinder-fr.org/Wiki/Pathfinder-RPG.Liste%20des%20sorts%20(fin).ashx", 'list': False},
        {'URL': "http://www.pathfinder-fr.org/Wiki/Pathfinder-RPG.Liste%20des%20formules%20dalchimiste.ashx", 'list': True},
        {'URL': "http://www.pathfinder-fr.org/Wiki/Pathfinder-RPG.Liste%20des%20sorts%20dantipaladin.ashx", 'list': True},
        {'URL': "http://www.pathfinder-fr.org/Wiki/Pathfinder-RPG.Liste%20des%20sorts%20de%20bardes.ashx", 'list': True},
        {'URL': "http://www.pathfinder-fr.org/Wiki/Pathfinder-RPG.liste%20des%20sorts%20de%20chaman.ashx", 'list': True},
        {'URL': "http://www.pathfinder-fr.org/Wiki/Pathfinder-RPG.Liste%20des%20sorts%20de%20conjurateurs.ashx", 'list': True},
        {'URL': "http://www.pathfinder-fr.org/Wiki/Pathfinder-RPG.Liste%20des%20sorts%20de%20druides.ashx", 'list': True},
        {'URL': "http://www.pathfinder-fr.org/Wiki/Pathfinder-RPG.Liste%20des%20sorts%20densorceleursmagiciens.ashx", 'list': True},
        {'URL': "http://www.pathfinder-fr.org/Wiki/Pathfinder-RPG.liste%20des%20sorts%20dhypnotiseur.ashx", 'list': True},
        {'URL': "http://www.pathfinder-fr.org/Wiki/Pathfinder-RPG.Liste%20des%20sorts%20dinquisiteur.ashx", 'list': True},
        {'URL': "http://www.pathfinder-fr.org/Wiki/Pathfinder-RPG.Liste%20des%20sorts%20d%c3%a9l%c3%a9mentaliste.ashx", 'list': True},
        {'URL': "http://www.pathfinder-fr.org/Wiki/Pathfinder-RPG.Liste%20des%20sorts%20de%20magus.ashx", 'list': True},
        {'URL': "http://www.pathfinder-fr.org/Wiki/Pathfinder-RPG.Liste%20des%20sorts%20de%20m%c3%a9dium.ashx", 'list': True},
        {'URL': "http://www.pathfinder-fr.org/Wiki/Pathfinder-RPG.Sorts%20doccultiste.ashx", 'list': True},
        {'URL': "http://www.pathfinder-fr.org/Wiki/Pathfinder-RPG.Liste%20des%20sorts%20de%20paladins.ashx", 'list': True},
        {'URL': "http://www.pathfinder-fr.org/Wiki/Pathfinder-RPG.Liste%20des%20sorts%20de%20pr%c3%aatres.ashx", 'list': True},
        {'URL': "http://www.pathfinder-fr.org/Wiki/Pathfinder-RPG.Sorts%20de%20psychiste.ashx", 'list': True},
        {'URL': "http://www.pathfinder-fr.org/Wiki/Pathfinder-RPG.Liste%20des%20sorts%20de%20r%c3%b4deurs.ashx", 'list': True},
        {'URL': "http://www.pathfinder-fr.org/Wiki/Pathfinder-RPG.Liste%20des%20sorts%20de%20Sanguin.ashx", 'list': True},
        {'URL': "http://www.pathfinder-fr.org/Wiki/Pathfinder-RPG.Liste%20des%20sorts%20de%20sorci%c3%a8re.ashx", 'list': True},
        {'URL': "http://www.pathfinder-fr.org/Wiki/Pathfinder-RPG.Sorts%20de%20spirite.ashx", 'list': True},
        ]

FIELDS = ['Nom', 'École', 'Niveau', 'Portée', 'Cible ou zone d\'effet', 'Temps d\'incantation', 'Composantes', 'Durée', 'Jet de sauvegarde', 'Résistance à la magie', 'Description', 'DescriptionHTML', 'Source', 'Référence' ]
MATCH = ['Référence']
IGNORE = ['Source']

FIELDSNEDB = ['nom', 'ecole', 'niveau', 'portee', 'cible', 'tempsIncantation', 'composantes', 'duree', 'jds', 'rm', 'description', 'descriptionHTML', 'source', 'reference', '_id' ]
MATCHNEDB = ['reference']
IGNORENEDB = ['source', '_id']



liste = []
listeNedb = []

print("Extraction des sorts...")

listSorts = []    
for u in URLs:
    if MOCK_LIST:
        parsed_html = BeautifulSoup(open(MOCK_LIST),features="lxml").find(id='PageContentDiv')
    else:
        parsed_html = BeautifulSoup(urllib.request.urlopen(u['URL']).read(),features="lxml").find(id='PageContentDiv')
    
    if u['list']:
        for el in parsed_html.children:
            if el.name == "ul":
                listSorts += el.find_all('li')
    else:
        listSorts += parsed_html.find_all('li')

#
# cette fonction se charge d'extraire le texte de la partie HTML
# en explorant certaines balises. Malheureusement, le format des
# pages peut différer d'une fois à l'autre.
#
def extractText(list):
    text = ""
    html = ""
    for el in list:
        text += html2text(el)
        html += html2simplehtml(el)
    html = re.sub('(?:\n|\r|\t)', '', re.sub('(?:<p>\s*</p>)+', '', re.sub('<p>\s*<table>', '<table>', re.sub('</table>\s*</p>', '</table>', re.sub('(?:<p>\s*)+', '<p>', re.sub('(?:</p>\s*)+', '</p>', "<p>" + html + "</p>"))))))
    return [text, html]

def convert4nedb(sort):
    sortNedb = {}

    sortNedb[u'nom']=sort[u'Nom']
    sortNedb[u'reference']=sort[u'Référence']
    sortNedb[u'source']=sort[u'Source']
    sortNedb['description']=sort['Description']
    sortNedb['descriptionHTML']=sort['DescriptionHTML']

    try:
        sortNedb['cible']=sort["Cible ou zone d'effet"]
    except:
        pass

    try:
        sortNedb['composantes']=sort["Composantes"]
    except:
        pass

    try:
        sortNedb['duree']=sort["Durée"]
    except:
        pass

    try:
        sortNedb['jds']=sort["Jet de sauvegarde"]
    except:
        pass
    
    try:
        sortNedb['niveau']=sort["Niveau"]
    except:
        pass
    
    try:
        sortNedb['portee']=sort["Portée"]
    except:
        pass
    
    try:
        sortNedb['rm']=sort["Résistance à la magie"]
    except:
        pass
    
    try:
        sortNedb['tempsIncantation']=sort["Temps d'incantation"]
    except:
        pass
    
    try:
        sortNedb['ecole']=sort["École"]
    except:
        pass

    
    #sortNedb['_id'] = int(hashlib.md5(sortNedb['reference'].encode('utf-8')).hexdigest()[:8],16)
    return sortNedb

# itération sur chaque page
for l in listSorts:
    sort = {}
    
    element = l.find_next('a')
    title = element.get('title')
    link  = element.get('href')

    if "pagelink" not in element.attrs['class']:
        print("Skipping unkown link: %s" % link)
        continue
    
    linkText = element.text
    restText = l.text[len(linkText):]
    
    source = "MJ"
    source_search = re.search('\(([a-zA-Z-]+?)\)', restText, re.IGNORECASE)
    if source_search:
        source = getValidSource(source_search.group(1), False)
    
    print("Sort %s (%s)" % (title, source))
    pageURL = "http://www.pathfinder-fr.org/Wiki/" + link
    
    sort[u'Nom']=title
    sort[u'Référence']=pageURL.lower()
    sort[u'Source']=source
    
    if MOCK_SORT:
        content = BeautifulSoup(open(MOCK_SORT),features="lxml").body.find(id='PageContentDiv')
    else:
        content = BeautifulSoup(urllib.request.urlopen(pageURL).read(),features="lxml").body.find(id='PageContentDiv')
    
    # lire les attributs
    text = ""
    for attr in content.find_all('b'):
        key = attr.text.strip()
        
        for s in attr.next_siblings:
            #print "%s %s" % (key,s.name)
            if s.name == 'b' or  s.name == 'br':
                break
            elif s.string:
                text += s.string

        # convertir les propriétés qui sont similaires
        if "cible" in key.lower() or "effet" in key.lower() or "cible" in key.lower() or "zone" in key.lower():
            key = "Cible ou zone d'effet"
        key = key.replace("’","'")

        if key in FIELDS:
            sort[key]=re.sub(';\s*$', '', text).strip()
            descr = s.next_siblings
            text = ""
        else:
            print("- Skipping unknown property %s" % key)

    # lire la description
    text = extractText(descr)
    sort['Description']=text[0].strip()
    sort['DescriptionHTML']=text[1].strip()
    
    # ajouter sort
    liste.append(sort)

    # conversion du sort pour nedb
    listeNedb.append(convert4nedb(sort))

    #if MOCK_SORT:
    #    break

print("Fusion avec fichier YAML existant...")

HEADER = ""

mergeYAML("../data/spells.yml", MATCH, FIELDS, HEADER, liste, IGNORE)

print("Fusion avec fichier NdDB existant...")

mergeNedb("../data/sorts.db", MATCHNEDB, FIELDSNEDB, listeNedb, IGNORENEDB)
