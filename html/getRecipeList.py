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
import dbShared
import cgi
import Cookie
import MySQLdb
import ghShared
import dbShared
import dbSession
import ghObjectRecipe
import resource
import recipe


def buildBestRecipe(conn, schem, inventory, user):
	#sys.stderr.write(str(schem) + '\n')
	r = ghObjectRecipe.schematicRecipe()
	r.schematicID = schem[0]
	r.recipeName = schem[4]
	if schem[5] != None:
		r.schematicImage = schem[5]
	# Look up the schematic ingredients
	oingSql = 'SELECT ingredientObject, Sum(ingredientContribution) FROM tSchematicIngredients WHERE schematicID="' + schem[0] + '" AND ingredientType = 0 GROUP BY ingredientObject;'
	oingCursor = conn.cursor()
	oingCursor.execute(oingSql)
	# Find other potential ingredients and their quality from inventory
	filledIng = True
	oingRow = oingCursor.fetchone()
	ingredients = []
	while oingRow != None and oingRow[0] != None:
		thisFilled = False
		# Iterate over the option for each ingredient and save top quality to new list
		for resType in inventory.iterkeys():
			if str(resType).find('\'' + oingRow[0] + '\'') > -1:
				thisFilled = True
				spawns = inventory[resType].split()
				for s in spawns:
					spawnQuality = recipe.calcIngredientQuality(conn, s.split('|')[0].strip(','), schem[0], user)
					ingredients.append((oingRow[0], s, spawnQuality))
		if thisFilled == False:
			filledIng = False
			break
		oingRow = oingCursor.fetchone()

	oingCursor.close()
	oingRow = None
	# If all ingredients can be found in inventory
	if filledIng:
		# Add the top quality scores found from sorted lists as new suggestion
		ingredients = sorted(ingredients, key=lambda ing: ing[2], reverse=True)
		cingSql = 'SELECT si.ingredientName, ingredientObject, ingredientQuantity, ingredientContribution, rt.containerType tcontainer, rg.containerType gcontainer, rt.resourceTypeName, rg.groupName FROM tSchematicIngredients si LEFT JOIN tResourceType rt ON si.ingredientObject = rt.resourceType LEFT JOIN tResourceGroup rg ON si.ingredientObject = rg.resourceGroup WHERE schematicID="' + r.schematicID + '" ORDER BY ingredientQuantity DESC, si.ingredientName'
		cingCursor = conn.cursor()
		cingCursor.execute(cingSql)
		cingRow = cingCursor.fetchone()
		while (cingRow != None):
			for ing in ingredients:
				if ing[0] == cingRow[1]:
					# get details of ingredient resource and add to recipe
					if cingRow[4] == None:
						if cingRow[5] == None:
							container = 'default'
							objectName = cingRow[1].rpartition('/')[2].replace('_',' ')
							if objectName[-4:] == '.iff':
								objectName = objectName[:-4]
						else:
							container = cingRow[5]
							objectName = cingRow[7]
					else:
						container = cingRow[4]
						objectName = cingRow[6]

					resDetails = ''
					spawn = resource.getResource(conn, 1, user, ing[1].split('|')[0].strip(','), None, None)
					resDetails = 'Loaded with: ' + spawn.spawnName + ', ' + spawn.resourceTypeName + '<br />' + spawn.getStatList()
					r.recipeIngredients.append(ghObjectRecipe.recipeIngredient(cingRow[1], ing[1].split('|')[0].strip(','), cingRow[0], cingRow[2], container, objectName, ing[2], resDetails))
					break

			cingRow = cingCursor.fetchone()
		cingCursor.close()
	return r

def getSuggestedRecipes(conn, user, galaxy, prof):
	# Return array of recipe objects suggested based on inventory
	recipes = []
	inventory = {}
	usedSchems = ''
	# Get a dictionary of inventory resType = spawnName,spawnName,spawnName
	cursor = conn.cursor()
	if (cursor):
		sqlStr1 = 'SELECT spawnID, spawnName, tResources.resourceType,'
		sqlStr1 += ' CR, CD, DR, FL, HR, MA, PE, OQ, SR, UT, ER,'
		sqlStr1 += ' units, (SELECT GROUP_CONCAT(resourceGroup SEPARATOR "\',\'") FROM tResourceTypeGroup rtg WHERE rtg.resourceType=tResources.resourceType) FROM tResources INNER JOIN tFavorites ON tResources.spawnID = tFavorites.itemID WHERE userID="' + user + '" AND favType=1 AND tResources.galaxy=' + galaxy + ' ORDER BY tResources.resourceType;'
		cursor.execute(sqlStr1)
		row = cursor.fetchone()
		while row != None:
			inventory['\'' + row[2] + '\',\'' + row[15] + '\''] = inventory.get('\'' + row[2] + '\',' + row[15], '') + ',' + str(row[0]) + '|CR' + str(row[3]) + '|CD' + str(row[4]) + '|DR' + str(row[5]) + '|FL' + str(row[6]) + '|HR' + str(row[7]) + '|MA' + str(row[8]) + '|PE' + str(row[9]) + '|OQ' + str(row[10]) + '|SR' + str(row[11]) + '|UT' + str(row[12]) + '|ER' + str(row[13])
			row = cursor.fetchone()
		cursor.close()
	# Iterate over inventory dict
	for resType in inventory.iterkeys():
		spawns = inventory[resType].split()
		schems = []
		# Select schematics where ingredient in type or groups of type
		sqlStr2 = 'SELECT tSchematic.schematicID, ingredientObject, Sum(ingredientContribution), schematicName, (SELECT imageName FROM tSchematicImages tsi WHERE tsi.schematicID=tSchematic.schematicID AND tsi.imageType=1) AS schemImage FROM tSchematicIngredients INNER JOIN tSchematic ON tSchematicIngredients.schematicID = tSchematic.schematicID INNER JOIN tSkillGroup ON tSchematic.skillGroup = tSkillGroup.skillGroup WHERE profID=' + prof + ' AND ingredientObject IN (' + str(resType) + ') GROUP BY tSchematic.schematicID, ingredientObject, ingredientQuantity, ingredientName ORDER BY tSchematic.schematicID, ingredientQuantity DESC, ingredientName;'
		ingCursor = conn.cursor()
		ingCursor.execute(sqlStr2)
		ingRow = ingCursor.fetchone()
		# Iterate over ingredients of matching schematics
		while ingRow != None:
			for s in spawns:
				spawnQuality = recipe.calcIngredientQuality(conn, s.split('|')[0].strip(','), ingRow[0], user)
				# Add to list of top quality spawn to ingredient with schemID
				schems.append((ingRow[0], ingRow[1], s, spawnQuality, ingRow[3], ingRow[4]))
			ingRow = ingCursor.fetchone()
		ingCursor.close()
		schems = sorted(schems, key=lambda schem: schem[3], reverse=True)
		# Iterate over sorted list of ingredient qualities
		for schem in schems:
			if usedSchems.find(',' + schem[0]) == -1 and spawnQuality > 0:
				r = buildBestRecipe(conn, schem, inventory, user)
				if r.getAverageQuality() > 100:
					recipes.append(r)
					usedSchems += ',' + r.schematicID

	recipes.sort(key=lambda recipe: recipe.getAverageQuality(), reverse=True)
	return recipes

def main():
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
			sid = cookies['gh_sid'].value
		except KeyError:
			sid = form.getfirst('gh_sid', '')
	else:
		currentUser = ''
		sid = form.getfirst('gh_sid', '')

	listFormat = form.getfirst('listFormat', '')
	listType = form.getfirst('listType', '')
	galaxy = form.getfirst('galaxy', '')
	profession = form.getfirst('profession', '')

	# Get a session
	logged_state = 0

	sess = dbSession.getSession(sid)
	if (sess != ''):
		logged_state = 1
		currentUser = sess

	# Main program
	errstr = ''
	tmpStr = ''
	profFilter = ''

	if not galaxy.isdigit():
		errstr = 'Error: You must provide a valid galaxy id.'
	if profession != '' and not profession.isdigit():
		errstr = 'Error: That is not a valid profession id.'
	if logged_state != 1:
		errstr = 'Error: You must be logged in to get your recipe list.'

	conn = dbShared.ghConn()
	cursor = conn.cursor()
	if (cursor and errstr == ''):
		headStr = '<table width="100%">'
		if listType == 'suggest':
			rl = getSuggestedRecipes(conn, currentUser, galaxy, profession)
			if len(rl) > 0:
				for r in rl:
					tmpStr += r.getRow(listType)
			else:
				tmpStr = '<tr><td>No suggestions at this time.  Try adding more to your inventory.</td></tr>'
		else:
			if profession.isdigit() and profession != '0':
				profFilter = ' AND profID={0}'.format(profession)
			sqlStr = 'SELECT recipeID, userID, tRecipe.schematicID, recipeName, (SELECT imageName FROM tSchematicImages img WHERE img.schematicID=tRecipe.schematicID AND img.imageType=1) AS schemImage FROM tRecipe INNER JOIN tSchematic ON tRecipe.schematicID = tSchematic.schematicID LEFT JOIN tSkillGroup ON tSchematic.skillGroup = tSkillGroup.skillGroup WHERE userID="' + currentUser + '" AND (tRecipe.galaxy=' + str(galaxy) + ' OR tRecipe.galaxy IS NULL)' + profFilter + ' ORDER BY recipeName;'
			sys.stderr.write(sqlStr)
			cursor.execute(sqlStr)
			row = cursor.fetchone()

			while (row != None):
				if (row[4] != None):
					schemImageName = row[4]
				else:
					schemImageName = 'none.jpg'
				r = ghObjectRecipe.schematicRecipe()
				r.recipeID = row[0]
				r.schematicID = row[2]
				r.recipeName = row[3]
				r.schematicImage = schemImageName
				sqlStr = 'SELECT si.ingredientName, ingredientResource, ingredientObject, ingredientContribution, ingredientQuality FROM tSchematicIngredients si LEFT JOIN (SELECT ingredientName, ingredientResource, ingredientQuality FROM tRecipeIngredients WHERE recipeID=' + str(r.recipeID) + ') ri ON si.ingredientName = ri.ingredientName WHERE schematicID="' + r.schematicID + '" and ingredientType = 0 ORDER BY ingredientQuantity DESC, si.ingredientName;'
				ingCursor = conn.cursor()
				ingCursor.execute(sqlStr)
				ingRow = ingCursor.fetchone()
				while (ingRow != None):
					ri = ghObjectRecipe.recipeIngredient()
					ri.ingredientObject = ingRow[2]
					ri.ingredientResource = ingRow[1]
					ri.ingredientName = ingRow[0]
					ri.ingredientAmount = ingRow[3]
					ri.resourceQuality = ingRow[4]
					r.recipeIngredients.append(ri)
					ingRow = ingCursor.fetchone()

				ingCursor.close()
				tmpStr += r.getRow('normal',sid)

				row = cursor.fetchone()

		tmpStr = headStr + tmpStr + '</table>'

		cursor.close()
	conn.close()

	print 'Content-type: text/html\n'
	print tmpStr


if __name__ == "__main__":
	main()
