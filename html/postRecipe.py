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
import cgi
import MySQLdb
from xml.dom import minidom
import resource
import recipe
#


def n2n(inVal):
	if (inVal == '' or inVal == None or inVal == 'undefined' or inVal == 'None'):
		return 'NULL'
	else:
		return str(inVal)

def addRecipe(conn, schematicID, recipeName, user, galaxy):
	# Add new Recipe
	returnStr = ""
	cursor = conn.cursor()
	chkcursor = conn.cursor()
	# Make sure schematic ID is valid
	tempSQL = "SELECT schematicName FROM tSchematic WHERE schematicID='" + schematicID + "';"
	try:
		chkcursor.execute(tempSQL)
		row = chkcursor.fetchone()
		if row == None:
			returnStr = "Error: That is not a valid schematic."
	except Exception as e:
		returnStr = 'Error: Add Failed.'
		sys.stderr.write(str(e))

	chkcursor.close()

	# insert new recipe
	if (returnStr.find("Error:") == -1):
		tempSQL = "INSERT INTO tRecipe (recipeName, userID, schematicID, galaxy) VALUES ('" + recipeName + "','" + user + "','" + schematicID + "', " + str(galaxy) + ");"
		try:
			cursor.execute(tempSQL)
			result = cursor.rowcount
			if (result < 1):
				returnStr = "Error: recipe not added."
			else:
				returnStr = "Recipe added.ID" + str(cursor.lastrowid)
		except Exception as e:
			returnStr = 'Error: Add Failed.'
			sys.stderr.write(str(e))
	conn.commit()
	cursor.close()
	return returnStr

def updateRecipe(conn, recipeID, newName):
	# Update recipe information
	returnStr = ""
	cursor = conn.cursor()
	tempSQL = "UPDATE tRecipe SET recipeName='" + newName + "' WHERE recipeID=" + str(recipeID) + ";"
	cursor.execute(tempSQL)
	result = cursor.rowcount
	if (result < 1):
		returnStr = "No change in name."
	else:
		returnStr = " Recipe name updated."
	conn.commit()
	cursor.close()
	return returnStr

def deleteRecipe(conn, recipeID, user):
	# Remove recipe
	returnStr = ""
	cursor = conn.cursor()
	tempSQL = "SELECT userID FROM tRecipe WHERE recipeID=" + recipeID + ";"
	cursor.execute(tempSQL)
	row = cursor.fetchone()
	if row != None:
		if row[0] != user:
			returnStr = "Error: You cannot delete that recipe because it is not yours."
		else:
			tempSQL = "DELETE FROM tRecipe WHERE recipeID=" + recipeID + ";"
			cursor.execute(tempSQL)
			tempSQL = "DELETE FROM tRecipeIngredients WHERE recipeID=" + recipeID + ";"
			cursor.execute(tempSQL)
			returnStr = "Recipe deleted."
	else:
		returnStr = "Error: That recipe could not be found."

	cursor.close()
	conn.commit()
	return returnStr

def updateIngredients(conn, recipeID, ingredients, schematicID, user):
	# Update recipe ingredient slots
	returnStr = ""
	cursor = conn.cursor()
	ingredients = ingredients.split(",")
	ingredientsUpdated = 0
	ingredientNames = ""

	for ingredient in ingredients:
		if ingredient != "" and ingredient != "clear":
			ingredientVals = ingredient.split(":")
			if len(ingredientVals) == 2 and ingredientVals[0] != "" and ingredientVals[1] != "":
				ingredientNames += "'" + ingredientVals[0] + "',"
				ingredientQuality = None
				# See if ingredient slot already exists
				tempSQL = "SELECT ingredientResource FROM tRecipeIngredients WHERE recipeID=" + str(recipeID) + " AND ingredientName='" + ingredientVals[0] + "';"
				cursor.execute(tempSQL)
				row = cursor.fetchone()
				if row != None:
					# Updated existing ingredient slot
					if row[0] != ingredientVals[1]:
						ingredientQuality = recipe.calcIngredientQuality(conn, ingredientVals[1], schematicID, user)
						tempSQL = "UPDATE tRecipeIngredients SET ingredientResource=" + ingredientVals[1] + ", ingredientQuality=" + n2n(ingredientQuality) + " WHERE recipeID=" + str(recipeID) + " AND ingredientName='" + ingredientVals[0] + "';"
						cursor.execute(tempSQL)
						ingredientsUpdated += cursor.rowcount
				else:
					# create new record for ingredient slot
					ingredientQuality = recipe.calcIngredientQuality(conn, ingredientVals[1], schematicID, user)
					tempSQL = "INSERT INTO tRecipeIngredients (recipeID, ingredientName, ingredientResource, ingredientQuality) VALUES (" + str(recipeID) + ",'" + ingredientVals[0] + "'," + str(ingredientVals[1]) + "," + n2n(ingredientQuality) + ");"
					cursor.execute(tempSQL)
					ingredientsUpdated += cursor.rowcount
	# Delete any ingredients that were not included in the current list
	ingredientNames += "''"
	tempSQL = "DELETE FROM tRecipeIngredients WHERE recipeID=" + str(recipeID) + " AND ingredientName NOT IN (" + ingredientNames + ");"
	cursor.execute(tempSQL)
	ingredientsDeleted = cursor.rowcount

	returnStr = " Updated " + str(ingredientsUpdated) + " ingredient slots."
	if ingredientsDeleted > 0:
		returnStr += " Cleared " + str(ingredientsDeleted) + " ingredient slots."

	conn.commit()
	cursor.close()
	return returnStr

def addIngredient(conn, recipeID, spawnID, schematicID, user):
	# Try to add a spawn to an available ingredient slot
	returnStr = ""
	filledCandidates = 0
	ingredientsUpdated = 0
	s = resource.getResource(conn, 1, user, spawnID, None, None)
	ingCursor = conn.cursor()
	ingSql = "SELECT si.ingredientName, ingredientObject, ingredientResource FROM tSchematicIngredients si LEFT JOIN (SELECT ingredientName, ingredientResource FROM tRecipeIngredients WHERE recipeID=" + str(recipeID) + ") ri ON si.ingredientName = ri.ingredientName WHERE schematicID='" + schematicID + "' ORDER BY ingredientQuantity DESC, si.ingredientName;"
	ingCursor.execute(ingSql)
	ingRow = ingCursor.fetchone()
	while ingRow != None:
		if s.groupList.find("," + ingRow[1] + ",") > -1:
			if ingRow[2] == None:
				cursor = conn.cursor()
				# create new record for ingredient slot
				ingredientQuality = recipe.calcIngredientQuality(conn, spawnID, schematicID, user)
				tempSQL = "INSERT INTO tRecipeIngredients (recipeID, ingredientName, ingredientResource, ingredientQuality) VALUES (" + str(recipeID) + ",'" + ingRow[0] + "'," + str(spawnID) + "," + n2n(ingredientQuality) + ");"
				cursor.execute(tempSQL)
				ingredientsUpdated += cursor.rowcount
				cursor.close()
			else:
				filledCandidates += 1

		ingRow = ingCursor.fetchone()

	if ingredientsUpdated > 0:
		returnStr = "Added " + s.spawnName + " to " + str(ingredientsUpdated) + " available slot(s)."
	else:
		if filledCandidates > 0:
			returnStr = "Any slots that could take the resource are already filled."
		else:
			returnStr = "That resource cannot be used in any of the slots of that schematic."

	conn.commit()
	ingCursor.close()
	return returnStr


def main():
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
	schematic = form.getfirst("schematic", "")
	recipeName = form.getfirst("recipeName", "")
	recipeID = form.getfirst("recipeID", "")
	ingredients = form.getfirst("ingredients", "")
	operation = form.getfirst("op", "")
	spawnID = form.getfirst("spawnID", "")
	galaxy = form.getfirst("galaxy", "")
	# escape input to prevent sql injection
	sid = dbShared.dbInsertSafe(sid)
	schematic = dbShared.dbInsertSafe(schematic)
	recipeName = dbShared.dbInsertSafe(recipeName)
	recipeID = dbShared.dbInsertSafe(recipeID)
	ingredients = dbShared.dbInsertSafe(ingredients)
	spawnID = dbShared.dbInsertSafe(spawnID)
	galaxy = dbShared.dbInsertSafe(galaxy)

	result = ""
	# Get a session
	logged_state = 0

	sess = dbSession.getSession(sid)
	if (sess != ''):
		logged_state = 1
		currentUser = sess

	#  Check for errors
	errstr = ""
	if recipeName == "" and operation == "":
		errstr = "Error: You must provide a name for the recipe."
	if schematic == "" and recipeID == "":
		errstr = "Error: You must select a schematic to base the recipe on."
	if logged_state != 1:
		errstr = "Error: You must be logged in to do that."
	if galaxy == "" and schematic != "":
		errstr = "Error: You must select a galaxy before creating a recipe."

	# Only process if no errors
	if (errstr == ""):
		result = ""
		if (logged_state > 0):
			conn = dbShared.ghConn()
			if schematic == "":
				#  Make sure user owns recipe
				chkcursor = conn.cursor()
				tempSQL = "".join(("SELECT userID, schematicID FROM tRecipe WHERE recipeID=", recipeID, " AND userID='", currentUser, "';"))
				chkcursor.execute(tempSQL)
				row = chkcursor.fetchone()
				if row != None:
					if operation == "delete":
						result = deleteRecipe(conn, recipeID, currentUser)
					elif operation == "addspawn":
						result = addIngredient(conn, recipeID, spawnID, row[1], currentUser)
					else:
						result = updateRecipe(conn, recipeID, recipeName)
						if ingredients != "":
							result += updateIngredients(conn, recipeID, ingredients, row[1], currentUser)
				else:
					result = "Error: That recipe does not exist or is not yours."
				chkcursor.close()
			else:
				result = addRecipe(conn, schematic, recipeName, currentUser, galaxy)
				tmpPos = result.find("ID")
				# Save and strip ID on successful add
				if tmpPos > -1:
					recipeID = result[tmpPos+2:]
					result = result[:tmpPos]
				# Update ingredients if they were provided (saving suggestion)
				if ingredients != '':
					result += updateIngredients(conn, recipeID, ingredients, schematic, currentUser)
			conn.close()
		else:
			result = "Error: must be logged in to do that."
	else:
		result = errstr

	print 'Content-type: text/xml\n'
	doc = minidom.Document()
	eRoot = doc.createElement("result")
	doc.appendChild(eRoot)

	eName = doc.createElement("recipeID")
	tName = doc.createTextNode(str(recipeID))
	eName.appendChild(tName)
	eRoot.appendChild(eName)
	eText = doc.createElement("resultText")
	tText = doc.createTextNode(result)
	eText.appendChild(tText)
	eRoot.appendChild(eText)
	print doc.toxml()

	if (result.find("Error:") > -1):
		sys.exit(500)
	else:
		sys.exit(200)


if __name__ == "__main__":
	main()
