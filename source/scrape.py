from typing import List, Dict
from collections import namedtuple
import requests
import re
import json
import math

class RouteEntry():
    def __init__(self,region:str,route:dict,index:int) -> None:
        # self.unlocked = route.get('unlocked') # unused
        self.region:str = region
        self.name:str = route.get('name','')
        self.uid:str = f"{region}{self.name.replace(' ','')}"
        self.pokes:List[str] = route.get('pokes',[])
        self.minLevel:int = route.get('minLevel',0)
        self.maxLevel:int = route.get('maxLevel',0)
        self.index:int = index

def scrapeRoutes(jsonPath = None) -> Dict[str, RouteEntry]:
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

def loadRoutes(routeJson: dict = None, path: str = None) -> Dict[str,RouteEntry]:
    '''
    take in the raw json of scrape, return object array of routes
    default input is json dict
    routePath kwarg treated as filePath
    '''
    if routeJson is not None:
        pass
    elif path is None:
        raise SyntaxError("invalid inputs")
    else:
        with open(path,'r') as fp:
            routeJson = json.load(fp)
    
    routeData = {}
    count = 0
    for region,v in routeJson.items():
        for route in v.values():
            entry = RouteEntry(region,route,count)
            routeData[entry.uid] = entry
            count += 1
    return routeData

class PokedexEntry():
    # stat calc in this obj
    # store lv100 on creation
    # create tupke types for pic
    ImageContainer = namedtuple('ImageContainer',['front','back'])
    PokeImageContainer = namedtuple('PokeImageContainer',['normal','shiny'])
    IndexContainer = namedtuple('IndexContiner',['index','evoIndex'])
    EvoContainer = namedtuple('EvoContainer',['level','to'])
    StatsContainer = namedtuple('StatsContainer',['hp', 'attack', 'defense', 'spAtk', 'spDef', 'speed', 'exp','avgAtk','avgDef'])
    
    def __init__(self,poke) -> None:
        self.name = poke['Pokemon'].replace(' ','-')
        self.displayName = poke['DisplayName']
        self.locations = []
        self.index = self.IndexContainer(poke['index'], poke['evoIndex'])
        if poke['evolution'] == {}:
            self.evolution = self.EvoContainer(0, '')
        else:
            self.evolution = self.EvoContainer(int(poke['evolution']['level']), poke['evolution']['to'].replace(" ","-"))
        self.prevolution = [i.replace(" ","-") for i in poke['prevolution']]
        self.image = self.PokeImageContainer(
            self.ImageContainer(poke['images']['normal']['front'], poke['images']['normal']['back']),
            self.ImageContainer(poke['images']['shiny']['front'], poke['images']['shiny']['back'])
        )
        self.types = poke['stats']['types']
        self.growthRate = poke['stats']['growth rate']
        self.catchRate = poke['stats']['catch rate']
        self.statsBase = self.StatsContainer( poke['stats']['hp'],
            poke['stats']['attack'], poke['stats']['defense'],
            poke['stats']['sp atk'], poke['stats']['sp def'],
            poke['stats']['speed'],  poke['stats']['base exp'],
            -1,-1
        )
        self.stats100 = self.StatsContainer( self.statHp(100),
            self.statValue(poke['stats']['attack'],100), self.statValue(poke['stats']['defense'],100),
            self.statValue(poke['stats']['sp atk'],100), self.statValue(poke['stats']['sp def'],100),
            self.statValue(poke['stats']['speed'],100), self.statValue(poke['stats']['base exp'],100),
            self.avgAtk(100), self.avgDef(100)
        )
        self.statsRank = self.StatsContainer(0,0,0,0,0,0,0,0,0)
        self.atkTime = max(0.3, math.floor(1000 / (500 + self.stats100.speed) * 800)/1000 )

    def statValue(self, raw, level):
        return math.floor((raw*100 + 50) * level / 150)

    def statHp (self, level):
        return math.floor(self.statsBase.hp * level * 3 / 40 )

    def avgDef(self,level):
        defense = self.statValue(self.statsBase.defense,level)
        spdef = self.statValue(self.statsBase.spDef,level)
        return (defense + spdef)/2

    def avgAtk(self, level):
        atk = self.statValue(self.statsBase.attack, level)
        spatk = self.statValue(self.statsBase.spAtk, level)
        return (atk+spatk)/2

    def expVal(self,level):
        return round(self.statsBase.exp / 16 + ( level * 3), 3)
    
    def expTeam(self,level):
        return round(self.statsBase.exp / 100 + level / 10 , 3)

    def setRank(self, data):
        pos = [arr.index(val) for arr,val in zip(data, self.stats100)]
        self.statsRank = self.StatsContainer(*pos)

def scrapePokedex(jsonPath = None) -> Dict[str,PokedexEntry]:
    '''
    create flat dict of pokedex
    include evolution data too
    '''
    db = requests.get("https://pokeidle.net/db.js").text
    db = "[" + db.split('[',1)[1]\
        .rsplit(",",1)[0] + "]"
    db = db.replace("\\'","'")
    # remove line comment
    p = re.compile('[^:]//.*', re.VERBOSE) 
    db = p.sub('',db)
    db = json.loads(db)


    evo = requests.get("https://pokeidle.net/evolutions.js").text
    evo = "{" + evo.split('{',1)[1] \
        .rsplit(",",1)[0] + "}"
    evo = evo.replace("\\'","'")
    evo = json.loads(evo)

    rEvo = {}
    for pre,post in evo.items():
        post = post['to']
        rEvo.setdefault(post,[])
        rEvo[post].append(pre)

    for pokeID,poke in enumerate(db):
        poke['stats'] = poke['stats'][0]
        poke['stats'].update(poke['exp'][0])
        del poke['exp']
        poke.update(poke['pokemon'][0])
        del poke['pokemon']

        poke["index"] = pokeID
        for k in ['catch rate','hp','attack', 'defense', 'sp atk', 'sp def', 'speed', 'base exp']:
            poke['stats'][k] = int(poke['stats'][k])
        poke["evolution"] = evo.get(poke["Pokemon"],{}) # empty dict if no evo
        poke['prevolution'] = rEvo.get(poke['Pokemon'],[])

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

    if jsonPath:
        with open(jsonPath,"w") as fp:
            json.dump(db,fp,indent="\t")
    return loadPokedex(db)

def loadPokedex(pokedex: list = None, path: str = None) -> Dict[str,PokedexEntry]:
    if pokedex is not None:
        pass
    elif path is None:
        raise SyntaxError("invalid inputs")
    else:
        with open(path,'r') as fp:
            pokedex = json.load(fp)
    pokedex = [PokedexEntry(i) for i in pokedex]

    statIndices = PokedexEntry.StatsContainer(
        sorted([poke.stats100.hp for poke in pokedex],reverse=True),
        sorted([poke.stats100.attack for poke in pokedex],reverse=True),
        sorted([poke.stats100.defense for poke in pokedex],reverse=True),
        sorted([poke.stats100.spAtk for poke in pokedex],reverse=True),
        sorted([poke.stats100.spDef for poke in pokedex],reverse=True),
        sorted([poke.stats100.speed for poke in pokedex],reverse=True),
        sorted([poke.stats100.exp for poke in pokedex],reverse=True),
        sorted([poke.stats100.avgAtk for poke in pokedex],reverse=True),
        sorted([poke.stats100.avgDef for poke in pokedex],reverse=True),
    )
    
    [poke.setRank(statIndices)for poke in pokedex]

    # array all the pokestats
    # index of to get the first so that ties get set correctly
    
    return {poke.name :poke for poke in pokedex}

def addLocToPokedex(routes:Dict[str, RouteEntry],pokedex:Dict[str,PokedexEntry]):
    pokeRoutes = {} # pokeName:[route.uid]
    for route in routes.values():
        for poke in route.pokes:
            pokeRoutes.setdefault(poke,[])
            pokeRoutes[poke].append(route.uid)

    for poke in pokedex.values():
        poke.locations = pokeRoutes.get(poke.name,[]) # empty list if not catchable
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



