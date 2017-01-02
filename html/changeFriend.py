#!/usr/bin/python
"""

 Copyright 2010 Paul Willworth <ioscode@gmail.com>

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
import ghNames
#
# Get current url
try:
	url = os.environ['SCRIPT_NAME']
except KeyError:
	url = ''

form = cgi.FieldStorage()
# Get Cookies
errorstr = ''
cookies = Cookie.SimpleCookie()
try:
	cookies.load(os.environ['HTTP_COOKIE'])
except KeyError:
	errorstr = 'no cookies\n'

if errorstr == '':
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


op = form.getfirst('op', '')
friend = form.getfirst('friend', '')
# escape input to prevent sql injection
sid = dbShared.dbInsertSafe(sid)
spawnName = dbShared.dbInsertSafe(op)
galaxy = dbShared.dbInsertSafe(friend)

# Get a session
logged_state = 0
linkappend = ''

sess = dbSession.getSession(sid, 2592000)
if (sess != ''):
	logged_state = 1
	currentUser = sess
	linkappend = 'gh_sid=' + sid

# Main program

print 'Content-type: text/html\n'
if (logged_state > 0):
	try:
		conn = dbShared.ghConn()
		cursor = conn.cursor()
	except Exception:
		result = "Error: could not connect to database"

	if (cursor):
		row = None

		sqlStr = ""
		if (op != '' and friend != ''):
			if (op == "remove"):
				# remove friend
				sqlStr = "DELETE FROM tUserFriends WHERE userID='" + currentUser + "' AND friendID='" + friend + "';"
				result = friend + " removed"
			elif (op == "add"):
				# add friend
				cursor.execute("SELECT added FROM tUserFriends WHERE userID='" + currentUser + "' AND friendID='" + friend + "';")
				row = cursor.fetchone()
				if row == None:
					# insert friend
					sqlStr = "INSERT INTO tUserFriends (userID, friendID, added) VALUES ('" + currentUser + "','" + friend + "',NOW());"
					result = friend + " added"
				else:
					result = friend + " is already on your friends list."

			cursor.execute(sqlStr)

		else:
			result = "Error: You must provide an operation and user id"
		cursor.close()
	else:
		result = "Error: No database connection"
	conn.close()
else:
	result = "Error: You must be logged in to update your friends."

print result
if (result.find("Error:") > -1):
	sys.exit(500)
else:
	sys.exit(200)
