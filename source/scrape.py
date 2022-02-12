from typing import Union,List
import requests
import re
import json


def scrapeRoutes(jsonPath = None) -> list:
    '''
    get routes, 
    ''' 
    t2 = requests.get("https://pokeidle.net/routes.js").text
    t2 = "{" + t2.split("{",1)[1]

    # replace some strings that make json parsing difficult
    t2 = t2.replace("Let\\'s Go :","LETSGO") \
        .replace("\\'","_quote_") \
        .replace('Type: Null',"Type Null") \
        .replace("Legends : Origins","Legends  Origins")

    # insert "" around keys
    p = re.compile('([a-zA-Z0-9_ ]*):', re.VERBOSE)
    rep1 = lambda match : f'"{match.group()[:-1].strip()}":'
    t2 = p.sub(rep1,t2)

    # replace '' with "" around values
    p = re.compile("'([^']*)'", re.VERBOSE)
    rep2 = lambda match : f'"{match.group()[1:-1].strip()}"'
    t2 = p.sub(rep2,t2)

    # undo the changes to data
    t2 = t2.replace("LETSGO","Let's Go :") \
        .replace("_quote_","'") \
        .replace("Type Null",'Type: Null') \
        .replace("Legends  Origins","Legends : Origins")

    t2 = json.loads(t2)

    if jsonPath:
        with open(jsonPath,"w") as fp:
            json.dump(t2,fp,indent="\t")

    return loadRoutes(t2)

class RouteEntry():
    def __init__(self,region:str,route:dict) -> None:
        self.region:str = region
        self.name:str = route.get('name','')
        self.uid:str = f"{region}{self.name.replace(' ','')}"
        self.pokes:List[str] = route.get('pokes',[])
        self.minLevel:int = route.get('minLevel',0)
        self.maxLevel:int = route.get('maxLevel',0)
        # self.unlocked = route.get('unlocked') # unused
    
def loadRoutes(routeJson: dict = None, routePath: str = None) -> List[RouteEntry]:
    '''
    take in the raw json of scrape, return object array of routes
    default input is json dict
    routePath kwarg treated as filePath
    '''
    if routeJson is None:
        if routePath is None:
            raise SyntaxError("invalid inputs")
        with open(routePath,'r') as fp:
            routeJson = json.load(fp)
    
    routeData = []
    for region,v in routeJson.items():
        for route in v.values():
            routeData.append(RouteEntry(region,route))
    return routeData



def scrapePokedex(makeJson = True) -> dict:
    '''
    create flat dict of pokedex
    include evolution data too
    '''
    db = requests.get("https://pokeidle.net/db.js").text
    db = "[" + db.split('[',1)[1]\
        .rsplit(",",1)[0] + "]"
    db = db.replace("\\'","'")
    p = re.compile('[^:]//.*', re.VERBOSE) 
    db = p.sub('',db)
    db = json.loads(db)

    evo = requests.get("https://pokeidle.net/evolutions.js").text
    evo = "{" + evo.split('{',1)[1] \
        .rsplit(",",1)[0] + "}"
    evo = evo.replace("\\'","'")
    evo = json.loads(evo)

    for pokeID,poke in enumerate(db):
        poke.update(poke['exp'][0])
        poke.update(poke['pokemon'][0])
        poke.update(poke['stats'][0])
        del poke['images']
        del poke['exp']
        del poke['pokemon']
        del poke['stats']

        poke["index"] = pokeID
        for k in ['catch rate','hp','attack', 'defense', 'sp atk', 'sp def', 'speed']:
            poke[k] = int(poke[k])
        poke["evolution"] = evo.get(poke["Pokemon"],{}) # empty dict if no evo

    def Rinsert(arr:list,pdexName:dict,currName):
        if currName in arr:
            return
        evoName = pdexName.get(currName,{}).get("evolution",{}).get("to")
        if evoName is None:
            arr.append(currName)
            return
        if evoName in arr:
            # insert curr before its evolution
            arr.insert(arr.index(evoName),currName)
            return
        # else insert curr at end
        arr.append(currName)
        Rinsert(arr,pdexName,evoName)
        return

    pokeNameByEvo = []
    pdexName = {i["Pokemon"]:i for i in db}

    for poke in db:
        Rinsert(pokeNameByEvo,pdexName,poke["Pokemon"])

    for poke in db:
        poke['evoIndex'] = pokeNameByEvo.index(poke['Pokemon'])

    if makeJson:
        with open("./pokedex.json","w") as fp:
            json.dump(db,fp,indent="\t")
    return db

def addLocToPokedex(routes,pokedex,makeJson=True):
    pokeRoutes = {} #pokemon:[RegionRoute] 
    for region,v in routes.items():
        for route in v.values():
            for poke in route['pokes']:
                pokeRoutes.setdefault(poke,[])
                pokeRoutes[poke]+= [ f"{region}{route['name']}".replace(" ","")]
    for poke in pokedex:
        poke['locations'] = pokeRoutes.get(poke['Pokemon'],[]) # empty list if not catchable
    
    if makeJson:
        with open("./pokedexLoc.json","w") as fp:
            json.dump(pokedex,fp,indent="\t")
    
    return pokedex

def scrapeDamageTaken(makeJson=True):
    damT = requests.get("https://richardpaulastley.github.io/piddb/typeModifiersTaken.js").text
    damT = "{" + damT.split('{',1)[1]\
        .replace(";","")
    damT = json.loads(damT)

    for victimtype,v in damT.items():
        newVictims = {}
        for mult,atktypes in v.items():
            mult = float(mult.replace("x",""))
            for atktype in atktypes:
                newVictims[atktype] = mult
        damT[victimtype] = newVictims
    if makeJson:
        with open("./damageTakenMulti.json","w") as fp:
            json.dump(damT,fp,indent="\t")
    return damT



