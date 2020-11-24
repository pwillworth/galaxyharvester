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
import cgi
from http import cookies
import pymysql
import dbSession
import dbShared
import re

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

uiTheme = form.getfirst('uiTheme', '')
inGameInfo = form.getfirst('inGameInfo', '')
defaultAlerts = form.getfirst('defaultAlerts', '')
sharedInventory = form.getfirst('sharedInventory', '0')
sharedRecipes = form.getfirst('sharedRecipes', '0')
# escape input to prevent sql injection
sid = dbShared.dbInsertSafe(sid)
uiTheme = dbShared.dbInsertSafe(uiTheme)
inGameInfo = dbShared.dbInsertSafe(inGameInfo)
# Get a session
logged_state = 0
linkappend = ''

sess = dbSession.getSession(sid)
if (sess != ''):
	logged_state = 1
	currentUser = sess
	if (useCookies == 0):
		linkappend = 'gh_sid=' + sid

#  Check for errors
errstr=''
if (len(uiTheme) < 1):
	errstr = errstr + "That is not a valid theme. \r\n"
if (logged_state == 0):
	errstr = errstr + "You must be logged in to update your theme. \r\n"
if len(inGameInfo) > 255:
    errstr = errstr + "Error: game info is too large (255 characters or less allowed)."
if re.search('[><&]', inGameInfo):
    errstr = errstr + "Error: game info contains illegal characters (no HTML allowed)."
if defaultAlerts.isdigit() == False:
    errstr = errstr + "Error: Default alerts invalid or not passed."
if sharedInventory.isdigit() == False:
	errstr = errstr + "Error: Shared Inventory invalid or not passed."
if sharedRecipes.isdigit() == False:
	errstr = errstr + "Error: Shared Recipes invalid or not passed."
if (errstr != ''):
	result = "Your other info could not be updated because of the following errors:\r\n" + errstr
else:
	conn = dbShared.ghConn()
	cursor = conn.cursor()
	cursor.execute("UPDATE tUsers SET themeName='{0}', inGameInfo='{1}', defaultAlertTypes={2}, sharedInventory={3}, sharedRecipes={4} WHERE userID='{5}';".format(uiTheme, inGameInfo, defaultAlerts, sharedInventory, sharedRecipes, currentUser))

	cursor.close()
	conn.close()
	result = "Other Info Updated"

	if useCookies:
		C['uiTheme'] = uiTheme
		C['uiTheme']['max-age'] = (86400 * 7)
		print(C)

print("Content-Type: text/html\n")
print(result)
