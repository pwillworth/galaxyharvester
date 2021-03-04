#!/usr/bin/env python3
"""

 Copyright 2021 Paul Willworth <ioscode@gmail.com>

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
import cgi
import pymysql
import re

#
# Favorite Types
# 1 = Resource Spawn
# 2 = Resource Type
# 3 = Profession
# 4 = Schematic

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
itemID = form.getfirst("itemID", "")
favType = form.getfirst("favType", "")
favGroup = form.getfirst("favGroup", "")
itemName = form.getfirst("itemName", "")
galaxyID = form.getfirst("galaxy", "")
operation = form.getfirst("op", "")
units = form.getfirst("units", "")
despawnAlert = form.getfirst("despawnAlert", "")

# escape input to prevent sql injection
sid = dbShared.dbInsertSafe(sid)
itemID = dbShared.dbInsertSafe(itemID)
favType = dbShared.dbInsertSafe(favType)
favGroup = dbShared.dbInsertSafe(favGroup)
itemName = dbShared.dbInsertSafe(itemName)
galaxyID = dbShared.dbInsertSafe(galaxyID)
operation = dbShared.dbInsertSafe(operation)
units = dbShared.dbInsertSafe(units)
despawnAlert = dbShared.dbInsertSafe(despawnAlert)


result = ""
# Get a session
logged_state = 0

sess = dbSession.getSession(sid)
if (sess != ''):
	logged_state = 1
	currentUser = sess

def n2n(inVal):
	if (inVal == "" or inVal == None or inVal == "undefined" or inVal == "None"):
		return "NULL"
	else:
		return str(inVal)

def favoriteExists(conn, user, favType, item, galaxy):
	# galaxy not set for spawn favorites
	galaxyCriteria = ""
	if favType != "1":
		galaxyCriteria = "".join((" AND galaxy=", galaxy))
	# Check if a user has an item as a favorite
	if favType == "2" or favType == "4":
		favSQL = "".join(("SELECT itemID FROM tFavorites WHERE favGroup='", str(item), "' AND userID='", user, "' AND favType=", str(favType), galaxyCriteria, ";"))
	else:
		favSQL = "".join(("SELECT favGroup FROM tFavorites WHERE itemID=", str(item), " AND userID='", user, "' AND favType=", str(favType), galaxyCriteria, ";"))
	cursor = conn.cursor()
	cursor.execute(favSQL)
	row = cursor.fetchone()
	cursor.close()

	return row != None

def addFavorite(conn, user, favType, item, galaxy):
	# Add item to favorites if it's not already added
	if galaxy.isdigit():
		cursor = conn.cursor()
		if favType == "2" or favType == "4":
			tempSQL = "INSERT INTO tFavorites (userID, favType, itemID, favGroup, galaxy) VALUES ('" + user + "', " + str(favType) + ", NULL, '" + item + "', " + str(galaxy) + ");"
		else:
			tempSQL = "INSERT INTO tFavorites (userID, favType, itemID, favGroup, galaxy) VALUES ('" + user + "', " + str(favType) + ", " + str(item) + ", '', " + str(galaxy) + ");"
		cursor.execute(tempSQL)
		result = str(cursor.rowcount)
		cursor.close()
	else:
		result = "Error: Galaxy is required when adding a new favorite. \r\n"

	return result

def removeFavorite(conn, user, favType, item, galaxy):
	# galaxy not set for spawn favorites
	galaxyCriteria = ""
	if favType != "1":
		galaxyCriteria = "".join((" AND galaxy=", galaxy))
	cursor = conn.cursor()
	if favType == "2" or favType == "4":
		tempSQL = "".join(("DELETE FROM tFavorites WHERE favGroup='", str(item), "' AND userID='", user, "' AND favType=", str(favType), galaxyCriteria, ";"))
	else:
		tempSQL = "".join(("DELETE FROM tFavorites WHERE itemID=", str(item), " AND userID='", user, "' AND favType=", str(favType), galaxyCriteria, ";"))
	cursor.execute(tempSQL)
	result = cursor.rowcount
	cursor.close()
	return result

units = units.replace(",","")
#  Check for errors
errstr = ""

if (len(itemID) < 1) and (galaxyID.isdigit() == False or itemName == ""):
	errstr = errstr + "Error: no item ID or galaxy + name provided. \r\n"
if (favType.isdigit() == False):
	errstr = errstr + "Error: no item type provided. \r\n"
if not re.match('^[\w _]+$', favGroup) and favGroup != "":
	errstr = errstr + "Error: group name contains illegal characters (only alpha numeric and spaces or underscores allowed)."
if len(favGroup) > 255:
	errstr = errstr + "Error: Group name must not be longer than 255 characters."
if (units != "" and units.isdigit() == False):
	errstr = errstr + "Error: The value you entered for units contains non-numeric characters."
if (units != "" and units.isdigit() == True):
	try:
		unitsTest = int(units)
		if unitsTest > 2147483648 or unitsTest < -2147483648:
			errstr = errstr + "Error: That value for units is outside the range I can store."
	except:
		errstr = errstr + "Error: The value you entered for units could not be converted to a number."

# Only process if no errors
if (errstr == ""):
	result = ""
	favGroup = favGroup.replace(" ", "_")
	if (logged_state > 0):
		# Find favorite record and update/add as needed
		conn = dbShared.ghConn()
		# Lookup spawn id if we dont have it
		if favType == "1" and itemID.isdigit() == False:
			itemID = str(dbShared.getSpawnID(itemName, galaxyID))
			if itemID == "-1":
				result = "Error: The spawn name you entered cannot be found in this galaxy."

		if itemID != "-1":
			if units != "" or favGroup != "" or despawnAlert != "":
				# Just updating favorite property but make sure its a favorite incase adding despawn or group for first time
				if favoriteExists(conn, currentUser, favType, itemID, galaxyID) != True:
					result = addFavorite(conn, currentUser, favType, itemID, galaxyID)
				if units != "":
					udStr = "units=" + str(units)
				if favGroup != "":
					udStr = "favGroup='" + favGroup + "'"
				if despawnAlert != "":
					udStr = "despawnAlert={0}".format(despawnAlert)

				if (str(result).find("Error:") == -1):
					cursor = conn.cursor()
					tempSQL = "UPDATE tFavorites SET " + udStr + " WHERE itemID=" + itemID + " AND userID='" + currentUser + "' AND favType=" + str(favType) + ";"
					cursor.execute(tempSQL)
					result = "Update complete"
					cursor.close()
			else:
				# Updating Favorite Status

				if favoriteExists(conn, currentUser, favType, itemID, galaxyID):
					if operation != "1":
						# fav exists and not forcing add, must be removing
						remresult = removeFavorite(conn, currentUser, favType, itemID, galaxyID)
						if remresult > 0:
							result = "Favorite removed."
						else:
							result = "Error: Failed to remove favorite, please try again."
					else:
						result = "Error: You already have that resource set as a favorite."
				else:
					# does not exist, adding as new favorite
					addresult = addFavorite(conn, currentUser, favType, itemID, galaxyID)
					if str(result).find("Error:") == -1 and addresult.isdigit() and addresult > '0':
						result = "New favorite added."
					else:
						result = "Error: Failed to add favorite.  " + result

		conn.close()
	else:
		result = "Error: must be logged in to change favorites"
else:
	result = errstr

print('Content-type: text/html\n')
print(result)

if (result.find("Error:") > -1):
	sys.exit(500)
else:
	sys.exit(200)
