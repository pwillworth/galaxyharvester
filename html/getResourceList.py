#!/usr/bin/python
"""

 Copyright 2017 Paul Willworth <ioscode@gmail.com>

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
import cgi
import MySQLdb
import ghShared
import ghLists
import dbShared
import ghObjects

# Get list of resource types under a group that are not currently available
def getUnavailableTypes(resGroup):
	retTypes = ''
	conn = dbShared.ghConn()
	cursor = conn.cursor()
	if (cursor):
		sqlStr1 = 'SELECT tResourceType.resourceType, resourceTypeName, ur.maxent FROM tResourceType LEFT JOIN (SELECT tResources.resourceType AS resType, Max(entered) AS maxent FROM tResources INNER JOIN tResourceType rt ON tResources.resourceType = rt.resourceType WHERE unavailable IS NULL AND rt.resourceGroup="' + resGroup + '" GROUP BY tResources.resourceType) ur ON tResourceType.resourceType = ur.resType WHERE enterable = 1 AND resourceGroup="' + resGroup + '";'
		cursor.execute(sqlStr1)
		row = cursor.fetchone()
		while (row != None):
			if (row[2] == None):
				retTypes = retTypes + row[1] + '- '
			row = cursor.fetchone()

	return retTypes.rstrip('- ')

# Get list of group tree for resource type
def getTypeGroups(resType):
	retGroups = ['resources|Resources','','','','','','']
	conn = dbShared.ghConn()
	cursor = conn.cursor()
	if (cursor):
		sqlStr1 = 'SELECT groupLevel, groupName, tResourceTypeGroup.resourceGroup FROM tResourceTypeGroup INNER JOIN tResourceGroup ON tResourceTypeGroup.resourceGroup = tResourceGroup.resourceGroup WHERE tResourceTypeGroup.resourceType="' + resType + '";'
		cursor.execute(sqlStr1)
		row = cursor.fetchone()
		while (row != None):
			if (row[0] != None):
				retGroups[row[0]-1] = row[2] + '|' + row[1]
			row = cursor.fetchone()

	return retGroups

# Get current url
try:
	url = os.environ['SCRIPT_NAME']
except KeyError:
	url = ''

form = cgi.FieldStorage()
# Get Cookies
useCookies = 1
cookies = Cookie.SimpleCookie()
try:
	cookies.load(os.environ['HTTP_COOKIE'])
except KeyError:
	useCookies = 0

if useCookies:
	try:
		currentUser = cookies['userID'].value
	except KeyError:
		currentUser = ''
	try:
		loginResult = cookies['loginAttempt'].value
	except KeyError:
		loginResult = 'success'
	try:
		sid = cookies['gh_sid'].value
	except KeyError:
		sid = form.getfirst('gh_sid', '')
else:
	currentUser = ''
	loginResult = 'success'
	sid = form.getfirst('gh_sid', '')

galaxy = form.getfirst('galaxy', '')
unavailableDays = form.getfirst('unavailableDays', '')
planet = form.getfirst('planetSel', '')
planetName = form.getfirst('planetName', '')
resGroup = form.getfirst('resGroup', '')
resCategory = form.getfirst('resCategory', '')
resType = form.getfirst('resType', '')
sort = form.getfirst('sort', '')
favorite = form.getfirst('favorite', 'undefined')
formatType = form.getfirst('formatType', '')
# escape input to prevent sql injection
sid = dbShared.dbInsertSafe(sid)
galaxy = dbShared.dbInsertSafe(galaxy)
unavailableDays = dbShared.dbInsertSafe(unavailableDays)
planet = dbShared.dbInsertSafe(planet)
planetName = dbShared.dbInsertSafe(planetName)
resGroup = dbShared.dbInsertSafe(resGroup)
resCategory = dbShared.dbInsertSafe(resCategory)
resType = dbShared.dbInsertSafe(resType)
sort = dbShared.dbInsertSafe(sort)
favorite = dbShared.dbInsertSafe(favorite)

# Get a session
logged_state = 0
linkappend = ''

sess = dbSession.getSession(sid, 2592000)
if (sess != ''):
	logged_state = 1
	currentUser = sess
	if (useCookies == 0):
		linkappend = 'gh_sid=' + sid

joinStr = ""
criteriaStr = "unavailable IS NULL"
unPlanetStr = ",'all'"
orderStr = ""
groupType = 1
formatStyle = 0
resBoxMargin = "4px"
galaxyState = 0
errorStr = ""

if galaxy == "":
	errorStr = "No Galaxy Specified"
else:
	galaxyState = dbShared.galaxyState(galaxy)

if (resGroup != "any" and resGroup != ""):
	joinStr = joinStr + " INNER JOIN (SELECT resourceType FROM tResourceTypeGroup WHERE resourceGroup='" + resGroup + "' GROUP BY resourceType) rtgg ON rt1.resourceType = rtgg.resourceType"
if (resCategory != "any" and resCategory != ""):
	joinStr = joinStr + " INNER JOIN (SELECT resourceType FROM tResourceTypeGroup WHERE resourceGroup='" + resCategory + "' GROUP BY resourceType) rtgc ON rt1.resourceType = rtgc.resourceType"

if (unavailableDays != None and unavailableDays.isdigit()):
	if (unavailableDays == "0"):
		criteriaStr = "tResources.galaxy=" + galaxy + " AND unavailable IS NULL"
	else:
		if (resType != "any" and resType != "") or (resGroup != "any" and resGroup != ""):
			criteriaStr = "tResources.galaxy=" + galaxy + " AND (unavailable IS NULL OR DATEDIFF(NOW(),unavailable) <= " + unavailableDays + ")"
		else:
			errorStr = "You must select a resource type or group when searching for unavailable resources."
else:
	criteriaStr = "tResources.galaxy=" + galaxy + " AND unavailable IS NULL"

if (planet == "" and planetName != ""):
	planet = dbShared.getPlanetID(planetName)
if (planet != "any" and planet !="null" and planet != ""):
	unPlanetStr = ",'"+planet+"'"
	criteriaStr = criteriaStr + " AND EXISTS (SELECT planetID FROM tResourcePlanet WHERE spawnID = tResources.spawnID AND planetID=" + planet + " AND unavailable IS NULL)"

if (resType != "any" and resType != ""):
	criteriaStr = criteriaStr + " AND tResources.resourceType='" + resType + "'"

if logged_state == 1:
	#for later when nonpublic waypoints in
	#wpCriteria = 'shareLevel=256 OR owner="' + currentUser + '" OR (shareLevel=64 AND owner IN (SELECT f1.friendID FROM tUserFriends f1 INNER JOIN tUserFriends f2 ON f1.userID=f2.friendID WHERE f1.userID="' + currentUser + '")) OR waypointID IN (SELECT uw.waypointID FROM tUserWaypoints uw WHERE unlocked IS NOT NULL AND uw.userID="' + currentUser + '")'
	wpCriteria = 'shareLevel=256'
	if favorite == "on":
		joinStr = joinStr + " INNER JOIN (SELECT itemID, favGroup FROM tFavorites WHERE userID='" + currentUser + "' AND favType=1) favs ON tResources.spawnID = favs.itemID"
	else:
		joinStr = joinStr + ' LEFT JOIN (SELECT itemID, favGroup FROM tFavorites WHERE userID="' + currentUser + '" AND favType=1) favs ON tResources.spawnID = favs.itemID'
	favCols = ', favGroup'
else:
	wpCriteria = 'shareLevel=256'
	favCols = ', NULL'


if sort[:4] == "time":
	if sort == "timeEntered":
		orderStr = " ORDER BY entered DESC"
	elif sort == "timeVerified":
		orderStr = " ORDER BY verified DESC"
	elif sort == "timeUnavailable":
		orderStr = " ORDER BY unavailable DESC"
elif sort[:4] == "stat":
	if sort[4:] == "avg":
		orderStr = " ORDER BY (CASE WHEN CRmax > 0 THEN CR ELSE 0 END + CASE WHEN CDmax > 0 THEN CD ELSE 0 END + CASE WHEN DRmax > 0 THEN DR ELSE 0 END + CASE WHEN FLmax > 0 THEN FL ELSE 0 END + CASE WHEN HRmax > 0 THEN HR ELSE 0 END + CASE WHEN MAmax > 0 THEN MA ELSE 0 END + CASE WHEN PEmax > 0 THEN PE ELSE 0 END + CASE WHEN OQmax > 0 THEN OQ ELSE 0 END + CASE WHEN SRmax > 0 THEN SR ELSE 0 END + CASE WHEN UTmax > 0 THEN UT ELSE 0 END + CASE WHEN ERmax > 0 THEN ER ELSE 0 END)"
		orderStr += " / (CASE WHEN CRmax > 0 THEN 1 ELSE 0 END + CASE WHEN CDmax > 0 THEN 1 ELSE 0 END + CASE WHEN DRmax > 0 THEN 1 ELSE 0 END + CASE WHEN FLmax > 0 THEN 1 ELSE 0 END + CASE WHEN HRmax > 0 THEN 1 ELSE 0 END + CASE WHEN MAmax > 0 THEN 1 ELSE 0 END + CASE WHEN PEmax > 0 THEN 1 ELSE 0 END + CASE WHEN OQmax > 0 THEN 2 ELSE 0 END + CASE WHEN SRmax > 0 THEN 1 ELSE 0 END + CASE WHEN UTmax > 0 THEN 1 ELSE 0 END + CASE WHEN ERmax > 0 THEN 1 ELSE 0 END) DESC"
	elif sort[4:] == "avgp":
		orderStr = " ORDER BY (CASE WHEN CRmax > 0 THEN ((CR-CRmin) / (CRmax-CRmin))*100 ELSE 0 END + CASE WHEN CDmax > 0 THEN ((CD-CDmin) / (CDmax-CDmin))*100 ELSE 0 END + CASE WHEN DRmax > 0 THEN ((DR-DRmin) / (DRmax-DRmin))*100 ELSE 0 END + CASE WHEN FLmax > 0 THEN ((FL-FLmin) / (FLmax-FLmin))*100 ELSE 0 END + CASE WHEN HRmax > 0 THEN ((HR-HRmin) / (HRmax-HRmin))*100 ELSE 0 END + CASE WHEN MAmax > 0 THEN ((MA-MAmin) / (MAmax-MAmin))*100 ELSE 0 END + CASE WHEN PEmax > 0 THEN ((PE-PEmin) / (PEmax-PEmin))*100 ELSE 0 END + CASE WHEN OQmax > 0 THEN ((OQ-OQmin) / (OQmax-OQmin))*200 ELSE 0 END + CASE WHEN SRmax > 0 THEN ((SR-SRmin) / (SRmax-SRmin))*100 ELSE 0 END + CASE WHEN UTmax > 0 THEN ((UT-UTmin) / (UTmax-UTmin))*100 ELSE 0 END + CASE WHEN ERmax > 0 THEN ((ER-ERmin) / (ERmax-ERmin))*100 ELSE 0 END)"
		orderStr += " / (CASE WHEN CRmax > 0 THEN 1 ELSE 0 END + CASE WHEN CDmax > 0 THEN 1 ELSE 0 END + CASE WHEN DRmax > 0 THEN 1 ELSE 0 END + CASE WHEN FLmax > 0 THEN 1 ELSE 0 END + CASE WHEN HRmax > 0 THEN 1 ELSE 0 END + CASE WHEN MAmax > 0 THEN 1 ELSE 0 END + CASE WHEN PEmax > 0 THEN 1 ELSE 0 END + CASE WHEN OQmax > 0 THEN 2 ELSE 0 END + CASE WHEN SRmax > 0 THEN 1 ELSE 0 END + CASE WHEN UTmax > 0 THEN 1 ELSE 0 END + CASE WHEN ERmax > 0 THEN 1 ELSE 0 END) DESC"
	else:
		if sort[4:] in ['CR','CD','DR','FL','HR','MA','PE','OQ','SR','UT','ER']:
			orderStr = " ORDER BY " + sort[4:] + " DESC"
elif sort[:4] == "tree":
	groupType = 2
	resBoxMargin = "16px"
	orderStr = " ORDER BY rg2.groupOrder, rg1.groupOrder, rt1.resourceTypeName"
	formatStyle = 2
else:
	groupType = 0
	resBoxMargin = "40px"
	orderStr = " ORDER BY rg2.groupOrder, rg1.groupOrder, rt1.resourceTypeName"

# Main program
s = None
currentGroup = ''
currentType = ''
currentLevel = 0
currentGroups = ['resources|Resources','','','','','','']
typeGroups = ['resources|Resources','','','','','','']


print 'Content-type: text/html\n'
if (errorStr == ""):
	conn = dbShared.ghConn()
	# Only show update tools if user logged in and has positive reputation
	stats = dbShared.getUserStats(currentUser, galaxy).split(",")
	userReputation = int(stats[2])

	cursor = conn.cursor()
	if (cursor):
		sqlStr1 = 'SELECT spawnID, spawnName, tResources.galaxy, entered, enteredBy, tResources.resourceType, rt1.resourceTypeName, rt1.resourceGroup,'
		sqlStr1 += ' CR, CD, DR, FL, HR, MA, PE, OQ, SR, UT, ER,'
		sqlStr1 += ' CASE WHEN rt1.CRmax > 0 THEN ((CR-rt1.CRmin) / (rt1.CRmax-rt1.CRmin))*100 ELSE NULL END AS CRperc,'
		sqlStr1 += ' CASE WHEN rt1.CDmax > 0 THEN ((CD-rt1.CDmin) / (rt1.CDmax-rt1.CDmin))*100 ELSE NULL END AS CDperc,'
		sqlStr1 += ' CASE WHEN rt1.DRmax > 0 THEN ((DR-rt1.DRmin) / (rt1.DRmax-rt1.DRmin))*100 ELSE NULL END AS DRperc,'
		sqlStr1 += ' CASE WHEN rt1.FLmax > 0 THEN ((FL-rt1.FLmin) / (rt1.FLmax-rt1.FLmin))*100 ELSE NULL END AS FLperc,'
		sqlStr1 += ' CASE WHEN rt1.HRmax > 0 THEN ((HR-rt1.HRmin) / (rt1.HRmax-rt1.HRmin))*100 ELSE NULL END AS HRperc,'
		sqlStr1 += ' CASE WHEN rt1.MAmax > 0 THEN ((MA-rt1.MAmin) / (rt1.MAmax-rt1.MAmin))*100 ELSE NULL END AS MAperc,'
		sqlStr1 += ' CASE WHEN rt1.PEmax > 0 THEN ((PE-rt1.PEmin) / (rt1.PEmax-rt1.PEmin))*100 ELSE NULL END AS PEperc,'
		sqlStr1 += ' CASE WHEN rt1.OQmax > 0 THEN ((OQ-rt1.OQmin) / (rt1.OQmax-rt1.OQmin))*100 ELSE NULL END AS OQperc,'
		sqlStr1 += ' CASE WHEN rt1.SRmax > 0 THEN ((SR-rt1.SRmin) / (rt1.SRmax-rt1.SRmin))*100 ELSE NULL END AS SRperc,'
		sqlStr1 += ' CASE WHEN rt1.UTmax > 0 THEN ((UT-rt1.UTmin) / (rt1.UTmax-rt1.UTmin))*100 ELSE NULL END AS UTperc,'
		sqlStr1 += ' CASE WHEN rt1.ERmax > 0 THEN ((ER-rt1.ERmin) / (rt1.ERmax-rt1.ERmin))*100 ELSE NULL END AS ERperc,'
		sqlStr1 += ' rt1.containerType, verified, verifiedBy, unavailable, unavailableBy, rg1.groupName, rt1.resourceCategory, rg2.groupName AS categoryName, rt1.resourceGroup, (SELECT Max(concentration) FROM tWaypoint WHERE tWaypoint.spawnID=tResources.spawnID AND (' + wpCriteria + ')) AS wpMaxConc' + favCols + ' FROM tResources INNER JOIN tResourceType rt1 ON tResources.resourceType = rt1.resourceType INNER JOIN tResourceGroup rg1 ON rt1.resourceGroup = rg1.resourceGroup INNER JOIN tResourceGroup rg2 ON rt1.resourceCategory = rg2.resourceGroup' + joinStr + ' WHERE ' + criteriaStr
		sqlStr1 = sqlStr1 + orderStr + ';'
		#sys.stderr.write(sqlStr1)
		cursor.execute(sqlStr1)
		row = cursor.fetchone()
		while (row != None):
			# group by resource group
			if groupType == 0:
				if (currentGroup != row[35]):
					# only print unavailable resource types if listing all available resources
					if (criteriaStr == "unavailable IS NULL"):
						missingStr = getUnavailableTypes(row[38])
						if len(missingStr) > 0:
							missingStr = missingStr.replace(row[35]+'s','')
							missingStr = missingStr.replace(row[35], '')
							missingStr = ' ( Unavailable Types: ' + missingStr + ')'
						else:
							missingStr = ' ( All types available )'
					else:
						missingStr = ''
					# print group header and start table
					if currentGroup != '':
						print '</table>'
					print '<h3 style="margin-left:20px;"><a href="' + ghShared.BASE_SCRIPT_URL + 'resourceType.py/' + row[38] + '" title="View schematics and recent spawns of this type" class="nameLink">' + row[35] + '</a><span style="font-weight:normal;font-size:.9em;opacity:0.8;"> ' + missingStr + '</span></h3>'
					print '<table id="tbl_' + row[38] + '" width="100%" class="resourceStats">'
					currentGroup = row[35]
			# group by full tree of groups
 			elif groupType == 2:
				if s == None:
					print '<table width="100%">'
				typeGroups = getTypeGroups(row[5])
				for i in range(7):
					#sys.stderr.write(typeGroups[i] + '\n')
					if typeGroups[i] != '':
						currentLevel = i+1
					if currentGroups[i] != typeGroups[i]:
						print '<tr><td><div class="surveyGroup" style="margin-left:' + str(i * 16) + 'px;"><a href="' + ghShared.BASE_SCRIPT_URL + 'resourceType.py/' + typeGroups[i][:typeGroups[i].find('|')] + '" title="View schematics and recent spawns of this type" class="nameLink" style="color:#999999;">' + typeGroups[i][typeGroups[i].find('|')+1:] + '</a></div></td></tr>'
				currentGroups = typeGroups
				if currentType != row[5]:
					print '<tr><td><div class="surveyGroup" style="margin-left:' + str(currentLevel * 16) + 'px;"><a href="' + ghShared.BASE_SCRIPT_URL + 'resourceType.py/' + row[5] + '" title="View schematics and recent spawns of this type" class="nameLink" style="color:#999999;">' + row[6] + '</a></div></td></tr>'
					currentType = row[5]
				resBoxMargin = str((currentLevel+2) * 16) + 'px'
			# no grouping for others
			else:
				if s == None:
					print '<table width="100%" class=resourceStats>'


			# populate this resource to object and print it
			s = ghObjects.resourceSpawn()
			s.spawnID = row[0]
			s.spawnName = row[1]
			s.spawnGalaxy = row[2]
			s.resourceType = row[5]
			s.resourceTypeName = row[6]
			s.containerType = row[30]
			s.stats.CR = row[8]
			s.stats.CD = row[9]
			s.stats.DR = row[10]
			s.stats.FL = row[11]
			s.stats.HR = row[12]
			s.stats.MA = row[13]
			s.stats.PE = row[14]
			s.stats.OQ = row[15]
			s.stats.SR = row[16]
			s.stats.UT = row[17]
			s.stats.ER = row[18]

			s.percentStats.CR = row[19]
			s.percentStats.CD = row[20]
			s.percentStats.DR = row[21]
			s.percentStats.FL = row[22]
			s.percentStats.HR = row[23]
			s.percentStats.MA = row[24]
			s.percentStats.PE = row[25]
			s.percentStats.OQ = row[26]
			s.percentStats.SR = row[27]
			s.percentStats.UT = row[28]
			s.percentStats.ER = row[29]

			s.entered = row[3]
			s.enteredBy = row[4]
			s.verified = row[31]
			s.verifiedBy = row[32]
			s.unavailable = row[33]
			s.unavailableBy = row[34]
			s.maxWaypointConc = row[39]
			if row[40] != None:
				s.favorite = 1
			s.planets = dbShared.getSpawnPlanets(conn, row[0], True, row[2])

			print '  <tr><td>'

			if logged_state > 0 and galaxyState == 1:
				controlsUser = currentUser
			else:
				controlsUser = ''

			if formatType == 'mobile':
				print s.getMobileHTML(controlsUser, int(stats[2]))
			else:
				print s.getHTML(formatStyle, resBoxMargin, controlsUser, userReputation)

			print '</td></tr>'
			row = cursor.fetchone()

		cursor.close()
	conn.close()
	print '  </table>'

else:
	print '<h2>' + errorStr + '</h2>'
