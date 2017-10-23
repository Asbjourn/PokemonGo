#!/usr/bin/python

import re
import sys
import urllib2

from bs4 import BeautifulSoup

url = "https://thesilphroad.com/species-stats"
regExp = re.compile(r"[^0-9]")

def filterInt(val):
    global regExp
    return regExp.sub("", val)

def innerHTML(ele):
    return ele.decode_contents(formatter=None)

def parseTypes(div):
    typeDivs = div.find_all("div")
    types = "["
    for typeDiv in typeDivs:
        types += (innerHTML(typeDiv) + ",")
    return types[0:-1] + "]"

def parseDiv(div):
    name = innerHTML(div.find("h1"))
    number = filterInt(innerHTML(div.find("div", class_="monPhotoWrap").find("p")))
    table = div.find("table")
    tds = table.find_all("td")
    height = filterInt(innerHTML(tds[1]))
    weight = filterInt(innerHTML(tds[3]))
    rowFluids = div.find_all("div", class_="row-fluid")
    typesFluid = rowFluids[1]
    types = parseTypes(typesFluid)
    maxCPFluid = rowFluids[3]
    maxCP = innerHTML(maxCPFluid.find_all("span", class_="progressBarLabel")[1])
    maxCP = filterInt(maxCP)
    attackFluid = rowFluids[4]
    attack = innerHTML(attackFluid.find("span", class_="progressBarLabel"))
    attack = filterInt(attack)
    defenseFluid = rowFluids[5]
    defense = innerHTML(defenseFluid.find("span", class_="progressBarLabel"))
    defense = filterInt(defense)
    staminaFluid = rowFluids[6]
    stamina = innerHTML(staminaFluid.find("span", class_="progressBarLabel"))
    stamina = filterInt(stamina)
    return "{0},{1},{2},{3},{4},{5},{6},{7},{8}\r\n".format(
        name,
        number,
        height,
        weight,
        types,
        maxCP,
        attack,
        defense,
        stamina
    )

def main(argv):
    with open("pokemon.csv", "w") as file:
        file.write("{0},{1},{2},{3},{4},{5},{6},{7},{8}\r\n".format(
            "Name",
            "Number",
            "Height(m)",
            "Weight(kg)",
            "Types",
            "Max CP",
            "Attack",
            "Defense",
            "Stamina"
        ))
        response = urllib2.urlopen(url)
        if response.getcode() == 200:
            html = response.read()
            soup = BeautifulSoup(html, "html.parser")
            divs = soup.find_all("div", class_="speciesWrap")
            for div in divs:
                file.write(parseDiv(div))
        else:
            print "Failed to get species-stats: {0}".format(response.getcode())
        response.close()

if __name__=='__main__':
    main(sys.argv[1:])
