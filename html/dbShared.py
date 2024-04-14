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
import sys
import time
from datetime import timedelta, datetime
sys.path.append("../")
import dbInfo
import subprocess
import ghObjects
import ghNames
import ghShared
import difflib

def ghConn():
	conn = pymysql.connect(host = dbInfo.DB_HOST,
	db = dbInfo.DB_NAME,
	user = dbInfo.DB_USER,
	passwd = dbInfo.DB_PASS)
	conn.autocommit(True)
	return conn

def dbInsertSafe(insertStr):
	newStr = ""
	if (insertStr != None):
		for i in range(len(str(insertStr))):
			if (str(insertStr)[i] == "'"):
				newStr = newStr + "'"
			newStr = newStr + str(insertStr)[i]
	return newStr

def n2n(inVal):
	if (inVal == '' or inVal == None or inVal == 'undefined' or inVal == 'None'):
		return 'NULL'
	else:
		return str(inVal)

# update resource activity stats tracking
def logEvent(sqlStr, eventType, user, galaxy, spawnID):
	conn = ghConn()
	cursor = conn.cursor()
	if (cursor):
		cursor.execute(sqlStr)

		# Create a user stats row if it does not exist yet
		cursor.execute("SELECT userID FROM tUserStats WHERE userID='" + user + "' AND galaxy=" + str(galaxy) + ";")
		row = cursor.fetchone()
		if (row == None):
			cursor.execute("INSERT INTO tUserStats (userID, galaxy, added, planet, edited, removed, verified, waypoint, repGood, repBad) VALUES ('" + user + "'," + str(galaxy) + ",0,0,0,0,0,0,0,0);")

		if eventType == 'a':
			cursor.execute("UPDATE tGalaxy SET totalSpawns = totalSpawns + 1 WHERE galaxyID=" + str(galaxy) + ";")
			cursor.execute("UPDATE tUserStats SET added = added + 1 WHERE userID = '" + user + "' AND galaxy=" + str(galaxy) + ";")
		elif eventType == 'p':
			cursor.execute("UPDATE tUserStats SET planet = planet + 1 WHERE userID = '" + user + "' AND galaxy=" + str(galaxy) + ";")
		elif eventType == 'e':
			cursor.execute("UPDATE tUserStats SET edited = edited + 1 WHERE userID = '" + user + "' AND galaxy=" + str(galaxy) + ";")
		elif eventType == 'r':
			cursor.execute("UPDATE tUserStats SET removed = removed + 1 WHERE userID = '" + user + "' AND galaxy=" + str(galaxy) + ";")
			# check if any planets still available
			markAll = 0
			cursor.execute("SELECT enteredBy FROM tResourcePlanet WHERE spawnID=" + str(spawnID) + " AND unavailable IS NULL;")
			row = cursor.fetchone()
			if (row == None):
				markAll = 1
			# update main table when all planets unavailable
			if (markAll == 1):
				updateSQL = "UPDATE tResources SET unavailable=NOW(), unavailableBy='" + user + "' WHERE spawnID=" + str(spawnID) + ";"
				cursor.execute(updateSQL)
		elif eventType == 'v':
			cursor.execute("UPDATE tUserStats SET verified = verified + 1 WHERE userID = '" + user + "' AND galaxy=" + str(galaxy) + ";")
		elif eventType == 'w':
			cursor.execute("UPDATE tGalaxy SET totalWaypoints = totalWaypoints + 1 WHERE galaxyID=" + str(galaxy) + ";")
			cursor.execute("UPDATE tUserStats SET waypoint = waypoint + 1 WHERE userID = '" + user + "' AND galaxy=" + str(galaxy) + ";")
		elif eventType == '+':
			cursor.execute("UPDATE tUserStats SET repGood = repGood + 1 WHERE userID = '" + user + "' AND galaxy=" + str(galaxy) + ";")
			checkUserAbilities(conn, user, galaxy)
		elif eventType == '-':
			cursor.execute("UPDATE tUserStats SET repBad = repBad + 1 WHERE userID = '" + user + "' AND galaxy=" + str(galaxy) + ";")
		cursor.close()
	conn.close()
	# Also log a user event for verifications and corrections
	if eventType == 'r' or eventType == 'v' or eventType == 'n' or eventType == 'g' or (eventType == 'p' and 'previously unavailable' in sqlStr):
		logUserEvent(user, galaxy, 'r', spawnID, eventType)

def logUserEvent(user, galaxy, targetType, targetID, eventType):
	conn = ghConn()
	cursor = conn.cursor()
	if (cursor):
		# Check if user is experienced enough to give rep bonus
		expGood = False
		# Exclude automated users
		if (user not in ghShared.automatedUsers):
			cursor.execute("SELECT added, repBad FROM tUserStats WHERE userID=%s AND galaxy=%s;", (user, galaxy))
			row = cursor.fetchone()
			if (row != None and row[0] != None):
				if (row[0] > (row[1] + 3)):
					expGood = True

		link = ""
		message = ""
		if eventType == "v" and expGood == True:
			# Get target User if target is resource
			if targetType == "r":
				cursor.execute("SELECT enteredBy, spawnName FROM tResources WHERE spawnID=" + str(targetID) + ";")
				row = cursor.fetchone()
				if (row != None):
					targetUser = row[0]
					link = "/resource.py/" + str(galaxy) + "/" + row[1]
					message = "You gained 1 reputation because someone verified your resource!"
			# Get target user if target is waypoint
			elif targetType == "w":
				cursor.execute("SELECT owner, spawnName FROM tWaypoint INNER JOIN tResources ON tWaypoint.spawnID = tResources.spawnID WHERE waypointID=" + str(targetID) + ";")
				row = cursor.fetchone()
				if (row != None):
					targetUser = row[0]
					link = "/resource.py/" + str(galaxy) + "/" + row[1]
					message = "You gained 1 reputation because someone verified your waypoint!"
			# Increment rep on target user for verification of their entry
			if targetUser != None:
				logEvent("INSERT INTO tUserEvents (userID, targetType, targetID, eventType, eventTime, causeEventType) VALUES ('" + targetUser + "', '" + targetType + "', " + str(targetID) + ", '+', NOW(), '" + eventType + "');", "+", targetUser, galaxy, targetID)
				cursor.execute("INSERT INTO tAlerts (userID, alertType, alertTime, alertMessage, alertLink, alertStatus) VALUES ('" + targetUser + "', 1, NOW(), '" + message + "', '" + link + "', 0);")

		if (eventType == "n" or eventType == "g") and expGood == True:
			# Get target user that entered the resource that is being corrected
			cursor.execute("SELECT userID, eventTime FROM tResourceEvents WHERE spawnID=%s AND eventType IN ('a','{0}') ORDER BY eventTime DESC;".format(eventType), targetID)
			eventRow = cursor.fetchone()
			targetUser = ''
			while eventRow != None:
				tt = datetime.fromtimestamp(time.time()) - eventRow[1]
				# Ignore if user is correcting themself or the previous action was too long ago
				if eventRow[0] != user and tt.days < 28:
					targetUser = eventRow[0]
				eventRow = cursor.fetchone()
			# Decrement rep on target user for entering a resource with a misspelled name or wrong galaxy
			if targetUser != '':
				# Only allow each user to do this once per resource though
				checkCursor = conn.cursor()
				checkCursor.execute("SELECT eventTime FROM tUserEvents WHERE userID=%s AND targetID=%s AND eventType=%s;",(user, targetID, eventType))
				checkRow = checkCursor.fetchone()
				if checkRow == None:
					link = "/resource.py/" + str(galaxy) + "/" + ghNames.getSpawnName(targetID)
					message = "You lost 1 reputation because your resource entry had to be corrected!"
					logEvent("INSERT INTO tUserEvents(userID, targetType, targetID, eventType, eventTime, causeEventType) VALUES ('" + targetUser + "', '" + targetType + "', " + str(targetID) + ", '-', NOW(), '" + eventType + "');","-", targetUser, galaxy, targetID)
					cursor.execute("INSERT INTO tAlerts(userID, alertType, alertTime, alertMessage, alertLink, alertStatus) VALUES ('" + targetUser + "', 1, NOW(), '" + message + "', '" + link + "', 0);")
				checkCursor.close()

		if eventType == "p" and expGood == True:
			# Get target user that marked the resource unavailable that is being corrected
			cursor.execute("SELECT userID, eventTime FROM tResourceEvents WHERE spawnID=%s AND eventType IN ('r') ORDER BY eventTime DESC;", (targetID))
			eventRow = cursor.fetchone()
			targetUser = ''
			while eventRow != None:
				tt = datetime.fromtimestamp(time.time()) - eventRow[1]
				# Ignore if user is correcting themself or the previous action was too long ago
				if eventRow[0] != user and tt.days < 28:
					targetUser = eventRow[0]
				eventRow = cursor.fetchone()
			# Decrement rep on target user for marking resource unavailable that is still available
			if targetUser != '':
				# Only allow each user to do this once per resource though
				checkCursor = conn.cursor()
				checkCursor.execute("SELECT eventTime FROM tUserEvents WHERE userID=%s AND targetID=%s AND eventType=%s;",(user, targetID, eventType))
				checkRow = checkCursor.fetchone()
				if checkRow == None:
					link = "/resource.py/" + str(galaxy) + "/" + ghNames.getSpawnName(targetID)
					message = "You lost 1 reputation because you removed a resource that is still available!"
					logEvent("INSERT INTO tUserEvents(userID, targetType, targetID, eventType, eventTime, causeEventType) VALUES ('" + targetUser + "', '" + targetType + "', " + str(targetID) + ", '-', NOW(), '" + eventType + "');", "-", targetUser, galaxy, targetID)
					cursor.execute("INSERT INTO tAlerts(userID, alertType, alertTime, alertMessage, alertLink, alertStatus) VALUES ('" + targetUser + "', 1, NOW(), '" + message + "', '" + link + "', 0);")
				checkCursor.close()

		# add the event record
		cursor.execute("INSERT INTO tUserEvents (userID, targetType, targetID, eventType, eventTime) VALUES ('" + user + "','" + targetType + "'," + str(targetID) + ",'" + eventType + "',NOW());")
		cursor.close()
	conn.close()

def logSchematicEvent(spawnID, galaxy, schematicID, expGroup, eventType, eventDetail, serverBestMode):
	if serverBestMode == 'current':
		eventTable = 'tServerBestStatus'
	else:
		eventTable = 'tSchematicEvents'

	conn = ghConn()
	cursor = conn.cursor()
	try:
		cursor.execute('INSERT INTO {0} (galaxy, eventTime, eventType, schematicID, expGroup, spawnID, eventDetail) VALUES (%s, NOW(), %s, %s, %s, %s, %s);'.format(eventTable), [galaxy, eventType, schematicID, expGroup, spawnID, eventDetail])
	except pymysql.IntegrityError as e:
		sys.stderr.write('Tried to insert duplicate schematic event: ' + eventDetail)
	result = cursor.rowcount
	if result < 1:
		sys.stderr.write('Failed to insert schematic event: ' + eventDetail)

	cursor.close()
	conn.close()

def getUserAttr(user, attr):
	conn = ghConn()
	cursor = conn.cursor()
	cursor.execute('SELECT pictureName, emailAddress, themeName, created, inGameInfo, paidThrough, defaultAlertTypes, sharedInventory, sharedRecipes FROM tUsers WHERE userID="' + user + '"')
	row = cursor.fetchone()
	if (row != None):
		if attr == 'themeName':
			retAttr = row[2]
		elif attr == 'emailAddress':
			retAttr = row[1]
		elif attr == 'pictureName':
			if (row[0] == '' or row[0] == None):
				retAttr = 'default'
			else:
				retAttr = row[0]
		elif attr == 'created':
			retAttr = row[3]
		elif (attr == 'inGameInfo' and row[4] != None):
			retAttr = row[4]
		elif (attr == 'paidThrough' and row[5] != None):
			retAttr = row[5]
		elif (attr == 'defaultAlertTypes'):
			retAttr = row[6]
		elif (attr == 'sharedInventory'):
			retAttr = row[7]
		elif (attr == 'sharedRecipes'):
			retAttr = row[8]
		else:
			retAttr = ''
	else:
		retAttr = ''

	cursor.close()
	conn.close()
	return retAttr

# Returns total amount user has donated to the site
def getUserDonated(user):
	conn = ghConn()
	cursor = conn.cursor()
	cursor.execute('SELECT Sum(paymentGross) FROM tPayments WHERE payerEmail = (SELECT emailAddress FROM tUsers WHERE userID=%s)', [user])
	row = cursor.fetchone()
	if (row != None and row[0] != None):
		retAttr = str(row[0])
	else:
		retAttr = ''

	cursor.close()
	conn.close()
	return retAttr

# Returns honor badge title for user based on stats
def getUserTitle(user):
	stats = getUserStats(user, 0).split(',')
	resScore = int(stats[0])
	mapScore = int(stats[1])
	repScore = int(stats[2])
	if (resScore + mapScore + repScore > 0):
		# set resource title part
		if resScore > 2000:
			resTitle = "Reaper"
		elif resScore > 500:
			resTitle = "Hound"
		elif resScore > 25:
			resTitle = "Harvester"
		else:
			resTitle = "Seeker"
		# set mapping title part
		if mapScore > 400:
			mapTitle = "Cartographer"
		elif mapScore > 100:
			mapTitle = "Mapper"
		elif mapScore > 5:
			mapTitle = "Finder"
		else:
			mapTitle = "Seeker"
		# set reputation title part
		if repScore > 100:
			repTitle = "Revered "
		elif repScore > 50:
			repTitle = "Honored "
		elif repScore > 25:
			repTitle = "Verified "
		else:
			repTitle = ""

		# Determine Style
		if (resScore > 2000 or mapScore > 400) and repScore > 100:
			retAttr = '<span class="statMax">'
		elif (resScore > 500 or mapScore > 100) and repScore > 25:
			retAttr = '<span class="statHigh">'
		else:
			retAttr = '<span class="statNormal">'
		# build full title
		if (resScore / 5) > mapScore:
			retAttr = retAttr + repTitle + resTitle + '</span>'
		else:
			retAttr = retAttr + repTitle + mapTitle + '</span>'
	else:
		retAttr = '<span>Lurker</span>'

	return retAttr

def getUserStats(user, galaxy):
	conn = ghConn()
	cursor = conn.cursor()
    # Galaxy 0 passed just combine stats for all galaxies
	if (galaxy == 0):
		cursor.execute('SELECT Sum(added), Sum(planet), Sum(edited), Sum(removed), Sum(verified), Sum(waypoint), Sum(repGood), Sum(repBad) FROM tUserStats WHERE userID = %s', [user])
	else:
		cursor.execute('SELECT added, planet, edited, removed, verified, waypoint, repGood, repBad FROM tUserStats WHERE userID = %s AND galaxy = %s', [user, galaxy])
	row = cursor.fetchone()
	if (row != None and row[0] != None):
		# build composite scores
		resScore = int((float(row[0]) * 2) + (float(row[1]) / 2) + float(row[2]) + float(row[3]) + (float(row[4]) / 2))
		mapScore = int(float(row[5]))
		repScore = int(float(row[6]) - float(row[7]))
	else:
		resScore = mapScore = repScore = 0

	cursor.close()
	conn.close()
	return '{0},{1},{2}'.format(resScore, mapScore, repScore)

def getUserAdmin(conn, user, galaxy):
	admin = False
	cursor = conn.cursor()
	cursor.execute('SELECT roleType FROM tGalaxyUser WHERE userID=%s AND galaxyID=%s ORDER BY roleType;', [user, galaxy])
	row = cursor.fetchone()
	if (row != None and row[0] == 'a'):
		admin = True

	cursor.close()
	return admin

def getGalaxyAdminList(conn, userID):
        listHTML = ''
        cursor = conn.cursor()
        cursor.execute("SELECT tGalaxyUser.galaxyID, galaxyName FROM tGalaxyUser INNER JOIN tGalaxy ON tGalaxyUser.galaxyID = tGalaxy.galaxyID WHERE tGalaxyUser.userID='{0}' AND roleType='a' ORDER BY galaxyName;".format(userID))
        row = cursor.fetchone()
        while row != None:
                listHTML += '<option value="{0}">{1}</option>'.format(row[0], row[1])
                row = cursor.fetchone()
        cursor.close()
        return listHTML

def getLastResourceChange():
	conn = ghConn()
	cursor = conn.cursor()
	cursor.execute('SELECT Max(entered) FROM tResources')
	row = cursor.fetchone()
	if (row != None):
		retDate = row[0]
	else:
		retDate = ''

	cursor.close()
	conn.close()
	return retDate

def getLastExport(galaxy):
	conn = ghConn()
	cursor = conn.cursor()
	cursor.execute('SELECT lastExport FROM tGalaxy WHERE galaxyID=' + str(galaxy))
	row = cursor.fetchone()
	if (row != None and row[0] != None):
		retDate = row[0]
	else:
		retDate = 'never'

	cursor.close()
	conn.close()
	return retDate

def getPlanetID(planetName):
	conn = ghConn()
	cursor = conn.cursor()
	# Temporarily accept other form of Yavin IV during transition
	if 'avin' in planetName.lower():
		planetName = 'yavin4'
	###
	if 'kaas' in planetName.lower():
		planetName = 'dromundkaas'
	###
	cursor.execute('SELECT planetID FROM tPlanet WHERE LOWER(REPLACE(planetName," ","")) = "' + planetName.lower() + '";')
	row = cursor.fetchone()
	if (row != None and row[0] != None):
		retVal = str(row[0])
	else:
		retVal = "0"

	cursor.close()
	conn.close()
	return retVal

def galaxyState(galaxyID):
	# 0 = Unlaunched, 1 = Active, 2 = Retired
	conn = ghConn()
	cursor = conn.cursor()
	cursor.execute('SELECT galaxyState FROM tGalaxy WHERE galaxyID = ' + str(galaxyID) + ';')
	row = cursor.fetchone()
	if (row != None and row[0] != None):
		retVal = row[0]
	else:
		retVal = 0

	cursor.close()
	conn.close()
	return retVal

def getGalaxyAdmins(conn, galaxyID):
        admins = []
        cursor = conn.cursor()
        cursor.execute("SELECT userID FROM tGalaxyUser WHERE galaxyID=%s AND roleType='a';", [galaxyID])
        row = cursor.fetchone()
        while row != None:
                admins.append(row[0])
                row = cursor.fetchone()
        cursor.close()
        return admins

def friendStatus(uid, ofUser):
	# 0 = None, 1 = Added, 2 = Reciprocated
	conn = ghConn()
	cursor = conn.cursor()
	cursor.execute('SELECT uf1.added, uf2.added FROM tUserFriends uf1 LEFT JOIN tUserFriends uf2 ON uf1.friendID=uf2.userID AND uf1.userID=uf2.friendID WHERE uf1.userID = \'' + ofUser + '\' AND uf1.friendID = \'' + uid + '\';')
	row = cursor.fetchone()
	if (row != None and row[0] != None):
		if row[1] != None:
			retVal = 2
		else:
			retVal = 1
	else:
		retVal = 0

	cursor.close()
	conn.close()
	return retVal

def getSpawnID(resName, galaxy):
	conn = ghConn()
	cursor = conn.cursor()
	newid = -1
	if ( len(resName) > 0 and len(galaxy) > 0 ):
		cursor.execute("SELECT spawnID FROM tResources WHERE galaxy=" + galaxy + " AND spawnName='" + resName + "';")
		row = cursor.fetchone()
		if row != None:
			newid = row[0]

	cursor.close()
	conn.close()
	return newid

def getSpawnPlanets(conn, spawnID, availableOnly, galaxy):
	criteriaStr = ''
	planets = []
	cursor = conn.cursor()
	if (cursor):
		if availableOnly:
			criteriaStr = ' AND unavailable IS NULL'
		sqlStr = 'SELECT DISTINCT tPlanet.planetID, planetName, enteredBy FROM tGalaxyPlanet, tPlanet LEFT JOIN (SELECT planetID, enteredBy FROM tResourcePlanet WHERE spawnID='+str(spawnID)+criteriaStr+') trp ON tPlanet.planetID=trp.planetID WHERE (tPlanet.planetID < 11) OR (tPlanet.planetID = tGalaxyPlanet.planetID AND tGalaxyPlanet.galaxyID = '+str(galaxy)+') ORDER BY planetName;'
		cursor.execute(sqlStr)
		row = cursor.fetchone()
		while (row != None):
			p = ghObjects.resourcePlanet(row[0], row[1], row[2])
			planets.append(p)
			row = cursor.fetchone()
	cursor.close()
	return planets

def getResourceTypeID(conn, resourceTypeName):
	# try to figure out resource type id... sometimes name can different slighty from
	# some sources like Corellia vs. Corellian

	# Some servers like to be special and abbreviate the word Gemstone
	if resourceTypeName in ['Hothian Type 1 Amorphous Gem', 'Hothian Type 2 Amorphous Gem', 'Hothian Type 1 Crystalline Gem', 'Hothian Type 2 Crystalline Gem']:
		resourceTypeName = resourceTypeName + 'stone'
	typeID = ''
	cursor = conn.cursor()
	cursor.execute("SELECT resourceType, resourceTypeName FROM tResourceType;")
	row = cursor.fetchone()
	while row != None:
		if len(difflib.get_close_matches(resourceTypeName, [row[1]], 1, 0.97)) > 0:
			typeID = row[0]
		row = cursor.fetchone()
	cursor.close()
	return typeID

def getUserPostBlockedSecondsRemaining(userID, targetType):
	# Default not blocked
	retVal = 0
	conn = ghConn()
	cursor = conn.cursor()
	cursor.execute("SELECT eventTime FROM tUserEvents WHERE userID = '" + userID + "' AND eventType='-' AND targetType='" + targetType + "' AND causeEventType='r';")
	row = cursor.fetchone()
	# If user has negative reputation event in last 24 hours for this type, return remaining cooldown time
	if (row != None and row[0] != None):
		tt = datetime.fromtimestamp(time.time()) - row[0]
		if tt.days < 1:
			retVal = 86400 - tt.seconds

	cursor.close()
	conn.close()
	return retVal

def checkUserAbilities(conn, userID, galaxy):
	# See if Rep bonus has granted new ability and alert
	stats = getUserStats(userID, galaxy).split(',')
	reputation = int(stats[2])
	for k, v in ghShared.MIN_REP_VALS.items():
		if v == reputation:
			alertNewAbility(conn, userID, k, galaxy)

def alertNewAbility(conn, userID, abilityKey, galaxy):
    # Add alert with custom message about new ability user has unlocked
	message = "Congratuations!  You have unlocked a new ability on Galaxy Harvester in {1} galaxy.  You can now {0}.  Thanks for your contributions, and keep the the good work!".format(ghShared.ABILITY_DESCR[abilityKey], ghNames.getGalaxyName(galaxy))
	alertLink = "{0}user.py/{1}".format(ghShared.BASE_SCRIPT_URL, userID)
	alertcursor = conn.cursor()
	alertcursor.execute("INSERT INTO tAlerts (userID, alertType, alertTime, alertMessage, alertLink, alertStatus) VALUES ('{0}', 1, NOW(), '{1}', '{2}', 0);".format(userID, message, alertLink))
	alertcursor.close()

def getBaseProfs(galaxy):
	# Short-circuit returns on system galaxy IDs (NGE, Non-NGE, Jedi). Move on if neither.
	match str(galaxy):
		case '-1':
			return '-1, 1337'
		case '0':
			return '0, 1337'
		case '1337':
			return '-1, 0, 1337'
		case _:
			pass

	# Determine set of base profession galaxy IDs to include by checking if galaxy is flagged NGE
	baseProfs = '0, 1337'
	conn = ghConn()
	cursor = conn.cursor()
	if (cursor):
		cursor.execute('SELECT galaxyNGE FROM tGalaxy WHERE galaxyID={0};'.format(str(galaxy)))
		row = cursor.fetchone()
		if (row != None) and (row[0] > 0):
			baseProfs = '-1, 1337'
		cursor.close()
	conn.close()
	return baseProfs
