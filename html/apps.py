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
import sys
import cgi
from http import cookies
import dbSession
import pymysql
import ghShared
import ghLists
import dbShared
from jinja2 import Environment, FileSystemLoader

# Get current url
try:
	url = os.environ['SCRIPT_NAME']
except KeyError:
	url = ''
uiTheme = ''
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
	try:
		uiTheme = C['uiTheme'].value
	except KeyError:
		uiTheme = ''
else:
	currentUser = ''
	loginResult = form.getfirst('loginAttempt', '')
	sid = form.getfirst('gh_sid', '')

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

pictureName = dbShared.getUserAttr(currentUser, 'pictureName')
print('Content-type: text/html\n')
env = Environment(loader=FileSystemLoader('templates'))
env.globals['BASE_SCRIPT_URL'] = ghShared.BASE_SCRIPT_URL
env.globals['MOBILE_PLATFORM'] = ghShared.getMobilePlatform(os.environ['HTTP_USER_AGENT'])
template = env.get_template('apps.html')
print(template.render(uiTheme=uiTheme, loggedin=logged_state, currentUser=currentUser, loginResult=loginResult, linkappend=linkappend, url=url, pictureName=pictureName, imgNum=ghShared.imgNum, galaxyList=ghLists.getGalaxyList(), enableCAPTCHA=ghShared.RECAPTCHA_ENABLED, siteidCAPTCHA=ghShared.RECAPTCHA_SITEID))
