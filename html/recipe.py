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
import cgi
import Cookie
import dbSession
import MySQLdb
import ghShared
import ghNames
import ghObjectRecipe
import ghLists
import dbShared
import resource
import schematics
from jinja2 import Environment, FileSystemLoader


def calcIngredientQuality(conn, spawnID, schematicID, user):
	# Calculate the quality of ingredient resource for schematic
	resQuality = None

	if spawnID != None:
		qualityData = schematics.getQualityData(conn, schematicID)
		qualityResSum = 0
		qualityResCount = 0.0
		spawn = resource.getResource(conn, 1, user, spawnID, None, None)
		for prop in qualityData:
			for item in prop:
				if getattr(spawn.stats, item[0]) != None:
					qualityResCount += item[1]
					qualityResSum += getattr(spawn.stats, item[0])*item[1]
		if qualityResCount > 0:
			resQuality = qualityResSum/qualityResCount
		else:
			resQuality = None
	return resQuality

def main():
	# Get current url
	try:
		url = os.environ['SCRIPT_NAME']
	except KeyError:
		url = ''

	form = cgi.FieldStorage()
	uiTheme = ''
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
		try:
			uiTheme = cookies['uiTheme'].value
		except KeyError:
			uiTheme = ''
		try:
			galaxy = cookies['galaxy'].value
		except KeyError:
			galaxy = form.getfirst('galaxy', ghShared.DEFAULT_GALAXY)
	else:
		currentUser = ''
		loginResult = form.getfirst('loginAttempt', '')
		sid = form.getfirst('gh_sid', '')
		galaxy = form.getfirst('galaxy', ghShared.DEFAULT_GALAXY)

	# escape input to prevent sql injection
	sid = dbShared.dbInsertSafe(sid)

	# Get a session
	logged_state = 0
	linkappend = ''
	disableStr = ''
	if loginResult == None:
		loginResult = 'success'

	sess = dbSession.getSession(sid)
	if (sess != ''):
		logged_state = 1
		currentUser = sess
		if (uiTheme == ''):
			uiTheme = dbShared.getUserAttr(currentUser, 'themeName')
		if (useCookies == 0):
			linkappend = 'gh_sid=' + sid
	else:
		disableStr = ' disabled="disabled"'
		if (uiTheme == ''):
			uiTheme = 'crafter'

	# Get recipe id from path
	path = []
	if os.environ.has_key('PATH_INFO'):
		path = os.environ['PATH_INFO'].split('/')[1:]
		path = [p for p in path if p != '']
	recipeHTML = ''
	slotHTML = ''
	schemImageName = ''
	schematicDetailsHTML = ''
	ingTypes = ''
	ingGroups = ''
	pageType = 'recipe'
	if len(path) > 0:
		recipeID = dbShared.dbInsertSafe(path[0])
		url = url + '/' + recipeID
		r = ghObjectRecipe.schematicRecipe()
		if logged_state == 1:
			# Look up recipe info
			try:
				conn = dbShared.ghConn()
				cursor = conn.cursor()
			except Exception:
				recipeHTML = "Error: could not connect to database"

			if (cursor and recipeID.isdigit()):
				cursor.execute('SELECT recipeID, userID, tRecipe.schematicID, recipeName, (SELECT imageName FROM tSchematicImages si WHERE si.schematicID=tRecipe.schematicID AND si.imageType=1) AS schemImage, schematicName, complexity FROM tRecipe INNER JOIN tSchematic ON tRecipe.schematicID = tSchematic.schematicID WHERE recipeID=' + recipeID + ';')
				row = cursor.fetchone()

				if (row != None):
					if row[1] == currentUser:
						# main recipe data
						if (row[4] != None):
							schemImageName = row[4]
						else:
							schemImageName = 'none.jpg'

						r.recipeID = row[0]
						r.schematicID = row[2]
						r.recipeName = row[3]
						r.schematicImage = schemImageName

						# schematic quality data
						schematicDetailsHTML = '<div><a href="' + ghShared.BASE_SCRIPT_URL + 'schematics.py/' + row[2] + '" title="Go to schematic page.">' + row[5] + '</a></div>'
						schematicDetailsHTML += '<div>Complexity: ' + str(row[6]) + '</div>'
						expGroup = ''
						expProp = ''
						schematicDetailsHTML += '<td valign="top"><h3>Qualities</h3><ul id="qualitiesList" style="margin-top:6px;">'
						expCursor = conn.cursor()
						expCursor.execute('SELECT tSchematicQualities.expQualityID, expProperty, expGroup, statName, statWeight, weightTotal FROM tSchematicQualities INNER JOIN tSchematicResWeights ON tSchematicQualities.expQualityID = tSchematicResWeights.expQualityID WHERE schematicID="' + r.schematicID + '" ORDER BY expGroup, expProperty, statName;')
						expRow = expCursor.fetchone()
						while (expRow != None):
							if (expGroup != expRow[2]):
								tmpName = expRow[2].replace('_',' ')
								schematicDetailsHTML = schematicDetailsHTML + '<li class="groupText">' + tmpName + '</li>'
								expGroup = expRow[2]
							if (expProp != expRow[1]):
								tmpName = expRow[1].replace('_',' ')
								schematicDetailsHTML = schematicDetailsHTML + '<li class="schemQualityProperty altText">' + tmpName + '</li>'
								expProp = expRow[1]

							schematicDetailsHTML += '<li class="schemQualityItem" tag="' + expRow[3] + ':' + str((expRow[4]*1.0/expRow[5])*100) + '"><span class="inlineBlock" style="width:100px;">' + ghNames.getStatName(expRow[3]) + (': </span><span>%.0f' % ((expRow[4]*1.0/expRow[5])*100)) + '%</span></li>'

							expRow = expCursor.fetchone()

						expCursor.close()
						# Look up ingredient data
						ri = None
						sqlStr = 'SELECT si.ingredientName, ingredientResource, ingredientObject, ingredientQuantity, ingredientContribution, rt.containerType tcontainer, rg.containerType gcontainer, rt.resourceTypeName, rg.groupName, ingredientQuality FROM tSchematicIngredients si LEFT JOIN (SELECT ingredientName, ingredientResource, ingredientQuality FROM tRecipeIngredients WHERE recipeID=' + str(r.recipeID) + ') ri ON si.ingredientName = ri.ingredientName LEFT JOIN tResourceType rt ON si.ingredientObject = rt.resourceType LEFT JOIN tResourceGroup rg ON si.ingredientObject = rg.resourceGroup WHERE schematicID="' + r.schematicID + '" ORDER BY ingredientQuantity DESC, si.ingredientName'
						ingCursor = conn.cursor()
						ingCursor.execute(sqlStr)
						ingRow = ingCursor.fetchone()
						while (ingRow != None):
							if ingRow[5] == None:
								if ingRow[6] == None:
									container = 'default'
									objectName = ingRow[2].rpartition('/')[2].replace('_',' ')
									if objectName[-4:] == '.iff':
										objectName = objectName[:-4]
								else:
									ingGroups += '"' + ingRow[2] + '",'
									container = ingRow[6]
									objectName = ingRow[8]
							else:
								ingTypes += '"' + ingRow[2] + '",'
								container = ingRow[5]
								objectName = ingRow[7]

							# get details of ingredient resource for schematic
							resDetails = ''
							if ingRow[1] != None and (ingRow[5] != None or ingRow[6] != None):
								spawn = resource.getResource(conn, logged_state, currentUser, ingRow[1], None, None)
								resDetails = 'Loaded with: ' + spawn.spawnName + ', ' + spawn.resourceTypeName + '<br />' + spawn.getStatList()
							r.recipeIngredients.append(ghObjectRecipe.recipeIngredient(ingRow[2], ingRow[1], ingRow[0], ingRow[3], container, objectName, ingRow[9], resDetails))
							ingRow = ingCursor.fetchone()

						ingCursor.close()
						if ingTypes != '':
							ingTypes = ingTypes[:-1]
						if ingGroups != '':
							ingGroups = ingGroups[:-1]
						slotHTML = r.getIngredientSlots()
					else:
						recipeHTML = "That is not your recipe."
				else:
					recipeHTML = "The recipe ID given could not be found."
				cursor.close()
			else:
				# Render recipe home if any non number in sub path
				pageType = 'home'

			conn.close()
		else:
			recipeHTML = "You must be logged in to manage recipes."
	else:
		recipeHTML = 'You have not specified a recipe to edit, would you like to create a new one?<div style="float:right;"><button type=button value="New Recipe" class="ghButton" onclick="addRecipe();">New Recipe</button></div>'

	pictureName = dbShared.getUserAttr(currentUser, 'pictureName')
	print 'Content-type: text/html\n'
	env = Environment(loader=FileSystemLoader('templates'))
	env.globals['BASE_SCRIPT_URL'] = ghShared.BASE_SCRIPT_URL
	env.globals['MOBILE_PLATFORM'] = ghShared.getMobilePlatform(os.environ['HTTP_USER_AGENT'])
	template = env.get_template('recipe.html')
	print template.render(uiTheme=uiTheme, loggedin=logged_state, currentUser=currentUser, loginResult=loginResult, linkappend=linkappend, url=url, pictureName=pictureName, imgNum=ghShared.imgNum, galaxyList=ghLists.getGalaxyList(), professionList=ghLists.getProfessionList(galaxy), recipeHTML=recipeHTML, slotHTML=slotHTML, schematicDetailsHTML=schematicDetailsHTML, ingTypes=ingTypes, ingGroups=ingGroups, pageType=pageType, recipeID=r.recipeID, recipeName=r.recipeName, schemImageName=schemImageName)


if __name__ == "__main__":
	main()
