#!/usr/bin/env python3
"""

 Copyright 2020 Paul Willworth <ioscode@gmail.com>

 This file is part of Galaxy Harvester.

 Galaxy Harvester is free software: you can redistribute it and/or modify
 it under the terms of the GNU Affero General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.

 Galaxy Harvester is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU Affero General Public License for more details.

 You should have received a copy of the GNU Affero General Public License
 along with Galaxy Harvester.  If not, see <http://www.gnu.org/licenses/>.

"""

import pymysql
import dbShared
#

def getItemName(sqlStr):
    result = ""
    conn = dbShared.ghConn()
    cursor = conn.cursor()
    if (cursor):
        cursor.execute(sqlStr)
        row = cursor.fetchone()
        if (row != None):
            result = row[1]
    cursor.close()
    conn.close()
    return result

def getPlanetName(planetid):
    nameStr = getItemName('SELECT planetID, planetName FROM tPlanet WHERE planetID='+dbShared.dbInsertSafe(str(planetid))+';')
    return nameStr

def getSpawnName(spawnid):
    nameStr = getItemName('SELECT spawnID, spawnName FROM tResources WHERE spawnID='+dbShared.dbInsertSafe(str(spawnid))+';')
    return nameStr

def getResourceTypeName(typeid):
    nameStr = getItemName('SELECT resourceType, resourceTypeName FROM tResourceType WHERE resourceType="'+dbShared.dbInsertSafe(typeid)+'";')
    return nameStr

def getResourceGroupName(groupid):
    nameStr = getItemName('SELECT resourceGroup, groupName FROM tResourceGroup WHERE resourceGroup="'+dbShared.dbInsertSafe(groupid)+'";')
    return nameStr

def getGalaxyName(galaxyid):
    nameStr = getItemName('SELECT galaxyID, galaxyName FROM tGalaxy WHERE galaxyID="'+dbShared.dbInsertSafe(galaxyid)+'";')
    return nameStr

def getStatName(stat):
	if (stat == 'CR'):
		return 'Cold Resist'
	elif (stat == 'CD'):
		return 'Conductivity'
	elif (stat == 'DR'):
		return 'Decay Resist'
	elif (stat == 'FL'):
		return 'Flavor'
	elif (stat == 'HR'):
		return 'Heat Resist'
	elif (stat == 'MA'):
		return 'Malleability'
	elif (stat == 'PE'):
		return 'Potential Energy'
	elif (stat == 'OQ'):
		return 'Overall Quality'
	elif (stat == 'SR'):
		return 'Shock Resist'
	elif (stat == 'UT'):
		return 'Unit Toughness'
	elif (stat == 'ER'):
		return 'Entangle Resist'
	else:
		return stat
