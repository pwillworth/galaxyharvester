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
import dbSession
import MySQLdb
import cgi
import Cookie
import ghShared
import ghLists
import dbShared
#

form = cgi.FieldStorage()
cookies = Cookie.SimpleCookie()
errorstr = ''
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
	sid = form.getfirst('gh_sid', '')

# Get a session
logged_state = 0
sess = dbSession.getSession(sid, 2592000)
if (sess != ''):
	logged_state = 1
	currentUser = sess

groupType = form.getfirst('groupType', '')
profession = form.getfirst('profession', '')
craftingTab = form.getfirst('craftingTab', '')
resType = form.getfirst('resType', '')
resSecondary = form.getfirst('resSecondary', '')
resGroup = form.getfirst('resGroup', '')
selectSchematic = form.getfirst('selectSchematic', '')
listFormat = form.getfirst('listFormat', 'list')
galaxy = form.getfirst('galaxy', '')
# escape input to prevent sql injection
groupType = dbShared.dbInsertSafe(groupType)
profession = dbShared.dbInsertSafe(profession)
craftingTab = dbShared.dbInsertSafe(craftingTab)
resType = dbShared.dbInsertSafe(resType)
resSecondary = dbShared.dbInsertSafe(resSecondary)
resGroup = dbShared.dbInsertSafe(resGroup)
selectSchematic = dbShared.dbInsertSafe(selectSchematic)
listFormat = dbShared.dbInsertSafe(listFormat)

# groupType determines the filtering method for narrowing down schematic list
filterStr = ''
joinStr = ''
if (groupType == 'prof'):
	if (profession.isdigit()):
		filterStr = ' WHERE tSkillGroup.profID = ' + str(profession)
elif (groupType == 'tab'):
	if (craftingTab.isdigit()):
		filterStr = ' WHERE tSchematic.craftingTab = ' + str(craftingTab)
elif (groupType == 'res'):
	if (resGroup != '' and resGroup != None):
		if resSecondary == '1':
			joinStr = ' INNER JOIN (SELECT resourceType FROM tResourceTypeGroup WHERE resourceGroup="' + resGroup + '") rtg ON ingredientObject = rtg.resourceType'
		else:
			filterStr = ' WHERE ingredientObject = "' + resGroup + '"'
	else:
		if resSecondary == '1':
			filterStr = ' WHERE ingredientObject IN (SELECT tResourceTypeGroup.resourceGroup FROM tResourceTypeGroup INNER JOIN tResourceGroup ON tResourceTypeGroup.resourceGroup=tResourceGroup.resourceGroup WHERE resourceType="' + resType + '" AND groupLevel=(SELECT Max(rg.groupLevel) FROM tResourceTypeGroup rtg INNER JOIN tResourceGroup rg ON rtg.resourceGroup = rg.resourceGroup WHERE rtg.resourceType="' + resType + '") GROUP BY tResourceTypeGroup.resourceGroup)'
			joinStr = ' INNER JOIN (SELECT tResourceTypeGroup.resourceGroup FROM tResourceTypeGroup INNER JOIN tResourceGroup ON tResourceTypeGroup.resourceGroup=tResourceGroup.resourceGroup WHERE resourceType="' + resType + '" AND groupLevel=(SELECT Max(rg.groupLevel) FROM tResourceTypeGroup rtg INNER JOIN tResourceGroup rg ON rtg.resourceGroup = rg.resourceGroup WHERE rtg.resourceType="' + resType + '") GROUP BY tResourceTypeGroup.resourceGroup) rtgg ON ingredientObject = rtgg.resourceGroup'
		else:
			filterStr = ' WHERE ingredientObject = "' + resType + '"'
elif (groupType == 'favorite'):
	filterStr = ' WHERE tFavorites.userID = "' + currentUser + '" AND favType = 4'
	joinStr = ' INNER JOIN tFavorites ON tSchematic.schematicID = tFavorites.favGroup'

# Some schematics are custom entered per galaxy but those with galaxyID 0 are for all
if galaxy.isdigit():
	filterStr = filterStr + ' AND tSchematic.galaxy IN (0, {0})'.format(galaxy)

# We output an unordered list or a bunch of select element options depending on listFormat
currentGroup = ''
currentIngredient = ''
print 'Content-type: text/html\n'
if listFormat != 'option':
	print '  <ul class="schematics">'

conn = dbShared.ghConn()
cursor = conn.cursor()
if (cursor):
	if (groupType == 'tab' or groupType == 'favorite'):
		sqlStr1 = 'SELECT schematicID, tSchematic.craftingTab, typeName, schematicName FROM tSchematic INNER JOIN tObjectType ON tSchematic.objectType = tObjectType.objectType' + joinStr + filterStr + ' ORDER BY craftingTab, typeName, schematicName'
	elif (groupType == 'res'):
		sqlStr1 = 'SELECT DISTINCT tSchematic.schematicID, tSchematic.craftingTab, typeName, schematicName, ingredientObject, res.resName FROM tSchematic INNER JOIN tObjectType ON tSchematic.objectType = tObjectType.objectType INNER JOIN tSchematicIngredients ON tSchematic.schematicID = tSchematicIngredients.schematicID' + joinStr + ' LEFT JOIN (SELECT resourceGroup AS resID, groupName AS resName FROM tResourceGroup UNION ALL SELECT resourceType, resourceTypeName FROM tResourceType) res ON ingredientObject = res.resID' + filterStr + ' ORDER BY res.resName, craftingTab, typeName, schematicName'
	else:
		sqlStr1 = 'SELECT schematicID, profName, skillGroupName, schematicName FROM tSchematic INNER JOIN tSkillGroup ON tSchematic.skillGroup = tSkillGroup.skillGroup LEFT JOIN tProfession ON tSkillGroup.profID = tProfession.profID' + joinStr + filterStr
		if listFormat == 'option':
			sqlStr1 += ' ORDER BY schematicName'
		else:
			sqlStr1 += ' ORDER BY profName, skillGroupName, schematicName'

	cursor.execute(sqlStr1)
	row = cursor.fetchone()
	if (row == None):
		print '    <li><h3>No Schematics Found</h3></li>'
	while (row != None):
		if listFormat == 'option':
			print '<option value="' + row[0] + '">' + row[3] + '</option>'
		else:
			if (groupType == 'res'):
				if (currentIngredient != row[5]):
					print '  </ul>'
					print '  <div  style="margin-top:14px;"><a class="bigLink" href="' + ghShared.BASE_SCRIPT_URL + 'resourceType.py/' + row[4] + '">' + row[5] + '</a></div>'
					print '  <ul class="schematics">'
					currentIngredient = row[5]
					currentGroup = ''
			if (currentGroup != row[2]):
				print '    <li><h3>' + row[2] + '</h3></li>'
				currentGroup = row[2]
			if row[0] == selectSchematic:
				print '    <li class="listSelected"><a href="' + ghShared.BASE_SCRIPT_URL + 'schematics.py/' + row[0] + '">' + row[3] + '</a></li>'
			else:
				print '    <li><a href="' + ghShared.BASE_SCRIPT_URL + 'schematics.py/' + row[0] + '">' + row[3] + '</a></li>'
		row = cursor.fetchone()

	cursor.close()
conn.close()
if listFormat != 'option':
	print '  </ul>'
