import scrape
import math
from typing import List, Dict
from bs4 import BeautifulSoup as Soup

# pokedexLoc = scrape.addLocToPokedex(routes,pokedex)
# damageTakenMulti = scrape.scrapeDamageTaken()

def defaultSoup():
    soup = Soup("""<html>
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


    links = [
        "<a href=\"./pokedex.html\">pokedex</a>",
        "<a href=\"./pokedexEvo.html\">pokedex in Evolution order</a>",
        "<a href=\"./routes.html\">routes</a>",]
    links = [i+"<br>" for i in links]
    links = [Soup(i,features="html.parser") for i in links]
    for i in links:
        soup.body.contents.append(i)


    return soup

def makeRow(data:List[str]) -> Soup:
    '''
    make a bs4 tablerow object from a series of strings
    '''
    return Soup(f"<tr>{ ''.join(data) }</tr>",features="html.parser")

def makeRoutes(routes:Dict[str,scrape.RouteEntry],target:str):
    # consider adding pokestats onto routes also

    soup = defaultSoup()
    for route in sorted(routes.values(), key = lambda route : route.index):
        div = Soup(f"<div id={route.uid}><table></table><br/></div>",features="html.parser")

        keys = ["region","name","minLevel","maxLevel"]
        values = [route.region,route.name,route.minLevel,route.maxLevel]

        keyCells = [f"<th>{i}</th>" for i in keys]
        valCells = [f"<td>{i}</td>" for i in values]
        pokes = ["<th>Pokes : </th>"] + [f"<td><a href=\"./pokedex.html#{i}\">{i}</a></td>" for i in route.pokes]
        
        div.table.append(makeRow(keyCells))
        div.table.append(makeRow(valCells))
        div.table.append(makeRow(pokes))

        soup.body.contents.append(div)

    with open(target,"w") as fp:
        fp.write(soup.prettify())

def makePokedex(pokedex:Dict[str, scrape.PokedexEntry],routes:Dict[str, scrape.RouteEntry]):

    pokeTables = {} # (index,evoIndex) : div
    for poke in pokedex.values():
        # table for each should be same
        div = Soup(f"<div id={poke.name.replace(' ','')}><table></table></div>",features="html.parser")
        
        keys = ["DisplayName","type","evolution"]
        keys = [f"<th>{i}</th>" for i in keys]
        values = [f"<a href=\"#{poke.name}\">{poke.displayName}</a>",
            "-".join(poke.types), f"<a href=\"#{poke.evolution.to}\">{poke.evolution.to}</a>"]
        values = [f"<td>{i}</td>" for i in values]
        locationHead = ["<th>Routes</th>","<th>min level</th>","<th>max level</th>","<th>min exp</th>","<th>max exp</th>"]
        locations = [[f"<a href=\"./routes.html#{i}\">{i}</a>", 
            routes[i].minLevel, routes[i].maxLevel,
            poke.expVal(routes[i].minLevel), poke.expVal(routes[i].maxLevel)
            ] for i in poke.locations]
        locations = [[f"<td>{j}</td>" for j in i] for i in locations]
        statKeys = ['stat','hp','attack','defence','speed']
        statKeys = [f"<th>{i}</th>" for i in statKeys]
        stat100 = ['lv100',poke.stats100.hp, poke.stats100.avgAtk,poke.stats100.avgDef, poke.atkTime]
        stat100 = [f"<td>{i}</td>" for i in stat100]
        rank100 = ['rank',poke.statsRank.hp, poke.statsRank.avgAtk,poke.statsRank.avgDef, poke.statsRank.speed]
        rank100 = [f"<td>{i}</td>" for i in rank100]
        div.table.append(makeRow(keys))
        div.table.append(makeRow(values))
        div.table.append(makeRow(statKeys))
        div.table.append(makeRow(stat100))
        div.table.append(makeRow(rank100))

        # forms
        forms = [poke.name]
        checker = [poke.name]
        while len(checker) > 0:
            searchName = checker.pop(0)
            for nextName in pokedex[searchName].prevolution + [pokedex[searchName].evolution.to]:
                if nextName not in forms and nextName !='':
                    forms.append(nextName)
                    checker.append(nextName)
            
        # search for all pre/post evo then sort by evo order
        forms = [pokedex[poke] for poke in forms]
        forms = sorted(forms,key=lambda poke : poke.index.evoIndex)
        forms = [f"<td><a href=\"#{poke.name}\">{poke.displayName}</a></td>" for poke in forms]
        div.table.append(makeRow(["<th>Forms</th>"]))
        div.table.append(makeRow(forms))

        # locations
        div.table.append(makeRow(locationHead))
        for i in locations:
            div.table.append(makeRow(i))
        
        div.table.append(div.new_tag('br'))

        pokeTables[(poke.index.index,poke.index.evoIndex)] = div
    
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

routes = scrape.scrapeRoutes("./routes.json")
routes = scrape.loadRoutes(path = './routes.json')

pokedex = scrape.scrapePokedex("./pokedex.json")
pokedex = scrape.loadPokedex(path = "./pokedex.json")

pokedex = scrape.addLocToPokedex(routes,pokedex)

makeIndex()
makeRoutes(routes,"../docs/routes.html")
makePokedex(pokedex,routes)
