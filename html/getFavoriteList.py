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
import dbShared


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

	# Get form info
	favType = form.getfirst("favType", "")
	galaxy = form.getfirst("galaxy", "")
	# escape input to prevent sql injection
	favType = dbShared.dbInsertSafe(favType)

	# Get a session
	logged_state = 0
	sess = dbSession.getSession(sid, 2592000)
	if (sess != ''):
		logged_state = 1
		currentUser = sess
		if (useCookies == 0):
			linkappend = 'gh_sid=' + sid

	tmpStr = ''
	if galaxy.isdigit():
		galaxyCriteria = ' AND galaxy IN (0, {0})'.format(galaxy)

	if logged_state > 0:
		if favType == 'p':
			sqlStr = ''.join(('SELECT profID, profName, favsgalaxy FROM tProfession LEFT JOIN (SELECT itemID, galaxy AS favsgalaxy FROM tFavorites WHERE favType=3 AND userID="', currentUser, '"', galaxyCriteria, ') favs ON tProfession.profID = favs.itemID WHERE tProfession.craftingQuality>0', galaxyCriteria, ' ORDER BY profName;'))
		elif favType == 's':
			sqlStr = ''.join(('SELECT schematicID, schematicName, tFavorites.galaxy FROM tFavorites INNER JOIN tSchematic ON tFavorites.favGroup = tSchematic.schematicID WHERE tFavorites.userID="', currentUser, '" AND tFavorites.favType=4 ORDER BY schematicName'))
		else:
			sqlStr = ''.join(('SELECT favGroup, CASE WHEN resourceTypeName IS NULL THEN groupName ELSE resourceTypeName END, resourceCategory FROM tFavorites LEFT JOIN tResourceType ON tFavorites.favGroup=tResourceType.resourceType LEFT JOIN tResourceGroup ON tFavorites.favGroup=tResourceGroup.resourceGroup WHERE tFavorites.userID="', currentUser, '" AND tFavorites.favType=2 ORDER BY CASE WHEN tResourceGroup.resourceGroup IS NULL THEN tResourceType.resourceGroup ELSE tResourceGroup.resourceGroup END, resourceType'))
		conn = dbShared.ghConn()
		cursor = conn.cursor()
		if (cursor):
			cursor.execute(sqlStr)
			row = cursor.fetchone()
			tmpStr = '<ul class="plain">'
			while (row != None):
				if row[2] != None:
					if favType == 'p' or favType == 's':
						# Profession and Schematic favorites galaxy specific
						if str(row[2]) == galaxy:
							favImg = '<img src="/images/favorite16On.png" />'
						else:
							favImg = '<img src="/images/favorite16Off.png" />'

					if favType == 'p':
						tmpStr = ''.join((tmpStr, '<div class="inlineBlock profToggle"><div style="width:16px;height:16px;float:left;cursor: pointer;" onclick="toggleFavorite(this, 3, \'', str(row[0]), '\', ', galaxy, ');" title="Click to toggle favorite">', favImg, '</div>', row[1], '</div>'))
					elif favType == 's':
						tmpStr = ''.join((tmpStr, '<div class="schemToggle"><div style="width:16px;height:16px;float:left;cursor: pointer;" onclick="toggleFavorite(this, 3, \'', str(row[0]), '\', ', galaxy, ');" title="Click to toggle favorite">', favImg, '</div><a href="/schematics.py/', row[0], '">', row[1], '</a></div>'))
					else:
						tmpStr = ''.join((tmpStr, '<li>&nbsp;&nbsp;<a href="/resourceType.py/', row[0], '">', str(row[1]), '</a></li>'))
				else:
					if favType == 'p':
						tmpStr = ''.join((tmpStr, '<div class="inlineBlock profToggle"><div style="width:16px;height:16px;float:left;cursor: pointer;" onclick="toggleFavorite(this, 3, \'', str(row[0]), '\', ', galaxy, ');" title="Click to toggle favorite"><img src="/images/favorite16Off.png" /></div>', row[1], '</div>'))
					else:
						tmpStr = ''.join((tmpStr, '<li><span class="bigLink"><a href="/resourceType.py/', row[0], '">', str(row[1]), '</a></span></li>'))
				row = cursor.fetchone()
			tmpStr += '</ul>'
		cursor.close()
		conn.close()
	else:
		tmpStr = 'Error: You must be logged in to get your favorites list.'

	print 'Content-type: text/html\n'
	print tmpStr


if __name__ == "__main__":
	main()
