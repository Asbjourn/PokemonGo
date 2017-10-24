#!/usr/bin/python

import csv
import json
import math
import random
import re
import sys
import urllib2
from sets import Set

pokemon = {}
quickMoves = {}
chargeMoves = {}
aTE = {}

notAlphaNumeric = re.compile(r"[^a-zA-Z0-9]")

attributeMap = {
    "Height(m)" : "height",
    "Weight(kg)" : "weight",
    "Max CP" : "maxcp"
}

effectivenessMap = {
    -2 : 0.51,
    -1 : 0.714,
    0 : 1,
    1 : 1.4
}

attributeNum = Set([
    "height",
    "weight",
    "number",
    "maxcp",
    "attack",
    "defense",
    "stamina",
    "damage",
    "energy",
    "energy gain",
    "dps",
    "eps",
    "cooldown",
    "activation",
    "bars"
])




def parsePokemon(attributes, poke):
    global pokemon
    current = {}
    delta = 0
    for i in range(0, len(attributes)):
        attr = attributes[i]
        if attributeMap.has_key(attr):
            attr = attributeMap[attr]
        attr = attr.lower()
        value = poke[i + delta]
        if value[0] == "[":
            value = []
            flag = True
            while flag:
                test = poke[i + delta]
                if test[len(test)-1] == "]":
                    flag = False
                else:
                    delta += 1
                test = notAlphaNumeric.sub("", test)
                value.append(test)
            current[attr] = value
        elif attr in attributeNum:
            current[attr] = float(value)
        else:
            current[attr] = value
    pokemon[current["name"]] = current

def parseQuickMoves(attributes, move):
    global quickMoves
    current = {}
    for i in range(0, len(attributes)):
        attr = attributes[i]
        if attributeMap.has_key(attr):
            attr = attributeMap[attr]
        attr = attr.lower()
        value = move[i]
        if attr in attributeNum:
            current[attr] = float(value)
        else:
            current[attr] = value
    quickMoves[current["name"]] = current

def parseChargeMoves(attributes, move):
    global chargeMoves
    current = {}
    for i in range(0, len(attributes)):
        attr = attributes[i]
        if attributeMap.has_key(attr):
            attr = attributeMap[attr]
        attr = attr.lower()
        value = move[i]
        if attr in attributeNum:
            current[attr] = float(value)
        else:
            current[attr] = value
    chargeMoves[current["name"]] = current


def importPokemon():
    with open("pokemon.csv", "rb") as csvFile:
        reader = csv.reader(csvFile, delimiter=",")
        attributes = None
        for row in reader:
            if attributes == None:
                attributes = row
            else:
                parsePokemon(attributes, row)

def importQuickMoves():
    with open("quick-moves.csv", "rb") as csvFile:
        reader = csv.reader(csvFile, delimiter=",")
        attributes = None
        for row in reader:
            if attributes == None:
                attributes = row
            else:
                parseQuickMoves(attributes, row)
                
def importChargeMoves():
    with open("charge-moves.csv", "rb") as csvFile:
        reader = csv.reader(csvFile, delimiter=",")
        attributes = None
        for row in reader:
            if attributes == None:
                attributes = row
            else:
                parseChargeMoves(attributes, row)

def ascii_encode_dict(data):
    ret = {}
    for key, value in data.iteritems():
        if isinstance(key, unicode):
            key = key.encode('utf-8')
        if isinstance(value, unicode):
            value = value.encode('utf-8')
        elif isinstance(value, dict):
            value = ascii_encode_dict(value)
        ret[key] = value
    return ret

def importAttackTypeEffectiveness():
    global aTE
    with open("attack_type_effectiveness.json", "r") as jsonFile:
        json_data = jsonFile.read()
        aTE = json.loads(json_data, object_hook=ascii_encode_dict)

def damage(move,
           attack_pokemon, attack_ivs, attack_cpm,
           defense_pokemon, defense_ivs, defense_cpm):
    global aTE
    global effectivenessMap
    global pokemon
    
    power = move["damage"]
    aPokemon = pokemon[attack_pokemon]
    attack = (aPokemon["attack"] + attack_ivs["attack"]) * attack_cpm
    dPokemon = pokemon[defense_pokemon]
    defense = (dPokemon["defense"] + defense_ivs["defense"]) * defense_cpm
    stab = 1.0
    if move["type"] in aPokemon["types"]:
        stab = 1.2
    effective = 1.0
    for dType in dPokemon["types"]:
        effective *= effectivenessMap[aTE[move["type"]][dType]]
    return math.floor(0.5 * power * attack / defense * stab * effective) + 1
        
def simulateGymAttack():
    global attack_pokemon
    global attack_ivs
    global attack_cpm
    global attack_quick
    global attack_charge
    global defense_pokemon
    global defense_ivs
    global defense_cpm
    global defense_quick
    global defense_charge
    global time
    global delta

    # Attack Pokemon
    aPokemon = pokemon[attack_pokemon]
    aQuick = quickMoves[attack_quick]
    aCharge = chargeMoves[attack_charge]
    aDamageCounter = 0.0
    aEnergy = 0.0
    aCooldown = 0.0

    # Defend Pokemon
    dPokemon = pokemon[defense_pokemon]
    dQuick = quickMoves[defense_quick]
    dCharge = chargeMoves[defense_charge]
    dDamageCounter = 0.0
    dEnergy = 0.0
    dCooldown = 0.0
    dStamina = 2 * math.floor((dPokemon["stamina"] + defense_ivs["stamina"]) * defense_cpm)
    # Constants
    elapsed = 0.0
    snapshots = []

    while elapsed <= time and dDamageCounter < aPokemon["stamina"] and aDamageCounter < dStamina:
        aAttack = None
        aDamage = 0.0
        aStab = 1.0
        aEffectiveness = 1.0
        dAttack = None
        dDamage = 0.0
        dStab = 1.0
        dEffectiveness = 1.0
        
        # Attack Pokemon
        aCooldown -= delta
        if aCooldown > 0.001:
            # Do nothing
            aAttack = None
            aDamage = 0
        elif aEnergy > 100 / aCharge["bars"]:
            aDamage = damage(aCharge,
                             attack_pokemon, attack_ivs, attack_cpm,
                             defense_pokemon, defense_ivs, defense_cpm)
            aDamageCounter += aDamage
            aEnergy -= 100 / aCharge["bars"]
            aCooldown = aCharge["cooldown"]
            aAttack = aCharge
            if aAttack["type"] in aPokemon["types"]:
                aStab = 1.2
            for dType in dPokemon["types"]:
                aEffectiveness *= effectivenessMap[aTE[aAttack["type"]][dType]]
        else:
            aDamage = damage(aQuick,
                             attack_pokemon, attack_ivs, attack_cpm,
                             defense_pokemon, defense_ivs, defense_cpm)
            aDamageCounter += aDamage
            aEnergy += aQuick["energy gain"]
            aCooldown = aQuick["cooldown"]
            aAttack = aQuick
            if aAttack["type"] in aPokemon["types"]:
                aStab = 1.2
            for dType in dPokemon["types"]:
                aEffectiveness *= effectivenessMap[aTE[aAttack["type"]][dType]]

        # Defense Pokemon
        dCooldown -= delta
        if dCooldown > 0.001:
            dAttack = None
            dDamage = 0
        elif elapsed == 1.0:
            dDamage = damage(dQuick,
                             defense_pokemon, defense_ivs, defense_cpm,
                             attack_pokemon, attack_ivs, attack_cpm)
            dDamageCounter += dDamage
            dEnergy += dQuick["energy gain"]
            dAttack = dQuick
            if dAttack["type"] in dPokemon["types"]:
                dStab = 1.2
            for aType in aPokemon["types"]:
                dEffectiveness *= effectivenessMap[aTE[dAttack["type"]][aType]]
        elif dEnergy > 100 / dCharge["bars"]:
            if random.uniform(0.0, 1.0) > 0.5:
                dDamage = damage(dCharge,
                                 defense_pokemon, defense_ivs, defense_cpm,
                                 attack_pokemon, attack_ivs, attack_cpm)
                dDamageCounter += dDamage
                dEnergy -= 100 / dCharge["bars"]
                dCooldown = dCharge["cooldown"] + random.uniform(1.5, 2.5)
                dAttack = dCharge
                if dAttack["type"] in dPokemon["types"]:
                    dStab = 1.2
                for aType in aPokemon["types"]:
                    dEffectiveness *= effectivenessMap[aTE[dAttack["type"]][aType]]
            else:
                dDamage = damage(dQuick,
                                 defense_pokemon, defense_ivs, defense_cpm,
                                 attack_pokemon, attack_ivs, attack_cpm)
                dDamageCounter += dDamage
                dEnergy += dQuick["energy gain"]
                dCooldown = dQuick["cooldown"] + random.uniform(1.5, 2.5)
                dAttack = dQuick
                if dAttack["type"] in dPokemon["types"]:
                    dStab = 1.2
                for aType in aPokemon["types"]:
                    dEffectiveness *= effectivenessMap[aTE[dAttack["type"]][aType]]
        else:
            dDamage = damage(dQuick,
                             defense_pokemon, defense_ivs, defense_cpm,
                             attack_pokemon, attack_ivs, attack_cpm)
            dDamageCounter += dDamage
            dEnergy += dQuick["energy gain"]
            dCooldown = dQuick["cooldown"] + random.uniform(1.5, 2.5)
            dAttack = dQuick
            if dAttack["type"] in dPokemon["types"]:
                dStab = 1.2
            for aType in aPokemon["types"]:
                dEffectiveness *= effectivenessMap[aTE[dAttack["type"]][aType]]

        
        aEnergy += math.ceil(dDamage / 2)
        aEnergy = 100 if aEnergy > 100 else aEnergy
        dEnergy += math.ceil(aDamage / 2)
        dEnergy = 100 if dEnergy > 100 else dEnergy

        snapshot = {
            "attacker" : {
                "name" : aPokemon["name"],
                "hp" : aPokemon["stamina"] - dDamageCounter,
                "energy" : aEnergy,
                "cd" : aCooldown,
                "damage_dealt" : aDamageCounter,
                "attack" : None if aAttack == None else aAttack["name"]
            },
            "defender" : {
                "name" : dPokemon["name"],
                "hp" : dStamina - aDamageCounter,
                "energy" : dEnergy,
                "cd" : dCooldown,
                "damage_dealt" : dDamageCounter,
                "attack" : None if dAttack == None else dAttack["name"]
            },
        }

        snapshots.append(snapshot)

        if print_:
            if (print_Only_Attacks and (aAttack != None or dAttack != None)) or not print_Only_Attacks:
                aStrLength = 48
                aPokemonStr = "Attacking Pokemon:  %s" % (snapshot["attacker"]["name"], )
                aHPStr = "HP:                 %03d" % (snapshot["attacker"]["hp"], )
                aEnergyStr = "Energy:             %03d" % (aEnergy, )
                aCDStr = "Cooldown:           %1.2f" % (aCooldown, )
                aDamageStr = "Total damage dealt: %03d" % (aDamageCounter)
                aAttackStr = "Attack:             %s x%1.2f x%1.2f" % (aAttack["name"], aStab, aEffectiveness) if aAttack != None else ""
                
                aPokemonTail = " " * (aStrLength - len(aPokemonStr))
                aHPTail = " " * (aStrLength - len(aHPStr))
                aEnergyTail = " " * (aStrLength - len(aEnergyStr))
                aCDTail = " " * (aStrLength - len(aCDStr))
                aDamageTail = " " * (aStrLength - len(aDamageStr))
                aAttackTail = " " * (aStrLength - len(aAttackStr))
            
                dPokemonStr = "Defending Pokemon:  %s" % (snapshot["defender"]["name"], )
                dHPStr = "HP:                 %03d" % (snapshot["defender"]["hp"], )
                dEnergyStr = "Energy:             %03d" % (dEnergy, )
                dCDStr = "Cooldown:           %1.2f" % (dCooldown, )
                dDamageStr = "Total damage dealt: %03d" % (dDamageCounter)
                dAttackStr = "Attack:             %s x%1.2f x%1.2f" % (dAttack["name"], dStab, dEffectiveness) if dAttack != None else ""
                
                print "-" * (2 * aStrLength)
                print "Time Elapsed: {0}".format(elapsed)
                print "-" * (2 * aStrLength)
                print "%s%s%s" % (aPokemonStr, aPokemonTail, dPokemonStr)
                print "-" * (2 * aStrLength)
                print "%s%s%s" % (aHPStr, aHPTail, dHPStr)
                print "%s%s%s" % (aEnergyStr, aEnergyTail, dEnergyStr)
                print "%s%s%s" % (aCDStr, aCDTail, dCDStr)
                print "%s%s%s" % (aDamageStr, aDamageTail, dDamageStr)
                print "%s%s%s" % (aAttackStr, aAttackTail, dAttackStr)
                print ""

        elapsed += delta

    # Attacker [Win, Loss, Draw]
    if snapshots[len(snapshots)-1]["attacker"]["hp"] > 0 and snapshots[len(snapshots)-1]["defender"]["hp"] < 0:
        return [1, 0, 0, snapshots]
    elif snapshots[len(snapshots)-1]["attacker"]["hp"] < 0 and snapshots[len(snapshots)-1]["defender"]["hp"] > 0:
        return [0, 1, 0, snapshots]
    else:
        return [0, 0, 1, snapshots]

        
# Attacking Pokemon
attack_pokemon = "Jolteon"
attack_quick = "Thunder Shock"
attack_charge = "Discharge"
attack_ivs = {
    "attack" : 15,
    "defense" : 15,
    "stamina" : 15
}
attack_cpm = 1

# Defending Pokemon
defense_pokemon = "Gyarados"
defense_quick = "Dragon Tail"
defense_charge = "Outrage"
defense_ivs = {
    "attack" : 15,
    "defense" : 15,
    "stamina" : 15
}
defense_cpm = 1

# Constants
time = 60
delta = 0.01
print_ = False
print_Only_Attacks = False
numOfTrials = 1000
    
def main(argv):
    global attack_pokemon
    global defense_pokemon
    global numOfTrials
    
    importPokemon()
    importQuickMoves()
    importChargeMoves()
    importAttackTypeEffectiveness()
    results = [0, 0, 0, {}]
    for i in range(0, numOfTrials):
        counter = 1
        result = simulateGymAttack()
        results[0] += result[0]
        results[1] += result[1]
        results[2] += result[2]
        results[3][i] = result[3]
    print "%s vs %s" % (attack_pokemon, defense_pokemon, )
    print "Num of trials: %d" % (numOfTrials, )
    print "Attacker Win Rate: %1.2f" % (float(results[0]) / float(numOfTrials), )
    print "Attacker Loss Rate: %1.2f" % (float(results[1]) / float(numOfTrials), )
    print "Draw Rate: %1.2f" % (float(results[2]) / float(numOfTrials), )

if __name__=='__main__':
    main(sys.argv[1:])
