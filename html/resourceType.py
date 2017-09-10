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
import dbShared
import MySQLdb
import ghShared
import ghLists
from jinja2 import Environment, FileSystemLoader

def z2b(inVal):
	if inVal == 0:
		return ''
	else:
		return str(inVal)

def main():
	resHTML = '<h2>That resource type does not exist</h2>'
	resHistory = ''
	useCookies = 1
	linkappend = ''
	logged_state = 0
	currentUser = ''
	typeGroup = 'type'
	typeID = ''
	typeName = ''
	uiTheme = ''
	# Get current url
	try:
		url = os.environ['SCRIPT_NAME']
	except KeyError:
		url = ''

	form = cgi.FieldStorage()
	# Get Cookies

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
		loginResult = form.getfirst('loginAttempt', '')
		sid = form.getfirst('gh_sid', '')
		galaxy = form.getfirst('galaxy', ghShared.DEFAULT_GALAXY)

	# escape input to prevent sql injection
	sid = dbShared.dbInsertSafe(sid)

	# Get a session

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
		if (uiTheme == ''):
			uiTheme = 'crafter'

	path = ['']
	if os.environ.has_key('PATH_INFO'):
		path = os.environ['PATH_INFO'].split('/')[1:]
		path = [p for p in path if p != '']

	if path[0] != '':
		typeID = dbShared.dbInsertSafe(path[0])

		try:
			conn = dbShared.ghConn()
			cursor = conn.cursor()
		except Exception:
			errorstr = "Error: could not connect to database"

		if (cursor):
			cursor.execute('SELECT resourceTypeName, rg1.groupName, rg2.groupName, rt.containerType, CRmin, CRmax, CDmin, CDmax, DRmin, DRmax, FLmin, FLmax, HRmin, HRmax, MAmin, MAmax, PEmin, PEmax, OQmin, OQmax, SRmin, SRmax, UTmin, UTmax, ERmin, ERmax, rt.resourceCategory, rt.resourceGroup FROM tResourceType rt INNER JOIN tResourceGroup rg1 ON rt.resourceCategory = rg1.resourceGroup INNER JOIN tResourceGroup rg2 ON rt.resourceGroup = rg2.resourceGroup WHERE resourceType="' + typeID + '";')
			row = cursor.fetchone()
			if (row != None):
				typeName = row[0]
			else:
				# look up group info if not found as a type
				typeGroup = 'group'
				cursor.execute('SELECT groupName, (SELECT rg.groupName FROM tResourceGroupCategory rgc INNER JOIN tResourceGroup rg ON rgc.resourceCategory = rg.resourceGroup WHERE rgc.resourceGroup=tResourceGroup.resourceGroup AND rg.groupLevel = tResourceGroup.groupLevel -1) AS resCat, "" AS resourceGroup, Max(tResourceType.containerType) AS contType, Min(CRmin), Max(CRmax), Min(CDmin), Max(CDmax), Min(DRmin), Max(DRmax), Min(FLmin), Max(FLmax), Min(HRmin), Max(HRmax), Min(MAmin), Max(MAmax), Min(PEmin), Max(PEmax), Min(OQmin), Max(OQmax), Min(SRmin), Max(SRmax), Min(UTmin), Max(UTmax), Min(ERmin), Max(ERmax), (SELECT rgc.resourceCategory FROM tResourceGroupCategory rgc INNER JOIN tResourceGroup rg ON rgc.resourceCategory = rg.resourceGroup WHERE rgc.resourceGroup=tResourceGroup.resourceGroup AND rg.groupLevel = tResourceGroup.groupLevel -1) AS catID FROM tResourceGroup, tResourceType WHERE tResourceGroup.resourceGroup="' + typeID + '" AND tResourceType.resourceType IN (SELECT resourceType FROM tResourceTypeGroup WHERE resourceGroup="' + typeID + '" GROUP BY resourceType);')
				row = cursor.fetchone()
				if (row != None):
					typeName = row[0]
				else:
					typeGroup = ''

			favHTML = ''
			if logged_state > 0:
				favCursor = conn.cursor()
				favSQL = ''.join(('SELECT itemID FROM tFavorites WHERE favType=2 AND userID="', currentUser, '" AND favGroup="', typeID, '" AND galaxy=', galaxy))
				favCursor.execute(favSQL)
				favRow = favCursor.fetchone()
				if favRow != None:
					favHTML = '  <div class="inlineBlock" style="width:3%;float:left;"><a alt="Favorite" title="Favorite" style="cursor: pointer;" onclick="toggleFavorite(this, 2, \''+ typeID +'\', $(\'#galaxySel\').val());"><img src="/images/favorite16On.png" /></a></div>'
				else:
					favHTML = '  <div class="inlineBlock" style="width:3%;float:left;"><a alt="Favorite" title="Favorite" style="cursor: pointer;" onclick="toggleFavorite(this, 2, \''+ typeID +'\', $(\'#galaxySel\').val());"><img src="/images/favorite16Off.png" /></a></div>'
				favCursor.close()

			if typeName != '' and typeName != None:
				resHTML = '<div style="font-size:16px;font-weight:bold;">' + favHTML + typeName

				if row != None and row[3] != None:
					if row[1] != typeName:
						resHTML += '<div style="float:right;"><img src="/images/resources/'+row[3]+'.png" /></div></div>'
					else:
						resHTML += '</div>'
					# breadcrumb to resource type if not top level category
					if row[1] != typeName:
						resHTML += '<h3 style="margin-bottom:12px;">'
						if row[26] != 'resource':
							resHTML += '<a href="' + ghShared.BASE_SCRIPT_URL + 'resourceType.py/' + str(row[26]) + '">' + str(row[1]) + '</a>'
						else:
							resHTML += row[1]
						if typeGroup == 'type':
							resHTML += ' > <a href="' + ghShared.BASE_SCRIPT_URL + 'resourceType.py/' + row[27] + '">' + row[2] + '</a>'
						resHTML += ' > ' + typeName + '</h3>'
					# min/max stats table
					resHTML += '<table class="resAttr resourceStats"><tr>'
					resHTML += '<td><td class="header"><span>CR</span></td><td class="header"><span>CD</span></td><td class="header"><span>DR</span></td><td class="header"><span>FL</span></td><td class="header"><span>HR</span></td><td class="header"><span>MA</span></td><td class="header"><span>PE</span></td><td class="header"><span>OQ</span></td><td class="header"><span>SR</span></td><td class="header"><span>UT</span></td><td class="header"><span>ER</span></td></tr>'
					resHTML += '<tr><td class="header">Min</td><td>' + z2b(row[4]) + '</td><td>' + z2b(row[6]) + '</td><td>' + z2b(row[8]) + '</td><td>' + z2b(row[10]) + '</td><td>' + z2b(row[12]) + '</td><td>' + z2b(row[14]) + '</td><td>' + z2b(row[16]) + '</td><td>' + z2b(row[18]) + '</td><td>' + z2b(row[20]) + '</td><td>' + z2b(row[22]) + '</td><td>' + z2b(row[24]) + '</td></tr>'
					resHTML += '<tr><td class="header">Max</td><td>' + z2b(row[5]) + '</td><td>' + z2b(row[7]) + '</td><td>' + z2b(row[9]) + '</td><td>' + z2b(row[11]) + '</td><td>' + z2b(row[13]) + '</td><td>' + z2b(row[15]) + '</td><td>' + z2b(row[17]) + '</td><td>' + z2b(row[19]) + '</td><td>' + z2b(row[21]) + '</td><td>' + z2b(row[23]) + '</td><td>' + z2b(row[25]) + '</td></tr>'
					resHTML += '</table>'
				else:
					resHTML += '</div>'

			cursor.close()
		conn.close()
	else:
		resHTML = '<h1>Resource Type Groups</h1>'
		resHTML += '<div id="resTypeInfo">You have reached the resource type page.  From here, you can browse to any resource type and view things like: best spawns, schematics, creatures, and min/max stats.</div>'

	creature = max([typeID.find('bone_'), typeID.find('hide_'), typeID.find('meat_'), typeID.find('milk_')])
	if typeID == '':
		# Print the plain group list for pre-IE9 because it does not support rotate css
		tmpAgent = os.environ.get("HTTP_USER_AGENT", "unknown")
		if tmpAgent == 'unknown' or (tmpAgent.find("IE") > -1 and tmpAgent.find("MSIE 9.0") == -1):
			resTree = getResourceGroupsPlain()
		else:
			resTree = getResourceTree()
	else:
		resTree = ''
	pictureName = dbShared.getUserAttr(currentUser, 'pictureName')
	# Get reputation to determine editing abilities
	stats = dbShared.getUserStats(currentUser, galaxy).split(",")
	userReputation = int(stats[2])
	print 'Content-type: text/html\n'
	env = Environment(loader=FileSystemLoader('templates'))
	env.globals['BASE_SCRIPT_URL'] = ghShared.BASE_SCRIPT_URL
	env.globals['MOBILE_PLATFORM'] = ghShared.getMobilePlatform(os.environ['HTTP_USER_AGENT'])
	template = env.get_template('resourcetype.html')
	print template.render(uiTheme=uiTheme, loggedin=logged_state, currentUser=currentUser, loginResult=loginResult, linkappend=linkappend, url=url, pictureName=pictureName, imgNum=ghShared.imgNum, galaxyList=ghLists.getGalaxyList(), typeGroup=typeGroup, typeID=typeID, resHTML=resHTML, creature=creature, resTree=resTree, editCreatures=(userReputation>=ghShared.MIN_REP_VALS['ADD_CREATURE']), resourceType=typeID)


def getResourceTree():
	errorstr = ''
	currentLevel = 1
	levelCounter = 0
	currentLevelNodes = ['','','','','','','']
	tmpLeft = 0
	tmpTop = 0
	treeHTML = ''

	try:
		conn = dbShared.ghConn()
		cursor = conn.cursor()
	except Exception:
		errorstr = 'Error: could not connect to database'

	if errorstr == '':
		cursor.execute('SELECT resourceGroup, groupName, groupLevel, groupOrder from tResourceGroup ORDER BY groupOrder;');
		row = cursor.fetchone()
		while (row != None):
			if currentLevel < row[2]:
				levelCounter += 1
			currentLevel = row[2]
			tmpLeft = ((row[3]-levelCounter-1) * 26) - 30
			tmpTop = ((7 - currentLevel) * 110) + 260

			currentLevelNodes[row[2]-1] = currentLevelNodes[row[2]-1] + '<a href="' + ghShared.BASE_SCRIPT_URL + 'resourceType.py/' + row[0] + '"><div class="inlineBlock resTreeItem" style="left:' + str(tmpLeft) + 'px;top:' + str(tmpTop) + 'px;">' + row[1] + '</div></a>'
			row = cursor.fetchone()

		cursor.close()

	conn.close()

	currentLevelNodes = currentLevelNodes[1:]
	for level in currentLevelNodes:
		treeHTML = '<div>' + level + '</div>' + treeHTML

	return '<div style="height:1500px;"><div id="resourceTree">' + treeHTML + '</div></div>'

def getResourceGroupsPlain():
	treeHTML = ''
	treeHTML += '<h2><a href="' + ghShared.BASE_SCRIPT_URL + 'resourceType.py/organic">Organic</a></h2>'
	treeHTML += '<h3 style="margin-left:20px;"><a href="' + ghShared.BASE_SCRIPT_URL + 'resourceType.py/creature_food">Creature Food</a></h3>'
	treeHTML += '<div style="margin-left:40px;"><a href="' + ghShared.BASE_SCRIPT_URL + 'resourceType.py/milk">Milk</a> (<a href="' + ghShared.BASE_SCRIPT_URL + 'resourceType.py/milk_domesticated">Domesticated</a>|<a href="' + ghShared.BASE_SCRIPT_URL + 'resourceType.py/milk_wild">Wild</a>)</div>'
	treeHTML += '<div style="margin-left:40px;"><a href="' + ghShared.BASE_SCRIPT_URL + 'resourceType.py/meat">Meat</a> (<a href="' + ghShared.BASE_SCRIPT_URL + 'resourceType.py/meat_domesticated">Domesticated</a>|<a href="' + ghShared.BASE_SCRIPT_URL + 'resourceType.py/meat_wild">Wild</a>|<a href="' + ghShared.BASE_SCRIPT_URL + 'resourceType.py/meat_herbivore">Herbivore</a>|<a href="' + ghShared.BASE_SCRIPT_URL + 'resourceType.py/meat_carnivore">Carnivore</a>|<a href="' + ghShared.BASE_SCRIPT_URL + 'resourceType.py/meat_reptillian">Reptillian</a>|<a href="' + ghShared.BASE_SCRIPT_URL + 'resourceType.py/meat_avian">Avian</a>|<a href="' + ghShared.BASE_SCRIPT_URL + 'resourceType.py/meat_egg">Egg</a>|<a href="' + ghShared.BASE_SCRIPT_URL + 'resourceType.py/meat_insect">Insect</a>)</div>'
	treeHTML += '<div style="margin-left:40px;"><a href="' + ghShared.BASE_SCRIPT_URL + 'resourceType.py/seafood">Seafood</a> (<a href="' + ghShared.BASE_SCRIPT_URL + 'resourceType.py/seafood_fish">Fish</a>|<a href="' + ghShared.BASE_SCRIPT_URL + 'resourceType.py/seafood_crustacean">Crustacean</a>|<a href="' + ghShared.BASE_SCRIPT_URL + 'resourceType.py/seafood_mollusk">Mollusk</a>)</div>'
	treeHTML += '<h3 style="margin-left:20px;"><a href="' + ghShared.BASE_SCRIPT_URL + 'resourceType.py/creature_structural">Creature Structural</a></h3>'
	treeHTML += '<div style="margin-left:40px;"><a href="' + ghShared.BASE_SCRIPT_URL + 'resourceType.py/bone">Bone</a> (<a href="' + ghShared.BASE_SCRIPT_URL + 'resourceType.py/bone_avian">Avian</a>)</div>'
	treeHTML += '<div style="margin-left:40px;"><a href="' + ghShared.BASE_SCRIPT_URL + 'resourceType.py/bone_horn">Horn</a></div>'
	treeHTML += '<div style="margin-left:40px;"><a href="' + ghShared.BASE_SCRIPT_URL + 'resourceType.py/hide">Hide</a> (<a href="' + ghShared.BASE_SCRIPT_URL + 'resourceType.py/hide_wooly">Wooly</a>|<a href="' + ghShared.BASE_SCRIPT_URL + 'resourceType.py/hide_bristley">Bristley</a>|<a href="' + ghShared.BASE_SCRIPT_URL + 'resourceType.py/hide_leathery">Leathery</a>|<a href="' + ghShared.BASE_SCRIPT_URL + 'resourceType.py/hide_scaley">Scaley</a>)</div>'
	treeHTML += '<h3 style="margin-left:20px;"><a href="' + ghShared.BASE_SCRIPT_URL + 'resourceType.py/flora_food">Flora Food</a></h3>'
	treeHTML += '<div style="margin-left:40px;"><a href="' + ghShared.BASE_SCRIPT_URL + 'resourceType.py/cereal">Cereal</a> (<a href="' + ghShared.BASE_SCRIPT_URL + 'resourceType.py/corn">Corn</a>|<a href="' + ghShared.BASE_SCRIPT_URL + 'resourceType.py/rice">Rice</a>|<a href="' + ghShared.BASE_SCRIPT_URL + 'resourceType.py/oats">Oats</a>|<a href="' + ghShared.BASE_SCRIPT_URL + 'resourceType.py/wheat">Wheat</a>)</div>'
	treeHTML += '<div style="margin-left:40px;"><a href="' + ghShared.BASE_SCRIPT_URL + 'resourceType.py/seeds">Seeds</a> (<a href="' + ghShared.BASE_SCRIPT_URL + 'resourceType.py/vegetable">Vegetable</a>|<a href="' + ghShared.BASE_SCRIPT_URL + 'resourceType.py/fruit">Fruit</a>)</div>'
	treeHTML += '<h3 style="margin-left:20px;"><a href="' + ghShared.BASE_SCRIPT_URL + 'resourceType.py/flora_structural">Flora Structural</a></h3>'
	treeHTML += '<div style="margin-left:40px;"><a href="' + ghShared.BASE_SCRIPT_URL + 'resourceType.py/softwood">Soft Wood</a> (<a href="' + ghShared.BASE_SCRIPT_URL + 'resourceType.py/softwood_evergreen">Evergreen</a>)</div>'
	treeHTML += '<div style="margin-left:40px;"><a href="' + ghShared.BASE_SCRIPT_URL + 'resourceType.py/deciduous_wood">Deciduous Wood</a></div>'
	treeHTML += '<h2 style="margin-top:20px;"><a href="' + ghShared.BASE_SCRIPT_URL + 'resourceType.py/inorganic">Inorganic</a></h2>'
	treeHTML += '<h3 style="margin-left:20px;"><a href="' + ghShared.BASE_SCRIPT_URL + 'resourceType.py/chemical">Chemical</a></h3>'
	treeHTML += '<div style="margin-left:40px;"><a href="' + ghShared.BASE_SCRIPT_URL + 'resourceType.py/fuel_petrochem_liquid">Liquid Petrochem Fuel</a></div>'
	treeHTML += '<div style="margin-left:40px;"><a href="' + ghShared.BASE_SCRIPT_URL + 'resourceType.py/petrochem_inert">Inert Petrochemical</a></div>'
	treeHTML += '<div style="margin-left:40px;"><a href="' + ghShared.BASE_SCRIPT_URL + 'resourceType.py/fiberplast">Fiberplast</a></div>'
	treeHTML += '<h3 style="margin-left:20px;"><a href="' + ghShared.BASE_SCRIPT_URL + 'resourceType.py/water">Water</a></h3>'
	treeHTML += '<h3 style="margin-left:20px;"><a href="' + ghShared.BASE_SCRIPT_URL + 'resourceType.py/mineral">Mineral</a></h3>'
	treeHTML += '<div style="margin-left:40px;"><a href="' + ghShared.BASE_SCRIPT_URL + 'resourceType.py/fuel_petrochem_solid">Solid Petrochem Fuel</a></div>'
	treeHTML += '<div style="margin-left:40px;"><a href="' + ghShared.BASE_SCRIPT_URL + 'resourceType.py/radioactive">Radioactive</a></div>'
	treeHTML += '<div style="margin-left:40px;"><a href="' + ghShared.BASE_SCRIPT_URL + 'resourceType.py/metal">Metal</a> (<a href="' + ghShared.BASE_SCRIPT_URL + 'resourceType.py/steel">Steel</a>|<a href="' + ghShared.BASE_SCRIPT_URL + 'resourceType.py/iron">Iron</a>|<a href="' + ghShared.BASE_SCRIPT_URL + 'resourceType.py/aluminum">Aluminum</a>|<a href="' + ghShared.BASE_SCRIPT_URL + 'resourceType.py/copper">Copper</a>)</div>'
	treeHTML += '<div style="margin-left:40px;"><a href="' + ghShared.BASE_SCRIPT_URL + 'resourceType.py/ore">Low-Grade Ore</a> (<a href="' + ghShared.BASE_SCRIPT_URL + 'resourceType.py/ore_extrusive">Extrusive</a>|<a href="' + ghShared.BASE_SCRIPT_URL + 'resourceType.py/ore_intrusive">Intrusive</a>|<a href="' + ghShared.BASE_SCRIPT_URL + 'resourceType.py/ore_carbonate">Carbonate</a>|<a href="' + ghShared.BASE_SCRIPT_URL + 'resourceType.py/ore_siliclastic">Siliclastic</a>)</div>'
	treeHTML += '<div style="margin-left:40px;"><a href="' + ghShared.BASE_SCRIPT_URL + 'resourceType.py/gemstone">Gemstone</a> (<a href="' + ghShared.BASE_SCRIPT_URL + 'resourceType.py/gemstone_armophous">Amorphous</a>|<a href="' + ghShared.BASE_SCRIPT_URL + 'resourceType.py/gemstone_crystalline">Crystalline</a>)</div>'
	treeHTML += '<h3 style="margin-left:20px;"><a href="' + ghShared.BASE_SCRIPT_URL + 'resourceType.py/gas">Gas</a></h3>'
	treeHTML += '<div style="margin-left:40px;"><a href="' + ghShared.BASE_SCRIPT_URL + 'resourceType.py/gas_reactive">Reactive Gas</a></div>'
	treeHTML += '<div style="margin-left:40px;"><a href="' + ghShared.BASE_SCRIPT_URL + 'resourceType.py/gas_inert">Inert Gas</a></div>'
	treeHTML += '<h2 style="margin-top:20px;"><a href="' + ghShared.BASE_SCRIPT_URL + 'resourceType.py/energy">Energy</a></h2>'
	treeHTML += '<h3 style="margin-left:20px;"><a href="' + ghShared.BASE_SCRIPT_URL + 'resourceType.py/energy_renewable_unlimited_wind">Wind Energy</a></h3>'
	treeHTML += '<h3 style="margin-left:20px;"><a href="' + ghShared.BASE_SCRIPT_URL + 'resourceType.py/energy_renewable_unlimited_solar">Solar Energy</a></h3>'
	return treeHTML


if __name__ == "__main__":
	main()
