#!/usr/bin/python
"""

 Copyright 2016 Paul Willworth <ioscode@gmail.com>

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
import ghLists
import ghNames
import dbShared
from jinja2 import Environment, FileSystemLoader
import ghObjectSchematic


def getQualityData(conn, schematicID):
	# get array of schematic quality data
	qualityData = []
	propertyData = []
	expGroup = ''
	expProp = ''

	expCursor = conn.cursor()
	expCursor.execute('SELECT tSchematicQualities.expQualityID, expProperty, expGroup, statName, statWeight, weightTotal FROM tSchematicQualities INNER JOIN tSchematicResWeights ON tSchematicQualities.expQualityID = tSchematicResWeights.expQualityID WHERE schematicID="' + schematicID + '" ORDER BY expGroup, expProperty, statName;')
	expRow = expCursor.fetchone()
	while (expRow != None):
		if (expGroup != expRow[2]):
			expGroup = expRow[2]
		if (expProp != expRow[1]):
			if len(propertyData) > 0:
				qualityData.append(propertyData)
			propertyData = []
			expProp = expRow[1]

		propertyData.append([expRow[3],(expRow[4]*100.0)/(expRow[5]*100.0)])

		expRow = expCursor.fetchone()
	qualityData.append(propertyData)

	expCursor.close()
	return qualityData

# Get a list item for a component ingredient
def getComponentLink(cn, objectPath, ingredientType):
	compCursor = cn.cursor()
	compCursor.execute('SELECT schematicID, schematicName, complexity, xpAmount, (SELECT imageName FROM tSchematicImages tsi WHERE tsi.schematicID=tSchematic.schematicID AND tsi.imageType=1) AS schemImage FROM tSchematic WHERE objectPath="' + objectPath + '" OR objectGroup="' + objectPath + '";')
	compRow = compCursor.fetchone()
	tempStr = ''
	if (compRow != None):
		# use first image for slot
		if (compRow[4] != None):
			schemImageName = compRow[4]
		else:
			schemImageName = 'none.jpg'
		tempStr += '<img src="/images/schematics/' + schemImageName + '" class="schematicIngredient" />'
		tempStr += '</td><td>'
		tempStr += '<div class="schematicIngredient">'
		if ingredientType > 2:
			tempStr += '(Optional) '
		while compRow != None:
			# Add each potential component
			if tempStr.find('href') > -1:
				tempStr += ' or '
			tempStr += '<a href="' + compRow[0] + '">' + compRow[1] + '</a>'
			compRow = compCursor.fetchone()
		tempStr += '</div>'
	else:
		tempStr = '</td><td><div>'
		if ingredientType > 2:
			tempStr += '(Optional) '
		tempStr += objectPath[objectPath.rfind('/')+1:-4].replace('_',' ')
		tempStr += '</div>'

	return tempStr


def main():
	# Get current url
	try:
		url = os.environ['SCRIPT_NAME']
	except KeyError:
		url = ''
	uiTheme = ''
	schematicID = ''
	schemImageAttempt = ''
	schemHTML = '<h2>That schematic does not exist.</h2>'
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
		try:
			uiTheme = cookies['uiTheme'].value
		except KeyError:
			uiTheme = ''
		try:
			schemImageAttempt = cookies['schemImageAttempt'].value
		except KeyError:
			schemImageAttempt = ''
		try:
			galaxy = cookies['galaxy'].value
		except KeyError:
			galaxy = form.getfirst('galaxy', ghShared.DEFAULT_GALAXY)
	else:
		currentUser = ''
		loginResult = form.getfirst('loginAttempt', '')
		sid = form.getfirst('gh_sid', '')
		schemImageAttempt = form.getfirst('schemImageAttempt', '')
		galaxy = form.getfirst('galaxy', ghShared.DEFAULT_GALAXY)

	# escape input to prevent sql injection
	sid = dbShared.dbInsertSafe(sid)
	# Get a session
	logged_state = 0
	linkappend = ''
	disableStr = ''
	if loginResult == None:
		loginResult = 'success'

	sess = dbSession.getSession(sid, 2592000)
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

	path = []
	s = None
	if os.environ.has_key('PATH_INFO'):
		path = os.environ['PATH_INFO'].split('/')[1:]
		path = [p for p in path if p != '']

	favHTML = ''
	if len(path) > 0:
		schematicID = dbShared.dbInsertSafe(path[0])
		url = url + '/' + schematicID
		if (schematicID != 'index') and (schematicID != 'home'):
			# Build the schematic object
			try:
				conn = dbShared.ghConn()
				cursor = conn.cursor()
			except Exception:
				errorstr = "Error: could not connect to database"

			if (cursor):
				cursor.execute('SELECT schematicName, complexity, xpAmount, (SELECT imageName FROM tSchematicImages tsi WHERE tsi.schematicID=tSchematic.schematicID AND tsi.imageType=1) AS schemImage FROM tSchematic WHERE schematicID="' + schematicID + '";')
				row = cursor.fetchone()

				if (row != None):
					# main schematic data
					if (row[3] != None):
						schemImageName = row[3]
					else:
						schemImageName = 'none.jpg'

					s = ghObjectSchematic.schematic()
					s.schematicID = schematicID
					s.schematicName = row[0]
					s.complexity = row[1]
					s.xpAmount = row[2]
					s.schematicImage = schemImageName

					ingCursor = conn.cursor()
					ingCursor.execute('SELECT ingredientName, ingredientType, ingredientObject, ingredientQuantity, res.resName FROM tSchematicIngredients LEFT JOIN (SELECT resourceGroup AS resID, groupName AS resName FROM tResourceGroup UNION ALL SELECT resourceType, resourceTypeName FROM tResourceType) res ON ingredientObject = res.resID WHERE schematicID="' + schematicID + '" ORDER BY ingredientType, ingredientQuantity DESC;')
					ingRow = ingCursor.fetchone()
					while (ingRow != None):
						tmpName = ingRow[2]
						tmpName = tmpName.replace('shared_','')
						if (ingRow[1] == 0):
							# resource
							if (ingRow[4] != None):
								tmpLink = '</td><td><a href="' + ghShared.BASE_SCRIPT_URL + 'resourceType.py/' + ingRow[2] + '">' + ingRow[4] + '</a>'
							else:
								tmpLink = '</td><td><a href="' + ghShared.BASE_SCRIPT_URL + 'resourceType.py/' + ingRow[2] + '">' + ingRow[2] + '</a>'
						else:
							# component
							tmpLink = getComponentLink(conn, tmpName, ingRow[1])

						s.ingredients.append(ghObjectSchematic.schematicIngredient(ingRow[0], ingRow[1], tmpName, ingRow[3], ingRow[4], tmpLink))
						ingRow = ingCursor.fetchone()

					ingCursor.close()

					# schematic quality data
					expGroup = ''
					expProp = ''
					qg = None
					qp = None
					expCursor = conn.cursor()
					expCursor.execute('SELECT tSchematicQualities.expQualityID, expProperty, expGroup, statName, statWeight, weightTotal FROM tSchematicQualities INNER JOIN tSchematicResWeights ON tSchematicQualities.expQualityID = tSchematicResWeights.expQualityID WHERE schematicID="' + schematicID + '" ORDER BY expGroup, expProperty, statName;')
					expRow = expCursor.fetchone()
					while (expRow != None):
						if expRow[1] != expProp:
							if qp != None:
								qg.properties.append(qp)
								qp = None
							qp = ghObjectSchematic.schematicQualityProperty(expRow[1], expRow[5])
							expProp = expRow[1]

						if expRow[2] != expGroup:
							if qg != None:
								s.qualityGroups.append(qg)
								qg = None
							qg = ghObjectSchematic.schematicQualityGroup(expRow[2])
							expGroup = expRow[2]

						sw = ghObjectSchematic.schematicStatWeight(expRow[0], expRow[3], expRow[4], expRow[5])
						qp.statWeights.append(sw)
						expRow = expCursor.fetchone()
					if qp != None:
						qg.properties.append(qp)
					if qg != None:
						s.qualityGroups.append(qg)
					expCursor.close()

					# Get list of schematics this one can be used in
					useCursor = conn.cursor()
					useCursor.execute('SELECT tSchematicIngredients.schematicID, s2.schematicName FROM tSchematicIngredients INNER JOIN tSchematic ON tSchematicIngredients.ingredientObject = tSchematic.objectPath OR tSchematicIngredients.ingredientObject = tSchematic.objectGroup INNER JOIN tSchematic s2 ON tSchematicIngredients.schematicID=s2.schematicID WHERE tSchematic.schematicID = "' + schematicID + '" GROUP BY tSchematicIngredients.schematicID;')
					useRow = useCursor.fetchone()
					while (useRow != None):
						s.schematicsUsedIn.append([useRow[0], useRow[1]])
						useRow = useCursor.fetchone()

					useCursor.close()

					if logged_state > 0:
						favCursor = conn.cursor()
						favSQL = ''.join(('SELECT itemID FROM tFavorites WHERE favType=4 AND userID="', currentUser, '" AND favGroup="', schematicID, '" AND galaxy=', galaxy))
						favCursor.execute(favSQL)
						favRow = favCursor.fetchone()
						if favRow != None:
							favHTML = '  <div class="inlineBlock" style="width:3%;float:left;"><a alt="Favorite" title="Favorite" style="cursor: pointer;" onclick="toggleFavorite(this, 4, \''+ schematicID +'\', $(\'#galaxySel\').val());"><img src="/images/favorite16On.png" /></a></div>'
						else:
							favHTML = '  <div class="inlineBlock" style="width:3%;float:left;"><a alt="Favorite" title="Favorite" style="cursor: pointer;" onclick="toggleFavorite(this, 4, \''+ schematicID +'\', $(\'#galaxySel\').val());"><img src="/images/favorite16Off.png" /></a></div>'
						favCursor.close()

				cursor.close()

			conn.close()

	pictureName = dbShared.getUserAttr(currentUser, 'pictureName')
	print 'Content-type: text/html\n'
	env = Environment(loader=FileSystemLoader('templates'))
	env.globals['BASE_SCRIPT_URL'] = ghShared.BASE_SCRIPT_URL
	env.globals['MOBILE_PLATFORM'] = ghShared.getMobilePlatform(os.environ['HTTP_USER_AGENT'])
	template = env.get_template('schematics.html')
	print template.render(uiTheme=uiTheme, loggedin=logged_state, currentUser=currentUser, loginResult=loginResult, linkappend=linkappend, url=url, pictureName=pictureName, imgNum=ghShared.imgNum, galaxyList=ghLists.getGalaxyList(), professionList=ghLists.getProfessionList(), schematicTabList=ghLists.getSchematicTabList(), objectTypeList=ghLists.getObjectTypeList(), noenergyTypeList=ghLists.getOptionList('SELECT resourceType, resourceTypeName FROM tResourceType WHERE resourceCategory != "energy" ORDER BY resourceTypeName;'), resourceGroupList=ghLists.getResourceGroupList(), schematicID=schematicID, schematic=s, favHTML=favHTML)


if __name__ == "__main__":
	main()
