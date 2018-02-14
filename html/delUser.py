#!/usr/bin/python
"""

 Copyright 2018 Paul Willworth <ioscode@gmail.com>

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
import Cookie
import dbSession
import dbShared
import cgi
import MySQLdb
#
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
	sid = form.getfirst('gh_sid', '')

confirm = form.getfirst('confirm', '')
# escape input to prevent sql injection
sid = dbShared.dbInsertSafe(sid)

# Get a session
logged_state = 0

sess = dbSession.getSession(sid)
if (sess != ''):
	logged_state = 1
	currentUser = sess


# Main program
if (logged_state > 0):
	try:
		conn = dbShared.ghConn()
		cursor = conn.cursor()
	except Exception:
		result = "Error: could not connect to database"

	if (cursor):
		# remove it
		if confirm == 'delete':
			cursor.execute("UPDATE tUsers SET userState=3, emailAddress=NULL, userPassword=NULL, pictureName='default.jpg' WHERE userID=%s;", [currentUser])
			affRows = cursor.rowcount
			if affRows > 0:
				result = "User removed."
			else:
				result = "Error: User not found."

			cursor.execute("DELETE FROM tFavorites WHERE userID=%s;", [currentUser])
			cursor.execute("DELETE FROM tRecipeIngredients WHERE recipeID IN (SELECT recipeID FROM tRecipe WHERE userID=%s);", [currentUser])
			cursor.execute("DELETE FROM tRecipe WHERE userID=%s;", [currentUser])
			cursor.execute("DELETE FROM tFilters WHERE userID=%s;", [currentUser])
			cursor.execute("DELETE FROM tUserFriends WHERE userID=%s;", [currentUser])
			cursor.execute("DELETE FROM tGalaxyUser WHERE userID=%s;", [currentUser])
			cursor.execute("DELETE FROM tSessions WHERE userID=%s;", [currentUser])
		else:
			result = "Error: Confirmation text validation failed."

		cursor.close()

	else:
		result = "Error: No data connection"
	conn.close()
else:
	result = "Error: You must be logged in to delete yourself."

print 'Content-type: text/html\n'
print result

if (result.find("Error:") > -1):
	sys.exit(500)
else:
	sys.exit(200)
