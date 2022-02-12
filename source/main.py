import scrape
import json
from typing import List
from bs4 import BeautifulSoup as Soup


# pokedex = scrape.scrapePokedex()
# pokedexLoc = scrape.addLocToPokedex(routes,pokedex)
# damageTakenMulti = scrape.scrapeDamageTaken()

def defaultSoup():

    return Soup("""<html>
    <head>
    <style>
    table {
    font-family: arial, sans-serif;
    border-collapse: collapse;
    }
    td, th {
    border: 1px solid #dddddd;
    text-align: left;
    padding: 8px;
    }
    tr:nth-child(even) {
    background-color: #dddddd;
    }
    </style>
    <title></title>
    </head>
    <body></body>
    </html>""",features="html.parser")

def makeRow(data:List[str]) -> Soup:
    '''
    make a bs4 tablerow object from a series of strings
    '''
    return Soup(f"{ ''.join(data) }</tr>",features="html.parser")

def makeRoutes(routes:List[scrape.RouteEntry],target:str):
    # consider adding pokestats onto routes also

    soup = defaultSoup()
    for route in routes:
        div = Soup(f"<div id={route.uid}><table></table><br/></div>",features="html.parser")

        keys = ["region","name","minLevel","maxLevel"]
        values = [route.region,route.name,route.minLevel,route.maxLevel]

        keyCells = [f"<th>{i}</th>" for i in keys]
        valCells = [f"<td>{i}</td>" for i in values]
        pokes = ["<tr><th>Pokes : </th>"] + [f"<td><a href=\"./pokedex.html#{i}\">{i}</a></td>" for i in route.pokes]
        
        div.table.append(makeRow(keyCells))
        div.table.append(makeRow(valCells))
        div.table.append(makeRow(pokes))

        soup.body.contents.append(div)

    with open(target,"w") as fp:
        fp.write(soup.prettify())

def makePokedex():

    pokeTables = {} # (index,evoIndex) : div
    for poke in pokedexLoc:
        # table for each should be same
        table = Soup(f"<div id={poke['Pokemon'].replace(' ','')}><table></table></div>",features="html.parser")
        
        keys = ["DisplayName","Pokemon","types","evolution"]
        values = [poke["DisplayName"], poke["Pokemon"], "-".join(poke["types"]), poke["evolution"].get("to","")]

        keyCells = [f"<th>{i}</th>" for i in keys]
        keyRow = Soup(f"<tr>{''.join(keyCells)}</tr>",features="html.parser")
        valCells = [f"<td>{i}</td>" for i in values]
        valRow = Soup(f"<tr>{''.join(valCells)}</tr>",features="html.parser")
        locs = ["<tr><th>Routes : </th>"] + [f"<td><a href=\"./routes.html#{i}\">{i}<a></td>" for i in poke["locations"]]

        table.table.append(keyRow)
        table.table.append(valRow)
        table.table.append(Soup(f"{ ''.join(locs) }</tr><br/>",features="html.parser"))

        pokeTables[(poke['index'],poke['evoIndex'])] = table
    
    soup = defaultSoup()
    for key,value in sorted(pokeTables.items(),key=lambda x : x[0][0]):
        soup.body.contents.append(value)
    with open("../docs/pokedex.html","w") as fp:
        fp.write(soup.prettify())

    soup = defaultSoup()
    for key,value in sorted(pokeTables.items(),key=lambda x : x[0][1]):
        soup.body.contents.append(value)
    with open("../docs/pokedexEvo.html","w") as fp:
        fp.write(soup.prettify())

def makeIndex():
    with open("../docs/index.html","w") as fp:
        fp.write(defaultSoup().prettify())

# routes = scrape.scrapeRoutes("./routes.json")
routes = scrape.loadRoutes(routePath = './routes.json')
makeRoutes(routes,"../docs/routes.html")

pokedex = scrape.scrapePokedex()
pokedex = scrape.loadPokedex()
# makePokedex()
# makeIndex()