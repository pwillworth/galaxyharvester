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
from http import cookies
import dbSession
import dbShared
import cgi
import pymysql
import ghShared
import ghLists
import ghObjects
#

def getTableHeader(sortBy, editable):
	dbCols = ['spawnName','resourceTypeName','ER','CR','CD','DR','FL','HR','MA','PE','OQ','SR','UT','units']
	headerCols = ['Name','Type','ER','CR','CD','DR','FL','HR','MA','PE','OQ','SR','UT','units']
	if editable:
		headerString = '<tr><th></th>'
	else:
		headerString = '<tr>'
	for col in range(len(headerCols)):
		if (sortBy == dbCols[col]):
			headerStyle = 'sorted'
		else:
			headerStyle = 'tableHead'
		headerString = ''.join((headerString, '<th class="', headerStyle, '" onclick="filterResources(\'', dbCols[col], '\')">', headerCols[col], '</th>'))

	if editable:
		headerString = ''.join((headerString, '<th style="background-image:url(/images/xRed16.png);background-repeat:no-repeat;background-position:0px 0px;" title="Despawn Alert"></th><th></th>'))
	headerString = ''.join((headerString, '</tr>'))

	return headerString

def xstr(s):
	return '' if s is None else str(s)


form = cgi.FieldStorage()
# Get Cookies
errorstr = ''
result = ''
C = cookies.SimpleCookie()
try:
	C.load(os.environ['HTTP_COOKIE'])
except KeyError:
	errorstr = 'no cookies\n'

if errorstr == '':
	try:
		currentUser = C['userID'].value
	except KeyError:
		currentUser = ''
	try:
		sid = C['gh_sid'].value
	except KeyError:
		sid = form.getfirst('gh_sid', '')
else:
	currentUser = ''
	sid = form.getfirst('gh_sid', '')

# Get a session
logged_state = 0
galaxy = form.getfirst('galaxy', '')
uid = form.getfirst('uid', '')
resGroup = form.getfirst('resGroup', '')
resType = form.getfirst('resType', '')
unitsGT = form.getfirst('unitsGT', '')
unitsLT = form.getfirst('unitsLT', '')
formatType = form.getfirst('formatType', '')
resGroups = form.getfirst('resGroups', '')
resTypes = form.getfirst('resTypes', '')
favGroup = form.getfirst('favGroup', '')
sortBy = form.getfirst('sortBy', '')

# escape input to prevent sql injection
sid = dbShared.dbInsertSafe(sid)
galaxy = dbShared.dbInsertSafe(galaxy)
uid = dbShared.dbInsertSafe(uid)
resGroup = dbShared.dbInsertSafe(resGroup)
resType = dbShared.dbInsertSafe(resType)
unitsGT = dbShared.dbInsertSafe(unitsGT)
unitsLT = dbShared.dbInsertSafe(unitsLT)
resGroups = dbShared.dbInsertSafe(resGroups)
resTypes = dbShared.dbInsertSafe(resTypes)
favGroup = dbShared.dbInsertSafe(favGroup)
sortBy = dbShared.dbInsertSafe(sortBy)

sess = dbSession.getSession(sid)
if (sess != ''):
	logged_state = 1
	currentUser = sess

if uid == '':
	uid = currentUser

joinStr = ""
criteriaStr = ""

# Build Criteria to Limit list
if (resType != "any" and resType != ""):
	criteriaStr = criteriaStr + " AND tResources.resourceType='" + resType + "'"
if (resGroup != "any" and resGroup != ""):
	joinStr = joinStr + " INNER JOIN (SELECT resourceType FROM tResourceTypeGroup WHERE resourceGroup='" + resGroup + "' GROUP BY resourceType) rtg ON tResourceType.resourceType = rtg.resourceType"
if (resTypes != "" and resGroups == ""):
	criteriaStr = criteriaStr + " AND tResources.resourceType IN (" + resTypes + ")"
if (resGroups != "" and resTypes == ""):
	joinStr = joinStr + " INNER JOIN (SELECT resourceType FROM tResourceTypeGroup WHERE resourceGroup IN (" + resGroups + ") GROUP BY resourceType) rtg ON tResourceType.resourceType = rtg.resourceType"
if (resGroups != "" and resTypes != ""):
	joinStr = joinStr + " INNER JOIN (SELECT resourceType FROM tResourceTypeGroup WHERE resourceGroup IN (" + resGroups + ") OR resourceType IN (" + resTypes + ") GROUP BY resourceType) rtg ON tResourceType.resourceType = rtg.resourceType"

if (unitsGT != "" and unitsGT.isdigit()):
	criteriaStr = criteriaStr + " AND units > " + str(unitsGT)
if (unitsLT != "" and unitsLT.isdigit()):
	criteriaStr = criteriaStr + " AND units < " + str(unitsLT)
if favGroup != "any" and favGroup != "undefined" and favGroup != "":
	criteriaStr = criteriaStr + " AND favGroup='" + favGroup + "'"

if formatType == 'alerts':
	criteriaStr = criteriaStr + " AND despawnAlert > 0 AND unavailable IS NULL"

# Restrict returned results if user is not sharing inventory
accessString = 'My'
if uid != currentUser:
	invShared = dbShared.getUserAttr(uid, 'sharedInventory')
	if invShared > 1:
		# Publicly shared
		accessString = '{0} Public'.format(uid)
	elif invShared > 0:
		# Shared with friends
		conn = dbShared.ghConn()
		cursor = conn.cursor()
		if (cursor):
			cursor.execute("SELECT added FROM tUserFriends WHERE userID=%s AND friendID=%s", [uid, currentUser])
			row = cursor.fetchone()
			if row == None:
				criteriaStr = criteriaStr + " AND 1=0"
		cursor.close()
		conn.close()
		accessString = '{0} Shared'.format(uid)
	else:
		# not shared
		criteriaStr = criteriaStr + " AND 1=0"
		accessString = 'No Shared'

# Build sorting clause
if formatType == 'inventory':
	orderStr = " ORDER BY tResourceType.resourceCategory, tResourceType.resourceGroup, tResources.resourceType"
if formatType == 'alerts':
	orderStr = " ORDER BY spawnName"
else:
	if sortBy != "" and sortBy != "undefined":
		orderStr = " ORDER BY favGroup ASC, " + sortBy + " DESC"
	else:
		orderStr = " ORDER BY favGroup ASC, entered DESC"

# Main program
currentGroup = "arvesgalhaxtery"
groupCount = 0
groupUnits = 0
groupResult = ""

if formatType == 'csv':
	print('Content-type: text/csv')
	print('Content-disposition: attachment; filename="inventory.csv"\n')
else:
	print('Content-type: text/html\n')

if uid != '':
	if galaxy.isdigit():
		galaxyState = dbShared.galaxyState(galaxy)
		conn = dbShared.ghConn()
		cursor = conn.cursor()
		if (cursor):
			sqlStr1 = 'SELECT spawnID, spawnName, tResources.galaxy, entered, enteredBy, tResources.resourceType, resourceTypeName, tResourceType.resourceGroup,'
			sqlStr1 += ' CR, CD, DR, FL, HR, MA, PE, OQ, SR, UT, ER,'
			sqlStr1 += ' CASE WHEN CRmax > 0 THEN (((CASE WHEN CR IS NULL THEN 0 ELSE CR END)-CRmin) / (CRmax-CRmin))*100 ELSE NULL END AS CRperc,'
			sqlStr1 += ' CASE WHEN CDmax > 0 THEN (((CASE WHEN CD IS NULL THEN 0 ELSE CD END)-CDmin) / (CDmax-CDmin))*100 ELSE NULL END AS CDperc,'
			sqlStr1 += ' CASE WHEN DRmax > 0 THEN (((CASE WHEN DR IS NULL THEN 0 ELSE DR END)-DRmin) / (DRmax-DRmin))*100 ELSE NULL END AS DRperc,'
			sqlStr1 += ' CASE WHEN FLmax > 0 THEN (((CASE WHEN FL IS NULL THEN 0 ELSE FL END)-FLmin) / (FLmax-FLmin))*100 ELSE NULL END AS FLperc,'
			sqlStr1 += ' CASE WHEN HRmax > 0 THEN (((CASE WHEN HR IS NULL THEN 0 ELSE HR END)-HRmin) / (HRmax-HRmin))*100 ELSE NULL END AS HRperc,'
			sqlStr1 += ' CASE WHEN MAmax > 0 THEN (((CASE WHEN MA IS NULL THEN 0 ELSE MA END)-MAmin) / (MAmax-MAmin))*100 ELSE NULL END AS MAperc,'
			sqlStr1 += ' CASE WHEN PEmax > 0 THEN (((CASE WHEN PE IS NULL THEN 0 ELSE PE END)-PEmin) / (PEmax-PEmin))*100 ELSE NULL END AS PEperc,'
			sqlStr1 += ' CASE WHEN OQmax > 0 THEN (((CASE WHEN OQ IS NULL THEN 0 ELSE OQ END)-OQmin) / (CASE WHEN OQmax-OQmin < 1 THEN 1 ELSE OQmax-OQmin END))*100 ELSE NULL END AS OQperc,'
			sqlStr1 += ' CASE WHEN SRmax > 0 THEN (((CASE WHEN SR IS NULL THEN 0 ELSE SR END)-SRmin) / (SRmax-SRmin))*100 ELSE NULL END AS SRperc,'
			sqlStr1 += ' CASE WHEN UTmax > 0 THEN (((CASE WHEN UT IS NULL THEN 0 ELSE UT END)-UTmin) / (UTmax-UTmin))*100 ELSE NULL END AS UTperc,'
			sqlStr1 += ' CASE WHEN ERmax > 0 THEN (((CASE WHEN ER IS NULL THEN 0 ELSE ER END)-ERmin) / (ERmax-ERmin))*100 ELSE NULL END AS ERperc,'
			sqlStr1 += ' tResourceType.containerType, verified, verifiedBy, unavailable, unavailableBy, favGroup, units, inventoryType, groupName, (SELECT GROUP_CONCAT(resourceGroup SEPARATOR ",") FROM tResourceTypeGroup rtg WHERE rtg.resourceType=tResources.resourceType), despawnAlert FROM tResources'
			sqlStr1 += ' INNER JOIN tResourceType ON tResources.resourceType = tResourceType.resourceType INNER JOIN tResourceGroup ON tResourceType.resourceGroup = tResourceGroup.resourceGroup INNER JOIN tFavorites ON tResources.spawnID = tFavorites.itemID' + joinStr
			sqlStr1 += ' WHERE userID="' + uid + '" AND favType=1 AND tResources.galaxy=' + galaxy + criteriaStr + orderStr + ';'
			cursor.execute(sqlStr1)
			row = cursor.fetchone()
			if row != None:
				currentGroup = row[35]
			else:
				result += accessString + ' - No Matching Resources.'

			if formatType == 'alerts':
				result += '<table id="tbl_despawnAlerts" class="resourceStats">'
			if formatType == 'csv':
				result += 'group,name,resource type,type name,ER,CR,CD,DR,FL,HR,MA,PE,OQ,SR,UT,units,enter date,unavailable date\n'

			while (row != None):
				if (currentGroup != row[35] and formatType == ''):
					# print group table
					result += '<h2 class="categoryHead" style="margin-top:10px;" tag="' + currentGroup + '">' + currentGroup.replace('_',' ') + ' (' + str(groupCount) + ' resources, ' + str(groupUnits) + ' units)</h2>'
					result += '<table id="tbl_' + currentGroup + '" style="width:770px;" class="resourceStats">'
					result += getTableHeader(sortBy, uid==currentUser and logged_state==1)
					result += groupResult
					result += '</table>'
					currentGroup = row[35]
					groupCount = 0
					groupUnits = 0
					groupResult = ""

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
				if row[35] != None:
					s.favorite = 1
					s.favGroup = row[35]
					if row[36] != None:
						s.units = row[36]
						groupUnits += s.units
					s.despawnAlert = row[40]
				s.inventoryType = row[37]
				s.groupName = row[38]
				if row[39] != None:
					s.groupList = ',' + row[39] + ','

				if formatType == 'inventory':
					result += s.getInventoryObject()
				elif formatType == 'alerts':
					result += s.getAlertsRow()
				elif formatType == 'csv':
					result += ','.join((s.favGroup, s.spawnName, s.resourceType, s.resourceTypeName, xstr(s.stats.ER), xstr(s.stats.CR), xstr(s.stats.CD), xstr(s.stats.DR), xstr(s.stats.FL), xstr(s.stats.HR), xstr(s.stats.MA), xstr(s.stats.PE), xstr(s.stats.OQ), xstr(s.stats.SR), xstr(s.stats.UT), str(s.units), xstr(s.entered), xstr(s.unavailable)))
					result += '\n'
				else:
					groupResult += s.getRow(uid == currentUser and logged_state==1)
					groupCount += 1

				row = cursor.fetchone()

			cursor.close()
		conn.close()
		if groupCount > 0 and formatType == '':
			# print last group
			result += '<h2 class="categoryHead" style="margin-top:10px;" tag="' + currentGroup + '">' + currentGroup.replace('_',' ') + ' (' + str(groupCount) + ' resources, ' + str(groupUnits) + ' units)</h2>'
			result += '<table id="tbl_' + currentGroup + '" style="width:760px;" class="resourceStats">'
			result += getTableHeader(sortBy, uid==currentUser and logged_state==1)
			result += groupResult
			result += '</table>'
		if formatType == 'alerts':
			result += '</table>'
	else:
		result = "Error: No galaxy specified"
else:
	result = "Error: No user specified."

print(result)
