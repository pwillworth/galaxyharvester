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
import re
from http import cookies
import dbSession
import dbShared
import ghShared
import cgi
import pymysql
import json
import urllib

# create a URL safe schematic id based on proposed name
def generateSchematicID(schematicName, galaxy):
	galaxyLen = len(str(galaxy))
	newID = schematicName.replace(' ', '_')
	newID = newID.translate(None, ';/?:@=&"<>#%\{\}|\^~[]`\'')
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
	checkCursor.execute('SELECT schematicName FROM tSchematic WHERE schematicID=%s;', [schemID])
	checkRow = checkCursor.fetchone()
	if checkRow != None:
		result = 'Error: A schematic already exists with the same ID.  Check if you need to edit the existing one, or change the ID in lua file.'
		badSchem = True
	checkCursor.close()

	try:
		print("saving: " + schem["customObjectName"] + " - " + schem["targetTemplate"])
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
		cursor.execute(schemSQL, [schemID, schem["customObjectName"], craftingTab, skillGroup, objectType, complexity, schemSize, xpType, xp, schem["targetTemplate"], objectGroup, galaxy, userID])

		# write ingredient information to database
		ingredients = []
		try:
			ingredients = schem["ingredientTitleNames"].strip('{').strip('}').split(",")
			ingTypes = schem["ingredientSlotType"].strip('{').strip('}').split(",")
			ingObjects = schem["resourceTypes"].strip('{').strip('}').split(",")
			resQuantities = schem["resourceQuantities"].strip('{').strip('}').split(",")
			resContribution = schem["contribution"].strip('{').strip('}').split(",")
			# Git rid of whitespace that may be present after items
			ingredients = map(str.strip, ingredients)
			ingTypes = map(str.strip, ingTypes)
			ingObjects = map(str.strip, ingObjects)
			resQuantities = map(str.strip, resQuantities)
			resContribution = map(str.strip, resContribution)
		except KeyError:
			result = '{0}  Could not determine ingredient data from schematic lua file.  Ingredients will need to entered manually or delete schematic, correct lua file, and try again.'.format(result)

		if len(ingredients) == len(ingObjects):
			for i in range(len(ingredients)):
				if ingObjects[i][-5:] == ".iff\"":
					ingObject = ingObjects[i].replace("shared_","")
				else:
					ingObject = ingObjects[i]

				ingSQL = "INSERT INTO tSchematicIngredients (schematicID, ingredientName, ingredientType, ingredientObject, ingredientQuantity, ingredientContribution) VALUES (%s, %s, %s, %s, %s, %s);"
				cursor.execute(ingSQL, [schemID, ingredients[i], ingTypes[i], ingObject, resQuantities[i], resContribution[i]])
		else:
			result = '{0}  Count of ingredientTitleNames and resourceTypes does not match.'.format(result)

		# write experimental property/quality info to database
		expProps = None
		try:
			expProps = schem["experimentalSubGroupTitles"].strip('{').strip('}').split(",")
			expGroups = schem["experimentalGroupTitles"].strip('{').strip('}').split(",")
			expCounts = schem["numberExperimentalProperties"].strip('{').strip('}').split(",")
			# res data
			expResProps = schem["experimentalProperties"].strip('{').strip('}').split(",")
			expResWeights = schem["experimentalWeights"].strip('{').strip('}').split(",")
			# git rid of whitespace that may be present after items
			expProps = map(str.strip, expProps)
			expGroups = map(str.strip, expGroups)
			expCounts = map(str.strip, expCounts)
			expResProps = map(str.strip, expResProps)
			expResWeights = map(str.strip, expResWeights)
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
					cursor.execute(qualSQL, [schemID, expProps[i], expGroups[i], weightTotal])
				# add resource properties according to count for this quality attribute
				for i2 in range(int(expCounts[i])):
					if (expResProps[weightPos+i2] != "XX"):
						weightSQL = "INSERT INTO tSchematicResWeights (expQualityID, statName, statWeight) VALUES (LAST_INSERT_ID(), %s, %s);"
						cursor.execute(weightSQL, [expResProps[weightPos+i2], expResWeights[weightPos+i2]])

				weightPos += int(expCounts[i])
		cursor.close()

	return '{0}|{1}'.format(schemID, result)

# Copy details from an existing schematic for later edit
def addSchematicByCopy(conn, skillGroup, sourceSchematic, schematicName, galaxy, userID):
	schematicID = generateSchematicID(schematicName, galaxy)
	checkCursor = conn.cursor()
	checkCursor.execute('SELECT schematicName FROM tSchematic WHERE schematicID=%s;', [schematicID])
	checkRow = checkCursor.fetchone()
	checkCursor.close()
	if checkRow == None:
		# Proceed with schematic copy
		cursor = conn.cursor()
		schemSQL = "INSERT INTO tSchematic (schematicID, schematicName, craftingTab, skillGroup, objectType, complexity, objectSize, xpType, xpAmount, objectPath, objectGroup, galaxy, enteredBy) SELECT %s, %s, craftingTab, %s, objectType, complexity, objectSize, xpType, xpAmount, 'object/{0}', objectGroup, %s, %s FROM tSchematic WHERE schematicID=%s;".format(schematicID)
		cursor.execute(schemSQL, [schematicID, schematicName, skillGroup, galaxy, userID, sourceSchematic])
		ingSQL = "INSERT INTO tSchematicIngredients (schematicID, ingredientName, ingredientType, ingredientObject, ingredientQuantity, ingredientContribution) SELECT %s, ingredientName, ingredientType, ingredientObject, ingredientQuantity, ingredientContribution FROM tSchematicIngredients WHERE schematicID=%s;"
		cursor.execute(ingSQL, [schematicID, sourceSchematic])
		# Iterate over the quality groups so we can generate new sets of res weights records pointing to new auto increment ids
		qualCursor = conn.cursor()
		qualSQL = "SELECT expQualityID, expProperty, expGroup, weightTotal FROM tSchematicQualities WHERE schematicID=%s"
		qualCursor.execute(qualSQL, [sourceSchematic])
		qualRow = qualCursor.fetchone()
		while qualRow != None:
			qualSQL = "INSERT INTO tSchematicQualities (schematicID, expProperty, expGroup, weightTotal) VALUES (%s, %s, %s, %s);"
			cursor.execute(qualSQL, [schematicID, qualRow[1], qualRow[2], qualRow[3]])
			weightSQL = "INSERT INTO tSchematicResWeights (expQualityID, statName, statWeight) SELECT LAST_INSERT_ID(), statName, statWeight FROM tSchematicResWeights WHERE expQualityID=%s;"
			cursor.execute(weightSQL, [qualRow[0]])
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
	checkCursor.execute('SELECT schematicName FROM tSchematic WHERE schematicID=%s;', [schematicID])
	checkRow = checkCursor.fetchone()
	checkCursor.close()
	if checkRow == None:
		# Proceed with schematic copy
		cursor = conn.cursor()
		schemSQL = "INSERT INTO tSchematic (schematicID, schematicName, craftingTab, skillGroup, objectType, complexity, objectSize, xpType, xpAmount, objectPath, objectGroup, galaxy, enteredBy) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
		cursor.execute(schemSQL, [schematicID, schematicName, 524288, skillGroup, 0, 0, 0, 'unknown', 0, 'object/{0}'.format(schematicID), '', galaxy, userID])
		cursor.close()

		result = 'Schematic created.'
	else:
		result = 'Error: The name you are providing is very similar to an existing schematic resulting in a duplicate id.  Please look at at schematic {0} do make sure you are not adding a duplicate or make the name more unique.'.format(checkRow[0])

	return '{0}|{1}'.format(schematicID, result)

# Update values of existing schematic
def updateSchematic(conn, schematicID, schematic):
	try:
		schem = json.loads(schematic)
	except ValueError as e:
		return 'Error: invalid schematic object {0}'.format(e)

	cursor = conn.cursor()
	if (cursor == None):
		return 'Error: database unavailable'

	schemSQL = "UPDATE tSchematic SET schematicName=%s, craftingTab=%s, skillGroup=%s, complexity=%s, xpAmount=%s, objectType=%s WHERE schematicID=%s;"
	try:
		cursor.execute(schemSQL, [schem['schematicName'], schem['craftingTab'], schem['skillGroup'], schem['complexity'], schem['xpAmount'], schem['objectType'], schematicID])
	except KeyError as e:
		return 'Error: Schematic object is missing required data: {0}'.format(e)

	ingCheck = {}
	for ing in schem['ingredients']:
		if ing['ingredientName'] in ingCheck:
			return 'Error: You have multiple ingredients with the same name.  Each ingredient name must be different.  Please update and try saving again.'
		else:
			ingCheck[ing['ingredientName']] = ''

	ingredientsBefore = 0
	ingredientsAfter = 0
	ingredientsChanged = 0
	qualitiesBefore = 0
	qualitiesAfter = 0
	qualitiesChanged = 0
	weightsBefore = 0
	weightsAfter = 0
	# Update ingredients
	schemSQL = "DELETE FROM tSchematicIngredients WHERE schematicID=%s;"
	cursor.execute(schemSQL, [schematicID])
	ingredientsBefore = cursor.rowcount
	for ing in schem['ingredients']:
		ingSQL = "INSERT INTO tSchematicIngredients (schematicID, ingredientName, ingredientType, ingredientObject, ingredientQuantity, ingredientContribution) VALUES (%s, %s, %s, %s, %s, %s);"
		cursor.execute(ingSQL, [schematicID, ing['ingredientName'], ing['ingredientType'], ing['ingredientObject'], ing['ingredientQuantity'], 100])
		ingredientsAfter = ingredientsAfter + cursor.rowcount

	# Update Experimental Qualities
	schemSQL = "DELETE FROM tSchematicResWeights WHERE expQualityID IN (SELECT expQualityID FROM tSchematicQualities WHERE schematicID=%s);"
	cursor.execute(schemSQL, [schematicID])
	weightsBefore = cursor.rowcount
	schemSQL = "DELETE FROM tSchematicQualities WHERE schematicID=%s;"
	cursor.execute(schemSQL, [schematicID])
	qualitiesBefore = cursor.rowcount
	for expgroup in schem['qualityGroups']:
		# Update all properties in the groups
		for expProp in expgroup['properties']:
			weightTotal = 0
			schemSQL = "INSERT INTO tSchematicQualities (schematicID, expProperty, expGroup, weightTotal) VALUES (%s, %s, %s, %s);"
			cursor.execute(schemSQL, [schematicID, expProp['prop'], expgroup['group'], expProp['weightTotal']])
			qualitiesAfter = qualitiesAfter + cursor.rowcount
			# Update all resource weights in the properties
			for resWeight in expProp['statWeights']:
				schemSQL = "INSERT INTO tSchematicResWeights (expQualityID, statName, statWeight) VALUES (LAST_INSERT_ID(), %s, %s);"
				cursor.execute(schemSQL, [resWeight['stat'], resWeight['statWeight']])
				weightsAfter = weightsAfter + cursor.rowcount

	cursor.close()
	return 'Schematic Updated.  Ingredients {0} (was {1}), Qualities {2} (was {3}), Weights {4} (was {5}).'.format(ingredientsAfter, ingredientsBefore, qualitiesAfter, qualitiesBefore, weightsAfter, weightsBefore)

# Get current url
try:
	url = os.environ['SCRIPT_NAME']
except KeyError:
	url = ''

form = cgi.FieldStorage()
# Get Cookies
useCookies = 1
C = cookies.SimpleCookie()
try:
	C.load(os.environ['HTTP_COOKIE'])
except KeyError:
	useCookies = 0

if useCookies:
	try:
		currentUser = C['userID'].value
	except KeyError:
		currentUser = ''
	try:
		loginResult = C['loginAttempt'].value
	except KeyError:
		loginResult = 'success'
	try:
		sid = C['gh_sid'].value
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
schematic = form.getfirst('schematic', '')

# escape input to prevent sql injection
sid = dbShared.dbInsertSafe(sid)
skillGroup = dbShared.dbInsertSafe(skillGroup)
copyFromSchem = dbShared.dbInsertSafe(copyFromSchem)
schematicName = dbShared.dbInsertSafe(schematicName)
schematicID = dbShared.dbInsertSafe(schematicID)

# Get a session
logged_state = 0

sess = dbSession.getSession(sid)
if (sess != ''):
	logged_state = 1
	currentUser = sess

userReputation = -9999
# Validation
errstr = ''
result = ''
if logged_state == 1:
	# Lookup reputation to validate abilities
	conn = dbShared.ghConn()
	stats = dbShared.getUserStats(currentUser, galaxy).split(",")
	userReputation = int(stats[2])
	admin = dbShared.getUserAdmin(conn, currentUser, galaxy)
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
	if userReputation < ghShared.MIN_REP_VALS['ADD_SCHEMATIC'] and not admin:
		errstr = errstr + 'Error: You have not yet built enough reputation to add schematic data.'
	if galaxy.isdigit() == False or len(galaxy) > 5:
		errstr = errstr + 'Error: A valid numeric galaxy id must be provided to add the new schematic to.'
	if re.search('[><&]', schematicName):
		errstr = errstr + 'Error: Schematic name contains illegal characters.'

if detailsMethod == 'DetailsLua':
	if not 'schematicLua' in form:
		errstr = 'No schematic lua file sent.'
	else:
		luaSchematic = form['schematicLua']
		if not luaSchematic.file: errstr = 'schematic lua data is not a file.'

	if not 'objectLua' in form:
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
	checkCursor = conn.cursor()

	if forceOp != 'edit':
		# check valid profession
		checkCursor.execute('SELECT profName FROM tProfession WHERE profID=%s', [profession])
		checkRow = checkCursor.fetchone()
		if checkRow == None:
			errstr = errstr + 'Error: Cannot find the profession for the id you provided.'
		checkRow = None
		# check for valid skill group
		checkCursor.execute('SELECT skillGroupName FROM tSkillGroup WHERE skillGroup=%s', [skillGroup])
		checkRow = checkCursor.fetchone()
		if checkRow == None:
			errstr = errstr + 'Error: Cannot find the skill group you provided.'

		if errstr == '':
			if detailsMethod == 'DetailsLua':
				results = addSchematicFromLua(conn, skillGroup, luaSchematic, luaObject, galaxy, currentUser).split('|')
				schematicID = results[0]
				result = results[1]
			elif detailsMethod == 'DetailsCopy':
				checkCursor.execute('SELECT schematicName FROM tSchematic WHERE schematicID=%s;', [copyFromSchem])
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
				dbShared.logSchematicEvent(0, galaxy, schematicID, currentUser, 'a', 'Added new schematic {0} using {1}.'.format(schematicName, detailsMethod), 'history')
	else:
		# Update existing schematic
		checkCursor.execute('SELECT enteredBy FROM tSchematic WHERE schematicID=%s', [schematicID])
		checkRow = checkCursor.fetchone()
		if checkRow != None:
			if checkRow[0] == None or checkRow[0] == '':
				errstr = errstr + 'Error: That schematic is part of the core game schematics and cannot be edited.'
			elif checkRow[0] != currentUser and userReputation < ghShared.MIN_REP_VALS['EDIT_OTHER_SCHEMATIC'] and not admin:
				errstr = errstr + 'Error: You do not have high enough reputation to edit other users\' schematic data yet.'
		else:
			errstr = errstr + 'Error: Schematic with that ID could not be found for editing.'

		if errstr == '':
			result = updateSchematic(conn, schematicID, schematic)
			if result.find("Error:") > -1:
				errstr = result
			else:
				dbShared.logSchematicEvent(0, galaxy, schematicID, currentUser, 'e', result, 'history')

	checkCursor.close()

	conn.close()

if errstr != '':
	if (forceOp == 'edit'):
		print('Content-type: text/html\n')
		print(errstr)
	else:
		print('Status: 303 See Other')
		print('Location: /message.py?action=addschematicfail&actionreason=' + urllib.quote_plus(errstr))
		print('')
else:
	if (forceOp == 'edit'):
		print('Content-type: text/html\n')
		print('Schematic saved.')
	else:
		# redirect to new/edited schematic
		print('Status: 303 See Other')
		print('Location: /schematics.py/{0}'.format(schematicID))
		print('')
