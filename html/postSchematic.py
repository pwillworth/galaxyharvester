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
import re
import Cookie
import dbSession
import dbShared
import ghShared
import cgi
import MySQLdb
import re

# create a URL safe schematic id based on proposed name
def generateSchematicID(schematicName, galaxy):
	galaxyLen = len(str(galaxy))
	newID = schematicName.replace(' ', '_')
	newID = newID.translate(None, ';/?:@=&"<>#%\{\}|\^~[]`')
	newID = newID[:127-galaxyLen] + str(galaxy)

	return newID


# Scrape data from uploaded lua file to create schematic
def addSchematicFromLua(conn, skillGroup, luaSchematic, luaObject, galaxy, userID):
	schem = {}
	badSchem = False
	schemID = ""

    # Extract value pairs from the two files
	while 1:
		line = luaSchematic.file.readline()
		if not line: break
		line.strip()
		eqPos = line.find("=")
		if (eqPos != -1):
			if schemID == "":
				schemID = line[:eqPos].strip()
				schemID = schemID[23:]
			sName = line[:eqPos].strip()
			sVal = line[eqPos+1:line.rfind(",")].strip().replace('"', '')
			schem[sName] = sVal

	if luaObject.file:
		while 1:
			oline = luaObject.file.readline()
			if not oline: break
			oline.strip()
			oeqPos = oline.find("=")
			if (oeqPos != -1):
				oName = oline[:oeqPos].strip()
				oVal = oline[oeqPos+1:oline.rfind(",")].strip().replace('"', '')
				if not oName in schem.keys():
					schem[oName] = oVal

	# Make sure schematic is valid and does not already exist
	if schemID == '':
		result = 'Error: Could not determine schematic data from schematic lua file.  Should contain id line but could not find it.'
		badSchem = True

	checkCursor = conn.cursor()
	checkCursor.execute('SELECT schematicName FROM tSchematic WHERE schematicID=%s;', (schemID))
	checkRow = checkCursor.fetchone()
	if checkRow != None:
		result = 'Error: A schematic already exists with the same ID.  Check if you need to edit the existing one, or change the ID in lua file.'
		badSchem = True
	checkCursor.close()

	try:
		print "saving: " + schem["customObjectName"] + " - " + schem["targetTemplate"]
	except KeyError:
		result = 'Error: Could not even determine schematic name and object path from schematic lua file, it may be invalid.'
		badSchem = True

	# Translate value pairs into schematic data records
	if badSchem == False:
		# object type and group to be manually set later
		objectType = 0
		objectGroup = ""
		result = 'Schematic added.'
		missingKeys = ''

		# load high level schematic properties available
		craftingTab = 524288
		try:
			craftingTab = int(schem["craftingToolTab"])
		except KeyError:
			missingKeys = missingKeys + 'craftingToolTab,'
		complexity = 0
		try:
			complexity = int(schem["complexity"])
		except KeyError:
			missingKeys = missingKeys + 'complexity,'
		schemSize = 0
		try:
			schemSize = int(schem["size"])
		except KeyError:
			missingKeys = missingKeys + 'size,'
		xpType = "unknown"
		try:
			xpType = schem["xpType"]
		except KeyError:
			missingKeys = missingKeys + 'xpType,'
		xp = 0
		try:
			xp = int(schem["xp"])
		except KeyError:
			missingKeys = missingKeys + 'xp,'

		if len(missingKeys) > 0:
			result = '{0} Some keys were missing so this data may need to be manually edited: {1}'.format(result, missingKeys)

		# write schematic information to database
		cursor = conn.cursor()
		schemSQL = "INSERT INTO tSchematic (schematicID, schematicName, craftingTab, skillGroup, objectType, complexity, objectSize, xpType, xpAmount, objectPath, objectGroup, galaxy, enteredBy) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
		cursor.execute(schemSQL, (schemID, schem["customObjectName"], craftingTab, skillGroup, objectType, complexity, schemSize, xpType, xp, schem["targetTemplate"], objectGroup, galaxy, userID))

		# write ingredient information to database
		ingredients = []
		try:
			ingredients = schem["ingredientTitleNames"].strip('{').strip('}').split(", ")
			ingTypes = schem["ingredientSlotType"].strip('{').strip('}').split(", ")
			ingObjects = schem["resourceTypes"].strip('{').strip('}').split(", ")
			resQuantities = schem["resourceQuantities"].strip('{').strip('}').split(", ")
			resContribution = schem["contribution"].strip('{').strip('}').split(", ")
		except KeyError:
			result = '{0}  Could not determine ingredient data from schematic lua file.  Ingredients will need to entered manually or delete schematic, correct lua file, and try again.'.format(result)

		for i in range(len(ingredients)):
			if ingObjects[i][-5:] == ".iff\"":
				ingObject = ingObjects[i].replace("shared_","")
			else:
				ingObject = ingObjects[i]

			sys.stderr.write(ingredients[i] + '\n')
			ingSQL = "INSERT INTO tSchematicIngredients (schematicID, ingredientName, ingredientType, ingredientObject, ingredientQuantity, ingredientContribution) VALUES (%s, %s, %s, %s, %s, %s);"
			cursor.execute(ingSQL, (schemID, ingredients[i], ingTypes[i], ingObject, resQuantities[i], resContribution[i]))

		# write experimental property/quality info to database
		expProps = None
		try:
			expProps = schem["experimentalSubGroupTitles"].strip('{').strip('}').split(", ")
			expGroups = schem["experimentalGroupTitles"].strip('{').strip('}').split(", ")
			expCounts = schem["numberExperimentalProperties"].strip('{').strip('}').split(", ")
			# res data
			expResProps = schem["experimentalProperties"].strip('{').strip('}').split(", ")
			expResWeights = schem["experimentalWeights"].strip('{').strip('}').split(", ")
		except KeyError:
			result = '{0}  No schematic qualities data could be extracted from the object lua.  Qualities will need to be entered manually or delete schematic, correct lua file and try again.'.format(result)

		if expProps != None:
			weightPos = 0
			for i in range(len(expProps)):
				# count the number of resource property weights to add to quality record
				weightTotal = 0
				for i2 in range(int(expCounts[i])):
					if (expResProps[weightPos+i2] != "XX"):
						weightTotal += int(expResWeights[weightPos+i2])
				if (expProps[i] != "null"):
					qualSQL = "INSERT INTO tSchematicQualities (schematicID, expProperty, expGroup, weightTotal) VALUES (%s, %s, %s, %s);"
					cursor.execute(qualSQL, (schemID, expProps[i], expGroups[i], weightTotal))
				# add resource properties according to count for this quality attribute
				for i2 in range(int(expCounts[i])):
					if (expResProps[weightPos+i2] != "XX"):
						weightSQL = "INSERT INTO tSchematicResWeights (expQualityID, statName, statWeight) VALUES (LAST_INSERT_ID(), %s, %s);"
						cursor.execute(weightSQL, (expResProps[weightPos+i2], expResWeights[weightPos+i2]))

				weightPos += int(expCounts[i])
		cursor.close()

	return '{0}|{1}'.format(schemID, result)

# Copy details from an existing schematic for later edit
def addSchematicByCopy(conn, skillGroup, sourceSchematic, schematicName, galaxy, userID):
	schematicID = generateSchematicID(schematicName, galaxy)
	checkCursor = conn.cursor()
	checkCursor.execute('SELECT schematicName FROM tSchematic WHERE schematicID=%s;', (schematicID))
	checkRow = checkCursor.fetchone()
	checkCursor.close()
	if checkRow == None:
		# Proceed with schematic copy
		cursor = conn.cursor()
		schemSQL = "INSERT INTO tSchematic (schematicID, schematicName, craftingTab, skillGroup, objectType, complexity, objectSize, xpType, xpAmount, objectPath, objectGroup, galaxy, enteredBy) SELECT %s, %s, craftingTab, %s, objectType, complexity, objectSize, xpType, xpAmount, '', objectGroup, %s, %s FROM tSchematic WHERE schematicID=%s;"
		cursor.execute(schemSQL, (schematicID, schematicName, skillGroup, galaxy, userID, sourceSchematic))
		ingSQL = "INSERT INTO tSchematicIngredients (schematicID, ingredientName, ingredientType, ingredientObject, ingredientQuantity, ingredientContribution) SELECT %s, ingredientName, ingredientType, ingredientObject, ingredientQuantity, ingredientContribution FROM tSchematicIngredients WHERE schematicID=%s;"
		cursor.execute(ingSQL, (schematicID, sourceSchematic))
		# Iterate over the quality groups so we can generate new sets of res weights records pointing to new auto increment ids
		qualCursor = conn.cursor()
		qualSQL = "SELECT expQualityID, expProperty, expGroup, weightTotal FROM tSchematicQualities WHERE schematicID=%s"
		qualCursor.execute(qualSQL, (sourceSchematic))
		qualRow = qualCursor.fetchone()
		while qualRow != None:
			qualSQL = "INSERT INTO tSchematicQualities (schematicID, expProperty, expGroup, weightTotal) VALUES (%s, %s, %s, %s);"
			cursor.execute(qualSQL, (schematicID, qualRow[1], qualRow[2], qualRow[3]))
			weightSQL = "INSERT INTO tSchematicResWeights (expQualityID, statName, statWeight) SELECT LAST_INSERT_ID(), statName, statWeight FROM tSchematicResWeights WHERE expQualityID=%s;"
			cursor.execute(weightSQL, qualRow[0])
			qualRow = qualCursor.fetchone()
		qualCursor.close()
		cursor.close()
		result = 'Schematic copied.'
	else:
		result = 'Error: The name you are providing is very similar to an existing schematic resulting in a duplicate id.  Please look at at schematic {0} do make sure you are not adding a duplicate or make the name more unique.'.format(checkRow[0])

	return '{0}|{1}'.format(schematicID, result)

# Add the basic skeleton of the schematic to be filled in later on edit screen
def addSchematicSkeleton(conn, skillGroup, schematicName, galaxy, userID):
	schematicID = generateSchematicID(schematicName, galaxy)
	checkCursor = conn.cursor()
	checkCursor.execute('SELECT schematicName FROM tSchematic WHERE schematicID=%s;', (schematicID))
	checkRow = checkCursor.fetchone()
	checkCursor.close()
	if checkRow == None:
		# Proceed with schematic copy
		cursor = conn.cursor()
		schemSQL = "INSERT INTO tSchematic (schematicID, schematicName, craftingTab, skillGroup, objectType, complexity, objectSize, xpType, xpAmount, objectPath, objectGroup, galaxy, enteredBy) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
		cursor.execute(schemSQL, (schematicID, schematicName, 524288, skillGroup, 0, 0, 0, 'unknown', 0, '', '', galaxy, userID))
		cursor.close()

		result = 'Schematic created.'
	else:
		result = 'Error: The name you are providing is very similar to an existing schematic resulting in a duplicate id.  Please look at at schematic {0} do make sure you are not adding a duplicate or make the name more unique.'.format(checkRow[0])

	return '{0}|{1}'.format(schematicID, result)


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

# Get form info
galaxy = form.getfirst('galaxy', '')
detailsMethod = form.getfirst('oDetails', '')
profession = form.getfirst('schemProfSel', '')
skillGroup = form.getfirst('skillGroupSel', '')
copyFromSchem = form.getfirst('schemCopySel', '')
schematicName = form.getfirst('schematicName', '')
forceOp = form.getfirst('forceOp', '')
schematicID = form.getfirst('schematicID', '')

# escape input to prevent sql injection
sid = dbShared.dbInsertSafe(sid)
skillGroup = dbShared.dbInsertSafe(skillGroup)
copyFromSchem = dbShared.dbInsertSafe(copyFromSchem)
schematicName = dbShared.dbInsertSafe(schematicName)
schematicID = dbShared.dbInsertSafe(schematicID)

# Get a session
logged_state = 0

sess = dbSession.getSession(sid, 2592000)
if (sess != ''):
	logged_state = 1
	currentUser = sess

userReputation = -9999
# Validation
errstr = ''
result = ''
if logged_state == 1:
	# Lookup reputation to validate abilities
	stats = dbShared.getUserStats(currentUser, galaxy).split(",")
	userReputation = int(stats[2])
else:
	errstr = 'You must be logged in to add schematic data.'

if forceOp == 'edit':
	if len(schematicID) < 3:
		errstr = errstr + 'Error: Schematic ID must be provided to edit.'
else:
	if profession.isdigit() == False:
		errstr = errstr + 'Error: Profession ID must be provided to add a new schematic.'
	if len(skillGroup) < 3:
		errstr = errstr + 'Error: Skill Group must be provided to add a new schematic.'
	if userReputation < ghShared.MIN_REP_VALS['ADD_SCHEMATIC']:
		errstr = errstr + 'Error: You have not yet built enough reputation to add schematic data.'
	if galaxy.isdigit() == False or len(galaxy) > 5:
		errstr = errstr + 'Error: A valid numeric galaxy id must be provided to add the new schematic to.'
	if re.search('[><&]', schematicName):
		errstr = errstr + 'Error: Schematic name contains illegal characters.'

if detailsMethod == 'DetailsLua':
	if not form.has_key('schematicLua'):
		errstr = 'No schematic lua file sent.'
	else:
		luaSchematic = form['schematicLua']
		if not luaSchematic.file: errstr = 'schematic lua data is not a file.'

	if not form.has_key('objectLua'):
		luaObject = ''
	else:
		luaObject = form['objectLua']
		if not luaObject.file: errstr = "object lua data is not a file."

if detailsMethod == 'DetailsCopy':
	if len(copyFromSchem) < 3:
		errstr = errstr + 'Error: Must provide schematic to copy from.'
	if len(schematicName) < 3:
		errstr = errstr + 'Error: Valid schematic name must be provided.'

if errstr == '':
	conn = dbShared.ghConn()
	checkCursor = conn.cursor()

	if forceOp != 'edit':
		# check valid profession
		checkCursor.execute('SELECT profName FROM tProfession WHERE profID=%s', (profession))
		checkRow = checkCursor.fetchone()
		if checkRow == None:
			errstr = errstr + 'Error: Cannot find the profession for the id you provided.'
		checkRow = None
		# check for valid skill group
		checkCursor.execute('SELECT skillGroupName FROM tSkillGroup WHERE skillGroup=%s', (skillGroup))
		checkRow = checkCursor.fetchone()
		if checkRow == None:
			errstr = errstr + 'Error: Cannot find the skill group you provided.'

		if errstr == '':
			if detailsMethod == 'DetailsLua':
				results = addSchematicFromLua(conn, skillGroup, luaSchematic, luaObject, galaxy, currentUser).split('|')
				schematicID = results[0]
				result = results[1]
			elif detailsMethod == 'DetailsCopy':
				checkCursor.execute('SELECT schematicName FROM tSchematic WHERE schematicID=%s;', (copyFromSchem))
				row = checkCursor.fetchone()
				checkCursor.close()
				if row != None:
					results = addSchematicByCopy(conn, skillGroup, copyFromSchem, schematicName, galaxy, currentUser).split('|')
					schematicID = results[0]
					result = results[1]
				else:
					errstr = errstr + 'Error: Could not find the schematic requested to copy from.'
			else:
				results = addSchematicSkeleton(conn, skillGroup, schematicName, galaxy, currentUser).split('|')
				schematicID = results[0]
				result = results[1]

			if result.find("Error:") > -1:
				errstr = result
	else:
		# Update existing schematic
		checkCursor.execute('SELECT enteredBy FROM tSchematic WHERE schematicID=%s', (schematicID))
		checkRow = checkCursor.fetchone()
		if checkRow != None:
			if checkRow[0] == None or checkRow[0] == '':
				errstr = errstr + 'Error: That schematic is part of the core game schematics and cannot be edited.'
			elif checkRow[0] != currentUser and userReputation < ghShared.MIN_REP_VALS['EDIT_OTHER_SCHEMATIC']:
				errstr = errstr + 'Error: You do not have high enough reputation to edit other users\' schematic data yet.'

		errstr = 'Error: Not implemented yet'

	checkCursor.close()

	conn.close()

if errstr != '':
	if (forceOp == 'edit'):
		print 'Content-type: text/html\n'
		print errstr
	else:
		print 'Status: 303 See Other'
		print 'Location: /message.py?action=addschematicfail&actionreason=' + errstr
		print ''
else:
	if (forceOp == 'edit'):
		print 'Content-type: text/html\n'
		print 'Schematic saved.'
	else:
		# redirect to new/edited schematic
		print 'Status: 303 See Other'
		print 'Location: /schematics.py/{0}'.format(schematicID)
		print ''
