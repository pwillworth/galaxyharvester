#!/usr/bin/python
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
import Cookie
import dbSession
import cgi
import MySQLdb
import time
from datetime import timedelta, datetime
import ghLists
import dbShared
import ghObjects

RES_STATS = ['ER','CR','CD','DR','FL','HR','MA','PE','OQ','SR','UT']

def getResourceSQL(wpCriteria, favCols, joinStr, orderCol, orderStr, criteriaStr, galaxyCriteriaStr, mine):
	if mine != '':
		criteriaStr += ' AND favGroup IS NOT NULL'
	sqlStr1 = 'SELECT tResources.spawnID, spawnName, tResources.galaxy, tResources.entered, tResources.enteredBy, tResources.resourceType, rt1.resourceTypeName, rt1.resourceGroup,'
	sqlStr1 += ' CR, CD, DR, FL, HR, MA, PE, OQ, SR, UT, ER,'
	sqlStr1 += ' CASE WHEN rt1.CRmax > 0 THEN ((CR-rt1.CRmin) / (rt1.CRmax-rt1.CRmin))*100 ELSE NULL END AS CRperc, CASE WHEN rt1.CDmax > 0 THEN ((CD-rt1.CDmin) / (rt1.CDmax-rt1.CDmin))*100 ELSE NULL END AS CDperc, CASE WHEN rt1.DRmax > 0 THEN ((DR-rt1.DRmin) / (rt1.DRmax-rt1.DRmin))*100 ELSE NULL END AS DRperc, CASE WHEN rt1.FLmax > 0 THEN ((FL-rt1.FLmin) / (rt1.FLmax-rt1.FLmin))*100 ELSE NULL END AS FLperc, CASE WHEN rt1.HRmax > 0 THEN ((HR-rt1.HRmin) / (rt1.HRmax-rt1.HRmin))*100 ELSE NULL END AS HRperc, CASE WHEN rt1.MAmax > 0 THEN ((MA-rt1.MAmin) / (rt1.MAmax-rt1.MAmin))*100 ELSE NULL END AS MAperc,'
	sqlStr1 += ' CASE WHEN rt1.PEmax > 0 THEN ((PE-rt1.PEmin) / (rt1.PEmax-rt1.PEmin))*100 ELSE NULL END AS PEperc, CASE WHEN rt1.OQmax > 0 THEN ((OQ-rt1.OQmin) / (rt1.OQmax-rt1.OQmin))*100 ELSE NULL END AS OQperc, CASE WHEN rt1.SRmax > 0 THEN ((SR-rt1.SRmin) / (rt1.SRmax-rt1.SRmin))*100 ELSE NULL END AS SRperc, CASE WHEN rt1.UTmax > 0 THEN ((UT-rt1.UTmin) / (rt1.UTmax-rt1.UTmin))*100 ELSE NULL END AS UTperc, CASE WHEN rt1.ERmax > 0 THEN ((ER-rt1.ERmin) / (rt1.ERmax-rt1.ERmin))*100 ELSE NULL END AS ERperc,'
	sqlStr1 += ' rt1.containerType, tResources.verified, tResources.verifiedBy, tResources.unavailable, tResources.unavailableBy, rg1.groupName, rt1.resourceCategory, rg2.groupName AS categoryName, rt1.resourceGroup, (SELECT Max(concentration) FROM tWaypoint WHERE tWaypoint.spawnID=tResources.spawnID AND tWaypoint.unavailable IS NULL AND (' + wpCriteria + ')) AS wpMaxConc' + favCols + ', ' + orderCol + ' FROM tResources INNER JOIN tResourceType rt1 ON tResources.resourceType = rt1.resourceType INNER JOIN tResourceGroup rg1 ON rt1.resourceGroup = rg1.resourceGroup INNER JOIN tResourceGroup rg2 ON rt1.resourceCategory = rg2.resourceGroup' + joinStr + ' WHERE ' + criteriaStr + galaxyCriteriaStr
	sqlStr1 += orderStr
	if fetchSize.isdigit():
		sqlStr1 += ' LIMIT ' + fetchSize
	sqlStr1 += ';'

	return sqlStr1

def getResourceCountSQL(wpCriteria, favCols, joinStr, orderCol, orderStr, criteriaStr, galaxyCriteriaStr, mine):
	if mine != '':
		criteriaStr += ' AND favGroup IS NOT NULL'
	sqlStr1 = 'SELECT Count(*)'
	sqlStr1 += ' FROM tResources INNER JOIN tResourceType rt1 ON tResources.resourceType = rt1.resourceType INNER JOIN tResourceGroup rg1 ON rt1.resourceGroup = rg1.resourceGroup INNER JOIN tResourceGroup rg2 ON rt1.resourceCategory = rg2.resourceGroup'
	sqlStr1 += joinStr + ' WHERE ' + criteriaStr + galaxyCriteriaStr + ';'

	return sqlStr1

def getResourceData(conn, resSQL, userReputation, activeUser, formatType):
	# get resource data for given criteria
	resourceHTML = ''
	s = None

	cursor = conn.cursor()
	if (cursor):
		lastValue = None
		cursor.execute(resSQL)
		row = cursor.fetchone()
		if row == None:
			resourceHTML = 'No resources found!'
		while (row != None):
			if s == None:
				if formatType == 'json':
					resourceHTML = '  [\n'
				else:
					resourceHTML = '<table width="100%" class=resourceStats>'

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
				s.despawnAlert = row[41]
			if row[42] != None:
				s.units = row[42]
			if sort == "quality":
				s.overallScore = row[43]
			s.planets = dbShared.getSpawnPlanets(conn, row[0], False, row[2])

			if formatType == 'json':
				resourceHTML += '    {'
			else:
				resourceHTML += '  <tr><td>'

			if formatType == 'mobile':
				resourceHTML += s.getMobileHTML(activeUser, userReputation, dbShared.getUserAdmin(conn, currentUser, galaxy))
			elif formatType == 'compare':
				resourceHTML += s.getHTML(1, '', activeUser, userReputation, dbShared.getUserAdmin(conn, currentUser, galaxy))
			elif formatType == 'json':
				resourceHTML += s.getJSON()
			else:
				resourceHTML += s.getHTML(0, '', activeUser, userReputation, dbShared.getUserAdmin(conn, currentUser, galaxy))

			if formatType == 'json':
				resourceHTML += '    }'
			else:
				resourceHTML += '</td></tr>'

			lastValue = row[43]

			row = cursor.fetchone()

			if formatType == 'json':
				resourceHTML += '  ,\n'
			else:
				resourceHTML += '  </table>'

		if fetchSize.isdigit() and cursor.rowcount == int(fetchSize):
			if formatType == 'json':
				resourceHTML += '],\n  "last_value" : ' + str(lastValue)
			else:
				resourceHTML += '<div style="display:none;">maxRowsReached' + str(lastValue) + '</div>'

		cursor.close()
	return resourceHTML

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
planet = form.getfirst('planetSel', '')
planetName = form.getfirst('planetName', '')
resGroup = form.getfirst('resGroup', '')
resCategory = form.getfirst('resCategory', '')
resType = form.getfirst('resType', '')
sort = form.getfirst('sort', '')
formatType = form.getfirst('formatType', '')
userBy = form.getfirst('userBy', '')
userAction = form.getfirst('userAction', '')
minVals = form.getfirst('minVals', '')
maxVals = form.getfirst('maxVals', '')
percVals = form.getfirst('percVals', '')
available = form.getfirst('available', '')
verified = form.getfirst('verified', '')
lastValue = form.getfirst('lastValue', '')
compare = form.getfirst('compare', '')
favorite = form.getfirst('favorite', 'undefined')
fetchSize = form.getfirst('fetchSize', '20')
# escape input to prevent sql injection
sid = dbShared.dbInsertSafe(sid)
galaxy = dbShared.dbInsertSafe(galaxy)
planet = dbShared.dbInsertSafe(planet)
planetName = dbShared.dbInsertSafe(planetName)
resGroup = dbShared.dbInsertSafe(resGroup)
resCategory = dbShared.dbInsertSafe(resCategory)
resType = dbShared.dbInsertSafe(resType)
sort = dbShared.dbInsertSafe(sort)
userBy = dbShared.dbInsertSafe(userBy)
userAction = dbShared.dbInsertSafe(userAction)
minVals = dbShared.dbInsertSafe(minVals)
maxVals = dbShared.dbInsertSafe(maxVals)
percVals = dbShared.dbInsertSafe(percVals)
lastValue = dbShared.dbInsertSafe(lastValue)
favorite = dbShared.dbInsertSafe(favorite)

# Get a session
logged_state = 0
linkappend = ''

sess = dbSession.getSession(sid)
if (sess != ''):
	logged_state = 1
	currentUser = sess
	if (useCookies == 0):
		linkappend = 'gh_sid=' + sid

joinStr = ""
criteriaStr = ""
galaxyCriteriaStr = ""
orderCol = "spawnID"
orderStr = " ORDER BY " + orderCol + " DESC"
groupType = 1
galaxyState = 0
errorStr = ""
percVals = percVals.replace("%","")

if galaxy == "":
	errorStr = "Error: No Galaxy Specified"
else:
	galaxyState = dbShared.galaxyState(galaxy)

if (resGroup != "any" and resGroup != ""):
	joinStr = joinStr + " INNER JOIN (SELECT resourceType FROM tResourceTypeGroup WHERE resourceGroup='" + resGroup + "' GROUP BY resourceType) rtgg ON rt1.resourceType = rtgg.resourceType"
if (resCategory != "any" and resCategory != ""):
	joinStr = joinStr + " INNER JOIN (SELECT resourceType FROM tResourceTypeGroup WHERE resourceGroup='" + resCategory + "' GROUP BY resourceType) rtgc ON rt1.resourceType = rtgc.resourceType"

criteriaStr = "tResources.galaxy=" + galaxy

if (planet == "" and planetName != ""):
	planet = dbShared.getPlanetID(planetName)
if (planet != "any" and planet != "" and planet != "0"):
	joinStr = joinStr + " INNER JOIN tResourcePlanet ON tResources.spawnID = tResourcePlanet.spawnID"
	criteriaStr += " AND planetID=" + planet

if (resType != "any" and resType != ""):
	criteriaStr = criteriaStr + " AND tResources.resourceType='" + resType + "'"

if logged_state == 1:
	#for later when nonpublic waypoints in
	#wpCriteria = 'shareLevel=256 OR owner="' + currentUser + '" OR (shareLevel=64 AND owner IN (SELECT f1.friendID FROM tUserFriends f1 INNER JOIN tUserFriends f2 ON f1.userID=f2.friendID WHERE f1.userID="' + currentUser + '")) OR waypointID IN (SELECT uw.waypointID FROM tUserWaypoints uw WHERE unlocked IS NOT NULL AND uw.userID="' + currentUser + '")'
	wpCriteria = 'shareLevel=256'
	if favorite == "on":
		joinStr = joinStr + " INNER JOIN (SELECT itemID, favGroup, despawnAlert, units FROM tFavorites WHERE userID='" + currentUser + "' AND favType=1) favs ON tResources.spawnID = favs.itemID"
	else:
		joinStr = joinStr + ' LEFT JOIN (SELECT itemID, favGroup, despawnAlert, units FROM tFavorites WHERE userID="' + currentUser + '" AND favType=1) favs ON tResources.spawnID = favs.itemID'
	favCols = ', favGroup, despawnAlert, units'
else:
	wpCriteria = 'shareLevel=256'
	favCols = ', NULL, NULL, NULL'

if (userBy != '' and userAction != ''):
	galaxyCriteriaStr += (" AND {0}By='{1}'").format(userAction, userBy)

if available != 'undefined' and available != '':
	galaxyCriteriaStr += ' AND tResources.unavailable IS NULL'
else:
	if not fetchSize.isdigit() or len(fetchSize) > 2:
		errorStr = "Error: Invalid fetch size when including unavailable resources."

if verified != 'undefined' and verified != '':
	galaxyCriteriaStr += ' AND tResources.verified IS NOT NULL'

mins = minVals.split(",")
if len(mins) == len(RES_STATS):
	for i in range(len(mins)):
		if mins[i].isdigit():
			criteriaStr = criteriaStr + " AND " + RES_STATS[i] + " >= " + str(mins[i])

maxs = maxVals.split(",")
if len(maxs) == len(RES_STATS):
	for i in range(len(maxs)):
		if maxs[i].isdigit():
			criteriaStr = criteriaStr + " AND " + RES_STATS[i] + " <= " + str(maxs[i])

if sort == "time":
	orderCol = "UNIX_TIMESTAMP(tResources.entered)"
	orderStr = " ORDER BY {0} DESC".format(orderCol)
if sort == "quality":
	weightStr = ""
	weights = percVals.split(",")
	if len(RES_STATS) == len(weights):
		for i in range(len(weights)):
			if weights[i].isdigit():
				weightStr = weightStr + ("+CASE WHEN {0}max > 0 THEN {0}*(" + str(weights[i]) + "/100) ELSE 0 END").format(RES_STATS[i])

		if weightStr == "":
			weightStr += ' ((CASE WHEN CRmax > 0 THEN CR*.06 ELSE 0 END + CASE WHEN CDmax > 0 THEN CD*12.74 ELSE 0 END + CASE WHEN DRmax > 0 THEN DR*12.26 ELSE 0 END + CASE WHEN FLmax > 0 THEN FL*3.22 ELSE 0 END + CASE WHEN HRmax > 0 THEN HR*1.27 ELSE 0 END + CASE WHEN MAmax > 0 THEN MA*5.1 ELSE 0 END + CASE WHEN PEmax > 0 THEN PE*9.34 ELSE 0 END + CASE WHEN OQmax > 0 THEN OQ*30.64 ELSE 0 END + CASE WHEN SRmax > 0 THEN SR*9.16 ELSE 0 END + CASE WHEN UTmax > 0 THEN UT*16.2 ELSE 0 END)'
			weightStr += ' / (CASE WHEN CRmax > 0 THEN .06 ELSE 0 END + CASE WHEN CDmax > 0 THEN 12.74 ELSE 0 END + CASE WHEN DRmax > 0 THEN 12.26 ELSE 0 END + CASE WHEN FLmax > 0 THEN 3.22 ELSE 0 END + CASE WHEN HRmax > 0 THEN 1.27 ELSE 0 END + CASE WHEN MAmax > 0 THEN 5.1 ELSE 0 END + CASE WHEN PEmax > 0 THEN 9.34 ELSE 0 END + CASE WHEN OQmax > 0 THEN 30.64 ELSE 0 END + CASE WHEN SRmax > 0 THEN 9.16 ELSE 0 END + CASE WHEN UTmax > 0 THEN 16.2 ELSE 0 END))'
		else:
			weightStr = weightStr[1:]

		orderCol = weightStr
		orderStr = " ORDER BY {0} DESC".format(orderCol)
if sort == "type":
	orderCol = "tResources.resourceType"
	orderStr = " ORDER BY {0} ASC".format(orderCol)
if sort == "group":
	orderCol = "rt1.resourceGroup"
	orderStr = " ORDER BY {0} ASC".format(orderCol)

if lastValue != "":
	criteriaStr = criteriaStr + (" AND {0} < {1}").format(orderCol,lastValue)

# Only show update tools if user logged in and has positive reputation
stats = dbShared.getUserStats(currentUser, galaxy).split(",")
userReputation = int(stats[2])

if formatType == 'json':
	print 'Content-type: text/json\n'
else:
	print 'Content-type: text/html\n'

if (errorStr == ""):
	resData = ''
	tokenPosition = -1
	conn = dbShared.ghConn()
	if logged_state > 0 and galaxyState == 1:
		activeUser = currentUser
	else:
		activeUser = ''
	if (compare == '' or compare == 'undefined' or logged_state == 0):
		resSQL = getResourceSQL(wpCriteria, favCols, joinStr, orderCol, orderStr, criteriaStr, galaxyCriteriaStr, '')
		resData = getResourceData(conn, resSQL, userReputation, activeUser, formatType)
		tokenPosition = resData.find('maxRowsReached')
		if tokenPosition > -1:
			resData += '<div style="text-align:center;"><button id="nextResourcesButton" class="ghButton" style="margin:10px;" onclick="moreResources(\''+ resData[tokenPosition+14:resData.find('</div>', tokenPosition)] + '\', \'next\');">Next 20</button></div>'
	else:
		# Include side by side comparison of inventory
		formatType = 'compare'
		resData = '<div class="resourceCompareGroup">'
		resData += '<div class="inlineBlock" style="width:50%">'
		resData += '<h4>Galaxy</h4>'
		resSQL = getResourceSQL(wpCriteria, favCols, joinStr, orderCol, orderStr, criteriaStr, galaxyCriteriaStr, '')
		resData += getResourceData(conn, resSQL, userReputation, activeUser, formatType)
		resData += '</div><div class="inlineBlock" style="width:50%">'
		resData += '<h4>My Inventory</h4>'
		resSQL = getResourceSQL(wpCriteria, favCols, joinStr, orderCol, orderStr, criteriaStr, '', 'y')
		resData += getResourceData(conn, resSQL, userReputation, activeUser, formatType)
		resData += '</div></div>'
		tokenPosition = resData.find('maxRowsReached')
		if tokenPosition > -1:
			resData += '<div style="text-align:center;"><button id="nextResourcesButton" class="ghButton" style="margin:10px;" onclick="moreResources(\''+ resData[tokenPosition+14:resData.find('</div>', tokenPosition)] + '\', \'next\');">Next 20</button></div>'

	# Include total results info for json service
	if formatType == 'json':
		responseData = '{\n'
		resCountSQL = getResourceCountSQL(wpCriteria, favCols, joinStr, orderCol, orderStr, criteriaStr, galaxyCriteriaStr, '')
		cursor = conn.cursor()
		if (cursor):
			cursor.execute(resCountSQL)
			row = cursor.fetchone()
			if row == None or row[0] == 0:
				responseData += '"response" :\n { "total_results" : 0,\n "total_pages" : 0,\n'
				resData = '"' + resData + '"'
			else:
				if fetchSize.isdigit():
					responseData += '"response" :\n { "total_results" : ' + str(row[0]) + ',\n "total_pages" : ' + str("%.0f" % (float((row[0] / int(fetchSize)) + 1))) + ',\n'
				else:
					responseData += '"response" :\n { "total_results" : ' + str(row[0]) + ',\n "total_pages" : 1,\n'
			cursor.close()
			responseData += ' "server_time" : "' + datetime.fromtimestamp(time.time()).strftime("%Y-%m-%d %H:%M:%S") + '",\n'
		print responseData + ' "resources" : '
		resData += '\n  }\n}'

	conn.close()
	print resData
	sys.exit(200)
else:
	if formatType == 'json':
		print '{ "response" : "' + errorStr + '" }'
	else:
		print '<h2>' + errorStr + '</h2>'
	sys.exit(500)
