#!/usr/bin/python
"""

 Copyright 2016 Paul Willworth <ioscode@gmail.com>

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
from xml.dom import minidom
import ghShared
#import locale
#

form = cgi.FieldStorage()
# Get Cookies
errorstr = ''
cookies = Cookie.SimpleCookie()
try:
    cookies.load(os.environ['HTTP_COOKIE'])
except KeyError:
    errorstr = 'no cookies\n'

if errorstr == '':
    try:
        currentUser = cookies['userID'].value
    except KeyError:
        currentUser = ''
    try:
        sid = cookies['gh_sid'].value
    except KeyError:
        sid = form.getfirst('gh_sid', '')
else:
    currentUser = ''
    loginResult = 'success'
    sid = form.getfirst('gh_sid', '')


galaxy = form.getfirst('galaxy', '')
planet = form.getfirst('planetName', '')
wpID = form.getfirst('wpID', '')
spawnName = form.getfirst('spawnName', '')
mine = form.getfirst('mine','undefined')
friends = form.getfirst('friends','undefined')
pub = form.getfirst('pub','undefined')
dshared = form.getfirst('dshared','undefined')
minCon = form.getfirst('minCon','')
uweeks = form.getfirst('uweeks','')
sortType = form.getfirst('sortType','')
# escape input to prevent sql injection
sid = dbShared.dbInsertSafe(sid)
galaxy = dbShared.dbInsertSafe(galaxy)
planet = dbShared.dbInsertSafe(planet)
wpID = dbShared.dbInsertSafe(wpID)
spawnName = dbShared.dbInsertSafe(spawnName)
mine = dbShared.dbInsertSafe(mine)
friends = dbShared.dbInsertSafe(friends)
pub = dbShared.dbInsertSafe(pub)
dshared = dbShared.dbInsertSafe(dshared)
minCon = dbShared.dbInsertSafe(minCon)
uweeks = dbShared.dbInsertSafe(uweeks)

# Get a session
logged_state = 0
linkappend = ''

sess = dbSession.getSession(sid, 2592000)
if (sess != ''):
    logged_state = 1
    currentUser = sess
    linkappend = 'gh_sid=' + sid

# Main program
result = ''
setCriteria = ''
rowLimitStr = ''
ownerCriteria = ''
sortString = ''
print 'Content-type: text/xml\n'
doc = minidom.Document()
eRoot = doc.createElement("result")
doc.appendChild(eRoot)

eGroup = doc.createElement("waypoints")
eRoot.appendChild(eGroup)

errstr = ""
if (galaxy.isdigit() == False):
	errstr = errstr + "Error: no galaxy selected. \r\n"
if mine != 'on' and friends != 'on' and pub != 'on' and dshared != 'on' and len(wpID) < 1:
	errstr = errstr + "Error: you must select at least one waypoint owner type in filters. \r\n"

#if (planet == "" and wpID == "" and spawnName == ""):
#	errstr = errstr + "Error: you must provide a planet, waypoint id, or spawn name criteria. \r\n"

if errstr == "":
	try:
		conn = dbShared.ghConn()
		cursor = conn.cursor()
	except Exception:
		result = "Error: could not connect to database"

	if (cursor):
		# set resource availability criteria
		if wpID == '':
			if uweeks.isdigit() and uweeks > 0:
				setCriteria += ' AND (tResources.unavailable IS NULL OR DATEDIFF(NOW(),tResources.unavailable) <= ' + str(int(uweeks) * 7) + ')'
			elif sortType == 'spawn':
				setCriteria += ' AND tWaypoint.unavailable IS NULL'
			else:
				setCriteria += ' AND tResources.unavailable IS NULL AND tWaypoint.unavailable IS NULL'

		# set primary criteria and and row limits
		if len(wpID) > 0:
			setCriteria += ' AND waypointID=' + wpID
		elif len(spawnName) > 0:
			setCriteria += ' AND spawnName=\'' + spawnName + '\''
			rowLimitStr = ' LIMIT 10'
		elif len(planet) > 0:
			setCriteria += ' AND tWaypoint.planetID=(SELECT planetID FROM tPlanet WHERE galaxy IN (0, ' + galaxy + ') AND LOWER(REPLACE(planetName," ","")) = "' + planet + '")'
		else:
			setCriteria += ' AND waypointType=\'u\''
			rowLimitStr = ' LIMIT 10'

		# set sorting
		if sortType == 'recent':
			sortString = ' ORDER BY entered DESC'
		else:
			sortString = ' ORDER BY concentration DESC'

		# set waypoint concentration criteria
		if minCon.isdigit() and minCon > 0:
			setCriteria += ' AND concentration >=' + minCon

		# set waypoint owner criteria
		#for later when nonpublic waypoints in
		#if logged_state == 1:
		#	if mine == 'on' or len(wpID) > 0:
		#		ownerCriteria += 'owner="' + currentUser + '"'
		#	if friends == 'on':
		#		ownerCriteria += ' OR (shareLevel=64 AND owner IN (SELECT f1.friendID FROM tUserFriends f1 INNER JOIN tUserFriends f2 ON f1.userID=f2.friendID WHERE f1.userID="' + currentUser + '"))'
		#	if pub == 'on':
		#		ownerCriteria += ' OR waypointID IN (SELECT uw.waypointID FROM tUserWaypoints uw WHERE unlocked IS NOT NULL AND uw.userID="' + currentUser + '")'
		#else:
		#	ownerCriteria += ' owner=""'

		if dshared == 'on':
			ownerCriteria += ' OR shareLevel=256'

		if ownerCriteria[0:4] == ' OR ':
			ownerCriteria = ownerCriteria[4:]

		if len(ownerCriteria) > 0:
			ownerCriteria = ' AND (' + ownerCriteria + ')'

		#sys.stderr.write('WHERE (CASE WHEN galaxy IS NULL THEN ' + galaxy + ' ELSE galaxy END)=' + galaxy + ' AND (' + ownerCriteria + ')' + setCriteria + sortString + rowLimitStr + ';')
		wpSql = 'SELECT waypointID, spawnName, owner, concentration, lattitude, longitude, waypointType, waypointName, price, shareLevel, planetName, tWaypoint.entered, tResources.resourceType, resourceTypeName, (SELECT Count(userID) FROM tUserEvents ue WHERE ue.targetType=\'w\' AND ue.targetID=waypointID AND ue.eventType=\'r\') AS delCount, (SELECT Count(userID) FROM tUserEvents ue WHERE ue.targetType=\'w\' AND ue.targetID=waypointID AND ue.eventType=\'v\') AS verCount FROM tWaypoint LEFT JOIN tResources ON tWaypoint.spawnID = tResources.spawnID LEFT JOIN tResourceType ON tResources.resourceType = tResourceType.resourceType INNER JOIN tPlanet ON tWaypoint.planetID = tPlanet.planetID WHERE (CASE WHEN tResources.galaxy IS NULL THEN ' + galaxy + ' ELSE tResources.galaxy END)=' + galaxy + ownerCriteria + setCriteria + sortString + rowLimitStr + ';'
		cursor.execute(wpSql)
		row = cursor.fetchone()

		while (row != None):
			wpID = str(row[0])

			eWaypoint = doc.createElement("waypoint")
			eWaypoint.setAttribute("id",str(row[0]))
			eGroup.appendChild(eWaypoint)

			eSpawn = doc.createElement("spawn")
			tSpawn = doc.createTextNode(str(row[1]))
			eSpawn.appendChild(tSpawn)
			eWaypoint.appendChild(eSpawn)

			eOwner = doc.createElement("owner")
			tOwner = doc.createTextNode(str(row[2]))
			eOwner.appendChild(tOwner)
			eWaypoint.appendChild(eOwner)

			eFetcher = doc.createElement("fetcher")
			if logged_state == 1:
				tFetcher = doc.createTextNode(currentUser)
			else:
				tFetcher = doc.createTextNode("")
			eFetcher.appendChild(tFetcher)
			eWaypoint.appendChild(eFetcher)

			eLat = doc.createElement("lattitude")
			tLat = doc.createTextNode(str(row[4]))
			eLat.appendChild(tLat)
			eWaypoint.appendChild(eLat)

			eLon = doc.createElement("longitude")
			tLon = doc.createTextNode(str(row[5]))
			eLon.appendChild(tLon)
			eWaypoint.appendChild(eLon)

			eConcentration = doc.createElement("concentration")
			tConcentration = doc.createTextNode(str(row[3]))
			eConcentration.appendChild(tConcentration)
			eWaypoint.appendChild(eConcentration)

			eType = doc.createElement("waypointType")
			tType = doc.createTextNode(str(row[6]))
			eType.appendChild(tType)
			eWaypoint.appendChild(eType)

			eTitle = doc.createElement("title")
			tTitle = doc.createTextNode(row[7])
			eTitle.appendChild(tTitle)
			eWaypoint.appendChild(eTitle)

			ePlanet = doc.createElement("planet")
			tPlanet = doc.createTextNode(row[10])
			ePlanet.appendChild(tPlanet)
			eWaypoint.appendChild(ePlanet)

			eAdded = doc.createElement("added")
			tAdded = doc.createTextNode(ghShared.timeAgo(row[11]))
			eAdded.appendChild(tAdded)
			eWaypoint.appendChild(eAdded)

			eAddedTime = doc.createElement("addedTime")
			tAddedTime = doc.createTextNode(str(row[11]))
			eAddedTime.appendChild(tAddedTime)
			eWaypoint.appendChild(eAddedTime)

			eResTypeID = doc.createElement("resTypeID")
			tResTypeID = doc.createTextNode(str(row[12]))
			eResTypeID.appendChild(tResTypeID)
			eWaypoint.appendChild(eResTypeID)

			eResType = doc.createElement("resType")
			tResType = doc.createTextNode(str(row[13]))
			eResType.appendChild(tResType)
			eWaypoint.appendChild(eResType)

			#locale.setlocale(locale.LC_ALL, "en_US.utf8")
			ePrice = doc.createElement("price")
			tPrice = doc.createTextNode(str(row[8]))
			#tPrice = doc.createTextNode(locale.format("%d",row[8],True))
			ePrice.appendChild(tPrice)
			eWaypoint.appendChild(ePrice)

			eShare = doc.createElement("shareLevel")
			tShare = doc.createTextNode(str(row[9]))
			eShare.appendChild(tShare)
			eWaypoint.appendChild(eShare)

			eDeleteCount = doc.createElement("delCount")
			tDeleteCount = doc.createTextNode(str(row[14]))
			eDeleteCount.appendChild(tDeleteCount)
			eWaypoint.appendChild(eDeleteCount)

			eVerifyCount = doc.createElement("verCount")
			tVerifyCount = doc.createTextNode(str(row[15]))
			eVerifyCount.appendChild(tVerifyCount)
			eWaypoint.appendChild(eVerifyCount)

			result = "found"
			row = cursor.fetchone()

		cursor.close()
		conn.close()
	else:
		result = "Error: could not connect to database"
else:
	result = errstr

eText = doc.createElement("resultText")
tText = doc.createTextNode(result)
eText.appendChild(tText)
eRoot.appendChild(eText)

print doc.toxml()
if (result.find("Error:") > -1):
	sys.exit(500)
else:
	sys.exit(200)
