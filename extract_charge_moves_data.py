#!/usr/bin/python

import re
import sys
import urllib2

from bs4 import BeautifulSoup

url = "https://pokemongo.gamepress.gg/charge-moves"
headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
           'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
           'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
           'Accept-Encoding': 'none',
           'Accept-Language': 'en-US,en;q=0.8',
           'Connection': 'keep-alive'}
request = urllib2.Request(url, headers=headers)
intRegExp = re.compile(r"[^0-9]")
decRegExp = re.compile(r"[^0-9.]")
typeRegExp = re.compile(r"/([a-z]+)\.gif")
barRegExp = re.compile(r"/([1-3])-energy.png")


def parseInt(val):
    global intRegExp
    return intRegExp.sub("", val)

def parseDec(val):
    global decRegExp
    return decRegExp.sub("", val)

def innerHTML(ele):
    return ele.decode_contents(formatter=None)

def parseRow(row):
    nameTD = row.find("td", class_="views-field-field-energy-requirements-image")
    name = innerHTML(nameTD.find("a"))
    barImg = nameTD.find("img")
    bars = 1
    if barImg != None:
        bars = barRegExp.search(barImg["src"]).group(1)
    typeTD = row.find("td", class_="views-field-field-move-element")
    typeImgURL = typeTD.find("img")["src"]
    type_ = typeRegExp.search(typeImgURL).group(1)
    damageTD = row.find("td", class_="views-field-field-move-damage")
    damage = parseInt(innerHTML(damageTD))
    activeTD = row.find("td", class_="views-field-field-damage-window-start")
    active = parseDec(innerHTML(activeTD))
    cooldownTD = row.find("td", class_="views-field-field-move-cooldown")
    cooldown = parseDec(innerHTML(cooldownTD))
    return "{0},{1},{2},{3},{4},{5}\r\n".format(
        name,
        bars,
        type_,
        damage,
        cooldown,
        active
    )

def main(argv):
    global req
    with open("charge-moves.csv", "w") as file:
        file.write("{0},{1},{2},{3},{4},{5}\r\n".format(
            "Name",
            "Bars",
            "Type",
            "Damage",
            "Cooldown",
            "Activation"
        ))
        response = urllib2.urlopen(request)
        if response.getcode() == 200:
            html = response.read()
            soup = BeautifulSoup(html, "html.parser")
            table = soup.find("table", {"id":"sort-table"}).find("tbody")
            rows = table.find_all("tr")
            for row in rows:
                file.write(parseRow(row))
        else:
            print "Failed to get species-stats: {0}".format(response.getcode())
        response.close()

if __name__=='__main__':
    main(sys.argv[1:])
