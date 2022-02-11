import scrape
import json
from bs4 import BeautifulSoup as Soup
routes = scrape.scrapeRoutes()
pokedex = scrape.scrapePokedex()
pokedexLoc = scrape.addLocToPokedex(routes,pokedex)
damageTakenMulti = scrape.scrapeDamageTaken()

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

def makeRoutes():
    # consider adding pokestats onto routes also

    soup = defaultSoup()
    for region,v in routes.items():
        for route in v.values():
            table = Soup(f"<div id={region}{route['name'].replace(' ','')}><table></table></div>",features="html.parser")

            keys = ["region","name","minLevel","maxLevel"]
            values = [region,route["name"],route["minLevel"],route["maxLevel"]]

            keyCells = [f"<th>{i}</th>" for i in keys]
            keyRow = Soup(f"<tr>{''.join(keyCells)}</tr>",features="html.parser")
            valCells = [f"<td>{i}</td>" for i in values]
            valRow = Soup(f"<tr>{''.join(valCells)}</tr>",features="html.parser")
            pokes = ["<tr><th>Pokes : </th>"] + [f"<td><a href=\"./pokedex.html#{i}\">{i}</a></td>" for i in route["pokes"]]
            
            table.table.append(keyRow)
            table.table.append(valRow)
            
            table.table.append(Soup(f"{ ''.join(pokes) }</tr><br/>",features="html.parser"))
            soup.body.contents.append(table)

    with open("../docs/routes.html","w") as fp:
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

makeRoutes()
makePokedex()
makeIndex()