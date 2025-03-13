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

import os
import sys
import cgi
import pymysql
import dbShared


def getStatList():
	result = ''
	result += '    <option value="ER">Entangle Resist</option>'
	result += '    <option value="CR">Cold Resist</option>'
	result += '    <option value="CD">Conductivity</option>'
	result += '    <option value="DR">Decay Resist</option>'
	result += '    <option value="FL">Flavor</option>'
	result += '    <option value="HR">Heat Resist</option>'
	result += '    <option value="MA">Malleability</option>'
	result += '    <option value="PE">Potential Energy</option>'
	result += '    <option value="OQ">Overall Quality</option>'
	result += '    <option value="SR">Shock Resist</option>'
	result += '    <option value="UT">Unit Toughness</option>'
	return result

def getThemeList():
	result = ''
	result += '      <option value="ghAlpha">Alpha Blue</option>'
	result += '      <option value="crafter">Crafter Grey</option>'
	result += '      <option value="Destroyer">Destroyer</option>'
	result += '      <option value="FSJediGray">FS Jedi</option>'
	result += '      <option value="Hutt">Hutt</option>'
	result += '      <option value="Imperial">Imperial</option>'
	result += '      <option value="ghOriginal">Original</option>'
	result += '      <option value="Rebel">Rebel</option>'
	result += '      <option value="rebelFlightSuits">Rebel Flight Suits</option>'
	result += '      <option value="WinduPurple">Windu Purple</option>'
	result += '      <option value="modernDarkMode">Dark Mode</option>'
	return result

def getSchematicTabList():
	result = ''
	result += '    <option value="1">Weapon</option>'
	result += '    <option value="2">Armor</option>'
	result += '    <option value="4">Food</option>'
	result += '    <option value="8">Clothing</option>'
	result += '    <option value="16">Vehicle</option>'
	result += '    <option value="32">Droid</option>'
	result += '    <option value="64">Chemical</option>'
	result += '    <option value="128">Bio-Chemical</option>'
	result += '    <option value="256">Creature</option>'
	result += '    <option value="512">Furniture</option>'
	result += '    <option value="1024">Installation</option>'
	result += '    <option value="2048">Jedi</option>'
	result += '    <option value="8192">Genetics</option>'
	result += '    <option value="131072">Starship Components</option>'
	result += '    <option value="262144">Ship Tools</option>'
	result += '    <option value="524288">Misc</option>'
	return result

def getGalaxyStatusList():
	result = ''
	result += '    <option value="0">Draft</option>'
	result += '    <option value="1">Active</option>'
	result += '    <option value="2">Inactive</option>'
	result += '    <option value="3">Removed</option>'
	return result

def getOptionList(sqlStr):
	result = ""
	thisGroup = ""
	conn = dbShared.ghConn()
	cursor = conn.cursor()
	if (cursor):
		cursor.execute(sqlStr)
		row = cursor.fetchone()
		while (row != None):
			if len(row)>2:
				if thisGroup == '':
					result = result + '  <optgroup label="' + str(row[2]) + '">'
					thisGroup = str(row[2])
				elif thisGroup != str(row[2]):
					result = result + '  </optgroup>'
					result = result + '  <optgroup label="' + str(row[2]) + '">'
					thisGroup = str(row[2])

				result = result + '  <option value="' + str(row[0]) + '" group="' + str(row[2]) + '">' + row[1] + '</option>'
			elif len(row)>1:
				result = result + '  <option value="' + str(row[0]) + '">' + row[1] + '</option>'
			else:
				result = result + '  <option>' + row[0] + '</option>'
			row = cursor.fetchone()
		cursor.close()
	conn.close()
	if thisGroup != "":
		result = result + '  </optgroup>'

	return result

def getResourceTypeList(galaxy='-1'):
	if galaxy != '-1':
		sqlStr = """
			SELECT
				tResourceType.resourceType,
				resourceTypeName
			FROM
				tResourceType
				LEFT JOIN tGalaxyResourceType tgrt ON tgrt.resourceType = tResourceType.resourceType AND tgrt.galaxyID = {0}
			WHERE
				(
					specificPlanet = 0
					OR specificPlanet IN (
						SELECT
							DISTINCT tPlanet.planetID
						FROM tPlanet, tGalaxyPlanet
						WHERE (tPlanet.planetID < 11) OR (tPlanet.planetID = tGalaxyPlanet.planetID AND tGalaxyPlanet.galaxyID = {0})
					)
				) AND (elective = 0 OR tgrt.resourceType IS NOT NULL)
			ORDER BY resourceTypeName;
		""".format(galaxy)

		listStr = getOptionList(sqlStr)
	else:
		listStr = getOptionList('SELECT resourceType, resourceTypeName FROM tResourceType ORDER BY resourceTypeName;')
	return listStr

def getResourceGroupList():
	listStr = getOptionList('SELECT resourceGroup, groupName FROM tResourceGroup WHERE groupLevel > 1 ORDER BY groupName;')
	return listStr

def getResourceGroupListShort():
	listStr = getOptionList('SELECT resourceGroup, groupName FROM tResourceGroup WHERE groupLevel < 4 AND groupLevel > 1 ORDER BY groupName;')
	return listStr

def getGalaxyList():
	listStr = getOptionList('SELECT galaxyID, CASE WHEN galaxyNGE > 0 THEN CONCAT(galaxyName, \' [NGE]\') ELSE galaxyName END, CASE WHEN galaxyState=1 THEN "Active" ELSE "Inactive" END FROM tGalaxy WHERE galaxyState > 0 AND galaxyState < 3 ORDER BY galaxyState, galaxyName;')
	return listStr

def getPlanetList(galaxy):
	if galaxy == -1 or galaxy == '':
		listStr = getOptionList('SELECT planetID, planetName FROM tPlanet ORDER BY planetName')
	else:
		listStr = getOptionList('SELECT DISTINCT tPlanet.planetID, planetName FROM tPlanet, tGalaxyPlanet WHERE (tPlanet.planetID < 11) OR (tPlanet.planetID = tGalaxyPlanet.planetID AND tGalaxyPlanet.galaxyID = {0}) ORDER BY planetName;'.format(galaxy))
	return listStr

def getProfessionList(galaxy):
	if galaxy == -1 or galaxy == '':
		listStr = getOptionList('SELECT profID, profName FROM tProfession WHERE galaxy=0 ORDER BY profName;')
	else:
		listStr = getOptionList('SELECT profID, profName FROM tProfession WHERE galaxy IN ({1},{0}) ORDER BY profName'.format(str(galaxy), dbShared.getBaseProfs(galaxy)))
	return listStr

def getObjectTypeList():
	listStr = getOptionList('SELECT objectType, typeName FROM tObjectType ORDER BY typeName;')
	return listStr
