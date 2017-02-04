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
import dbShared
import cgi
import MySQLdb
import ghLists
import ghObjects
#
def getProfOrder(profID):
	stats = {}
	weightTotal = 0
	tmpGroup = ''
	obyStr = ''
	obyStr2 = ''
	#maxCheckStr = ''
	if profID.isdigit():
		expCursor = conn.cursor()
		expCursor.execute('SELECT "holdername", statName, Sum(statWeight) AS sw, Sum(weightTotal) AS wt FROM tSchematicQualities INNER JOIN tSchematicResWeights ON tSchematicQualities.expQualityID = tSchematicResWeights.expQualityID INNER JOIN tSchematic ON tSchematicQualities.schematicID = tSchematic.schematicID INNER JOIN tSkillGroup ON tSchematic.skillGroup = tSkillGroup.skillGroup WHERE profID=' + prof + ' GROUP BY statName;')
		expRow = expCursor.fetchone()
		while (expRow != None):
			if expRow[0] != tmpGroup:
				weightTotal += int(expRow[3])
				tmpGroup = int(expRow[3])
			if expRow[1] in stats:
				stats[expRow[1]] = stats[expRow[1]] + int(expRow[2])
			else:
				stats[expRow[1]] = int(expRow[2])
			expRow = expCursor.fetchone()

		expCursor.close()
		# calculate column sort by based on quality weights((CR-CRmin) / (CRmax-CRmin))
		for k, v in stats.iteritems():
			weightVal = '%.2f' % (v*1.0 / weightTotal * 200)
			obyStr = obyStr + '+CASE WHEN ' + k + 'max > 0 THEN ((' + k + '-' + k + 'min) / (' + k + 'max-' + k + 'min))* ' + weightVal + ' ELSE 0 END'
			obyStr2 = obyStr2 + '+CASE WHEN ' + k + 'max > 0 THEN ' + weightVal + ' ELSE 0 END'

		if len(obyStr)>1:
			obyStr = obyStr[1:]
		if len(obyStr2)>1:
			obyStr2 = obyStr2[1:]

		return ' ((' + obyStr + ')*1000) / (' + obyStr2 + ')'
	else:
		return 'OQ'
#
def getTypeOrder(tabID, typeID):
	stats = {}
	weightTotal = 0
	tmpGroup = ''
	obyStr = ''
	obyStr2 = ''
	if tabID.isdigit():
		sqlStr = 'SELECT "holdername", statName, Sum(statWeight) AS sw, Sum(weightTotal) AS wt FROM tSchematicQualities INNER JOIN tSchematicResWeights ON tSchematicQualities.expQualityID = tSchematicResWeights.expQualityID INNER JOIN tSchematic ON tSchematicQualities.schematicID = tSchematic.schematicID WHERE craftingTab=' + tabID
		if typeID.isdigit():
			sqlStr = sqlStr + ' AND objectType=' + typeID
		sqlStr = sqlStr + ' GROUP BY statName;'
		#sys.stderr.write('typeid: ' + typeID + '\n')
		expCursor = conn.cursor()
		expCursor.execute(sqlStr)
		expRow = expCursor.fetchone()
		while (expRow != None):
			if expRow[0] != tmpGroup:
				weightTotal += int(expRow[3])
				tmpGroup = int(expRow[3])
			if expRow[1] in stats:
				stats[expRow[1]] = stats[expRow[1]] + int(expRow[2])
			else:
				stats[expRow[1]] = int(expRow[2])
			expRow = expCursor.fetchone()

		expCursor.close()
		# calculate column sort by based on quality weights
		for k, v in stats.iteritems():
			weightVal = '%.2f' % (v / weightTotal * 200)
			obyStr = obyStr + '+CASE WHEN ' + k + 'max > 0 THEN ((' + k + '-' + k + 'min) / (' + k + 'max-' + k + 'min))*' + weightVal + ' ELSE ' + weightVal + '/2 END'
			obyStr2 = obyStr2 + '+' + weightVal
		if len(obyStr)>1:
			obyStr = obyStr[1:]
		if len(obyStr2)>1:
			obyStr2 = obyStr2[1:]
		return ' (' + obyStr + ') / (' + obyStr2 + ')'
	else:
		return 'OQ'

# get comma separated list of resource categories to exclude for a set of schematics
def getTypeResGroups(tabID, typeID):
	resStr = '""'
	if tabID.isdigit():
		sqlStr = '(SELECT rtg.resourceGroup FROM tResourceTypeGroup rtg INNER JOIN tSchematicIngredients ON rtg.resourceType = tSchematicIngredients.ingredientObject INNER JOIN tSchematic ON tSchematicIngredients.schematicID = tSchematic.schematicID WHERE tSchematic.craftingTab=' + tabID
		if typeID.isdigit():
			sqlStr = sqlStr + ' AND tSchematic.objectType=' + typeID
		sqlStr = sqlStr + ' GROUP BY rtg.resourceGroup) UNION (SELECT rgc.resourceGroup FROM tResourceGroupCategory rgc INNER JOIN tSchematicIngredients ON rgc.resourceCategory = tSchematicIngredients.ingredientObject INNER JOIN tSchematic ON tSchematicIngredients.schematicID = tSchematic.schematicID WHERE tSchematic.craftingTab=' + tabID
		if typeID.isdigit():
			sqlStr = sqlStr + ' AND tSchematic.objectType=' + typeID
		sqlStr = sqlStr + ' GROUP BY rgc.resourceGroup) UNION (SELECT rgc.resourceGroup FROM tResourceGroupCategory rgc INNER JOIN tSchematicIngredients ON rgc.resourceGroup = tSchematicIngredients.ingredientObject INNER JOIN tSchematic ON tSchematicIngredients.schematicID = tSchematic.schematicID WHERE tSchematic.craftingTab=' + tabID
		if typeID.isdigit():
			sqlStr = sqlStr + ' AND tSchematic.objectType=' + typeID
		sqlStr = sqlStr + ' GROUP BY rgc.resourceGroup);'
		cursor = conn.cursor()
		cursor.execute(sqlStr)
		row = cursor.fetchone()
		while (row != None):
			resStr = resStr + ',"' + row[0] + '"'
			row = cursor.fetchone()

	return resStr

# get comma separated list of resource categories to exclude for a set of schematics
def getProfResGroups(profID):
	resStr = '""'
	if profID.isdigit():
		sqlStr = '(SELECT rtg.resourceGroup FROM tResourceTypeGroup rtg INNER JOIN tSchematicIngredients ON rtg.resourceType = tSchematicIngredients.ingredientObject INNER JOIN tSchematic ON tSchematicIngredients.schematicID = tSchematic.schematicID INNER JOIN tSkillGroup ON tSchematic.skillGroup = tSkillGroup.skillGroup WHERE profID=' + profID
		sqlStr = sqlStr + ' GROUP BY rtg.resourceGroup) UNION (SELECT rgc.resourceGroup FROM tResourceGroupCategory rgc INNER JOIN tSchematicIngredients ON rgc.resourceCategory = tSchematicIngredients.ingredientObject OR rgc.resourceGroup = tSchematicIngredients.ingredientObject INNER JOIN tSchematic ON tSchematicIngredients.schematicID = tSchematic.schematicID INNER JOIN tSkillGroup ON tSchematic.skillGroup = tSkillGroup.skillGroup WHERE profID=' + profID
		sqlStr = sqlStr + ' GROUP BY rgc.resourceGroup);'
		cursor = conn.cursor()
		cursor.execute(sqlStr)
		row = cursor.fetchone()
		while (row != None):
			resStr = resStr + ',"' + row[0] + '"'
			row = cursor.fetchone()

	return resStr

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
	sid = form.getfirst('gh_sid', '')

galaxy = form.getfirst('galaxy', '')
prof = form.getfirst('prof', '')
craftingTab = form.getfirst('craftingTab', '')
objectType = form.getfirst('objectType', '')
resGroup = form.getfirst('resGroup', '')
unavailable = form.getfirst('unavailable', '')
resType = form.getfirst('resType', '')
boxFormat = form.getfirst('boxFormat', '')
# Get a session
logged_state = 0
linkappend = ''
# escape input to prevent sql injection
sid = dbShared.dbInsertSafe(sid)
galaxy = dbShared.dbInsertSafe(galaxy)
prof = dbShared.dbInsertSafe(prof)
resGroup = dbShared.dbInsertSafe(resGroup)
resType = dbShared.dbInsertSafe(resType)
boxFormat = dbShared.dbInsertSafe(boxFormat)

sess = dbSession.getSession(sid, 2592000)
if (sess != ''):
	logged_state = 1
	currentUser = sess
	if (useCookies == 0):
		linkappend = 'gh_sid=' + sid


# Main program

print 'Content-type: text/html\n'
print '<table width="100%" class=resourceStats>'
if galaxy != '':
	galaxyState = dbShared.galaxyState(galaxy)
	conn = dbShared.ghConn()

	# Only show update tools if user logged in and has positive reputation
	stats = dbShared.getUserStats(currentUser, galaxy).split(",")

	cursor = conn.cursor()
	orderVals = ''
	if boxFormat == '0':
		formatStyle = 0
	else:
		formatStyle = 1
	if logged_state == 1:
		favJoin = ' LEFT JOIN (SELECT itemID, favGroup FROM tFavorites WHERE userID="' + currentUser + '" AND favType=1) favs ON tResources.spawnID = favs.itemID'
		favCols = ', favGroup'
	else:
		favJoin = ''
		favCols = ', NULL'

	if (cursor):
		if prof.isdigit() and prof != '0':
			# get order by profession combined schematic use
			orderVals += getProfOrder(prof)
		elif craftingTab.isdigit():
			# get order by crafting tab + object type schematic use
			orderVals += getTypeOrder(craftingTab, objectType)
		else:
			# base order on average presence of stats in all schematics of all present stats with extra modifier if an extremely high stat other than CR or ER exists
			orderVals += ' ((CASE WHEN CRmax > 0 THEN ((CR-CRmin) / (CRmax-CRmin))*.06 ELSE 0 END + CASE WHEN CDmax > 0 THEN ((CD-CDmin) / (CDmax-CDmin))*12.74 ELSE 0 END + CASE WHEN DRmax > 0 THEN ((DR-DRmin) / (DRmax-DRmin))*12.26 ELSE 0 END + CASE WHEN FLmax > 0 THEN ((FL-FLmin) / (FLmax-FLmin))*3.22 ELSE 0 END + CASE WHEN HRmax > 0 THEN ((HR-HRmin) / (HRmax-HRmin))*1.27 ELSE 0 END + CASE WHEN MAmax > 0 THEN ((MA-MAmin) / (MAmax-MAmin))*5.1 ELSE 0 END + CASE WHEN PEmax > 0 THEN ((PE-PEmin) / (PEmax-PEmin))*9.34 ELSE 0 END + CASE WHEN OQmax > 0 THEN ((OQ-OQmin) / (OQmax-OQmin))*30.64 ELSE 0 END + CASE WHEN SRmax > 0 THEN ((SR-SRmin) / (SRmax-SRmin))*9.16 ELSE 0 END + CASE WHEN UTmax > 0 THEN ((UT-UTmin) / (UTmax-UTmin))*16.2 ELSE 0 END)'
			orderVals += ' / (CASE WHEN CRmax > 0 THEN .06 ELSE 0 END + CASE WHEN CDmax > 0 THEN 12.74 ELSE 0 END + CASE WHEN DRmax > 0 THEN 12.26 ELSE 0 END + CASE WHEN FLmax > 0 THEN 3.22 ELSE 0 END + CASE WHEN HRmax > 0 THEN 1.27 ELSE 0 END + CASE WHEN MAmax > 0 THEN 5.1 ELSE 0 END + CASE WHEN PEmax > 0 THEN 9.34 ELSE 0 END + CASE WHEN OQmax > 0 THEN 30.64 ELSE 0 END + CASE WHEN SRmax > 0 THEN 9.16 ELSE 0 END + CASE WHEN UTmax > 0 THEN 16.2 ELSE 0 END) * 1000)'
			orderVals += ' + (CASE WHEN GREATEST(IFNULL((CD-CDmin) / (CDmax-CDmin),0), IFNULL((DR-DRmin) / (DRmax-DRmin),0), IFNULL((FL-FLmin) / (FLmax-FLmin),0), IFNULL((HR-HRmin) / (HRmax-HRmin),0), IFNULL((MA-MAmin) / (MAmax-MAmin),0), IFNULL((PE-PEmin) / (PEmax-PEmin),0), IFNULL((OQ-OQmin) / (OQmax-OQmin),0), IFNULL((SR-SRmin) / (SRmax-SRmin),0), IFNULL((UT-UTmin) / (UTmax-UTmin),0)) > .85 THEN 5 ELSE 0 END)'
			orderVals += ' + (CASE WHEN GREATEST(IFNULL((CD-CDmin) / (CDmax-CDmin),0), IFNULL((DR-DRmin) / (DRmax-DRmin),0), IFNULL((FL-FLmin) / (FLmax-FLmin),0), IFNULL((HR-HRmin) / (HRmax-HRmin),0), IFNULL((MA-MAmin) / (MAmax-MAmin),0), IFNULL((PE-PEmin) / (PEmax-PEmin),0), IFNULL((OQ-OQmin) / (OQmax-OQmin),0), IFNULL((SR-SRmin) / (SRmax-SRmin),0), IFNULL((UT-UTmin) / (UTmax-UTmin),0)) > .98 THEN 20 ELSE 0 END)'

		sqlStr1 = 'SELECT spawnID, spawnName, tResources.galaxy, entered, enteredBy, tResources.resourceType, resourceTypeName, resourceGroup,'
		sqlStr1 += ' CR, CD, DR, FL, HR, MA, PE, OQ, SR, UT, ER,'
		sqlStr1 += ' CASE WHEN CRmax > 0 THEN ((CR-CRmin) / (CRmax-CRmin))*100 ELSE NULL END AS CRperc, CASE WHEN CDmax > 0 THEN ((CD-CDmin) / (CDmax-CDmin))*100 ELSE NULL END AS CDperc, CASE WHEN DRmax > 0 THEN ((DR-DRmin) / (DRmax-DRmin))*100 ELSE NULL END AS DRperc, CASE WHEN FLmax > 0 THEN ((FL-FLmin) / (FLmax-FLmin))*100 ELSE NULL END AS FLperc, CASE WHEN HRmax > 0 THEN ((HR-HRmin) / (HRmax-HRmin))*100 ELSE NULL END AS HRperc, CASE WHEN MAmax > 0 THEN ((MA-MAmin) / (MAmax-MAmin))*100 ELSE NULL END AS MAperc, CASE WHEN PEmax > 0 THEN ((PE-PEmin) / (PEmax-PEmin))*100 ELSE NULL END AS PEperc, CASE WHEN OQmax > 0 THEN ((OQ-OQmin) / (OQmax-OQmin))*100 ELSE NULL END AS OQperc, CASE WHEN SRmax > 0 THEN ((SR-SRmin) / (SRmax-SRmin))*100 ELSE NULL END AS SRperc, CASE WHEN UTmax > 0 THEN ((UT-UTmin) / (UTmax-UTmin))*100 ELSE NULL END AS UTperc, CASE WHEN ERmax > 0 THEN ((ER-ERmin) / (ERmax-ERmin))*100 ELSE NULL END AS ERperc,'
		sqlStr1 += ' containerType, ' + orderVals + ', verified, verifiedBy, unavailable, unavailableBy' + favCols + ' FROM tResources INNER JOIN tResourceType ON tResources.resourceType = tResourceType.resourceType' + favJoin
		if (resGroup != 'any' and resGroup != ''):
			sqlStr1 += ' INNER JOIN (SELECT resourceType FROM tResourceTypeGroup WHERE resourceGroup="' + resGroup + '" GROUP BY resourceType) rtg ON tResources.resourceType = rtg.resourceType'
		if unavailable == "1":
			sqlStr1 += ' WHERE tResources.galaxy=' + galaxy
		else:
			sqlStr1 += ' WHERE tResources.galaxy=' + galaxy + ' AND unavailable IS NULL'
		if (resType != 'any' and resType != ''):
			sqlStr1 += ' AND tResources.resourceType = "' + resType + '"'
		if prof.isdigit() and prof != '0':
			sqlStr1 += ' AND tResourceType.resourceGroup IN (' + getProfResGroups(prof) + ')'
		if craftingTab.isdigit():
			sqlStr1 += ' AND tResourceType.resourceGroup IN (' + getTypeResGroups(craftingTab, objectType) + ')'
		sqlStr1 += ' ORDER BY'
		sqlStr1 += orderVals

		sqlStr1 += ' DESC LIMIT 6;'
		#sys.stderr.write(sqlStr1)
		cursor.execute(sqlStr1)
		row = cursor.fetchone()
		while (row != None):
			# populate spawn object and print
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

			s.overallScore = row[31]
			s.entered = row[3]
			s.enteredBy = row[4]
			s.verified = row[32]
			s.verifiedBy = row[33]
			s.unavailable = row[34]
			s.unavailableBy = row[35]
			if row[36] != None:
				s.favorite = 1
			s.planets = dbShared.getSpawnPlanets(conn, row[0], True, row[2])

			print '  <tr><td>'
			print s.getHTML(formatStyle, "", logged_state > 0 and galaxyState == 1, int(stats[2]))
			print '</td></tr>'
			row = cursor.fetchone()

		cursor.close()
	conn.close()
print '  </table>'
