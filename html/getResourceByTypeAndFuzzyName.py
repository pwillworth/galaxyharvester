#!/usr/bin/python
"""

 Copyright 2010 Paul Willworth <ioscode@gmail.com>

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
import Cookie
import dbSession
import dbShared
import cgi
import MySQLdb
import ghLists
import difflib
from xml.dom import minidom
#

form = cgi.FieldStorage()

spawnName = form.getfirst('name', '')
galaxy = form.getfirst('galaxy', '')
resType = form.getfirst('resType', '')
# escape input to prevent sql injection
spawnName = dbShared.dbInsertSafe(spawnName)
galaxy = dbShared.dbInsertSafe(galaxy)
resType = dbShared.dbInsertSafe(resType)



# Main program

print 'Content-type: text/xml\n'
doc = minidom.Document()
eRoot = doc.createElement("result")
doc.appendChild(eRoot)

try:
	conn = dbShared.ghConn()
	cursor = conn.cursor()
except Exception:
	result = "Error: could not connect to database"

result = "new"

if (cursor):
	sqlStr = 'SELECT spawnID, spawnName, CR, CD, DR, FL, HR, MA, PE, OQ, SR, UT, ER FROM tResources WHERE galaxy=' + galaxy + ' AND resourceType="' + resType + '" AND unavailable IS NULL;'
	#sys.stderr.write(sqlStr + "\n")
	cursor.execute(sqlStr)
	row = cursor.fetchone()

	while (row != None):
		#sys.stderr.write(row[1]+"\n")
		if len(difflib.get_close_matches(spawnName, [row[1]], 1, 0.7)) > 0:
			spawnID = str(row[0])

			eSpawn = doc.createElement("spawnID")
			tSpawn = doc.createTextNode(spawnID)
			eSpawn.appendChild(tSpawn)
			eRoot.appendChild(eSpawn)

			eName = doc.createElement("spawnName")
			tName = doc.createTextNode(row[1])
			eName.appendChild(tName)
			eRoot.appendChild(eName)

			eCR = doc.createElement("CR")
			tCR = doc.createTextNode(str(row[2]))
			eCR.appendChild(tCR)
			eRoot.appendChild(eCR)

			eCD = doc.createElement("CD")
			tCD = doc.createTextNode(str(row[3]))
			eCD.appendChild(tCD)
			eRoot.appendChild(eCD)

			eDR = doc.createElement("DR")
			tDR = doc.createTextNode(str(row[4]))
			eDR.appendChild(tDR)
			eRoot.appendChild(eDR)

			eFL = doc.createElement("FL")
			tFL = doc.createTextNode(str(row[5]))
			eFL.appendChild(tFL)
			eRoot.appendChild(eFL)

			eHR = doc.createElement("HR")
			tHR = doc.createTextNode(str(row[6]))
			eHR.appendChild(tHR)
			eRoot.appendChild(eHR)

			eMA = doc.createElement("MA")
			tMA = doc.createTextNode(str(row[7]))
			eMA.appendChild(tMA)
			eRoot.appendChild(eMA)

			ePE = doc.createElement("PE")
			tPE = doc.createTextNode(str(row[8]))
			ePE.appendChild(tPE)
			eRoot.appendChild(ePE)

			eOQ = doc.createElement("OQ")
			tOQ = doc.createTextNode(str(row[9]))
			eOQ.appendChild(tOQ)
			eRoot.appendChild(eOQ)

			eSR = doc.createElement("SR")
			tSR = doc.createTextNode(str(row[10]))
			eSR.appendChild(tSR)
			eRoot.appendChild(eSR)

			eUT = doc.createElement("UT")
			tUT = doc.createTextNode(str(row[11]))
			eUT.appendChild(tUT)
			eRoot.appendChild(eUT)

			eER = doc.createElement("ER")
			tER = doc.createTextNode(str(row[12]))
			eER.appendChild(tER)
			eRoot.appendChild(eER)

			pcursor = conn.cursor()
			pcursor.execute('SELECT tResourcePlanet.planetID, planetName FROM tResourcePlanet INNER JOIN tPlanet ON tResourcePlanet.planetID=tPlanet.planetID WHERE spawnID="' + spawnID + '";')
			prow = pcursor.fetchone()
			planets = ""
			planetNames = ""
			while (prow != None):
				planets = planets + str(prow[0]) + ","
				planetNames = planetNames + prow[1] + ", "
				prow = cursor.fetchone()

			if (len(planetNames) > 0):
				planetNames = planetNames[0:len(planetNames)-2]

			ePlanets = doc.createElement("Planets")
			tPlanets = doc.createTextNode(planetNames)
			ePlanets.appendChild(tPlanets)
			eRoot.appendChild(ePlanets)

			result = "found"
			break

		row = cursor.fetchone()
	else:
		result = "new"
	cursor.close()
	conn.close()
else:
	result = "Error: could not connect to database"

eText = doc.createElement("resultText")
tText = doc.createTextNode(result)
eText.appendChild(tText)
eRoot.appendChild(eText)

print doc.toxml()
if (result.find("Error:") > -1):
	sys.exit(500)
else:
	sys.exit(200)

