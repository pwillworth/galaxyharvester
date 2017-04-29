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
import ghLists
import dbShared
from jinja2 import Environment, FileSystemLoader

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
		galaxy = "14"
else:
	currentUser = ''
	loginResult = form.getfirst('loginAttempt', '')
	sid = form.getfirst('gh_sid', '')
	galaxy = '14'

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

# Allow for specifying galaxy in URL
path = []
if os.environ.has_key('PATH_INFO'):
	path = os.environ['PATH_INFO'].split('/')[1:]
	path = [p for p in path if p != '']

if len(path) > 0 and path[0].isdigit():
	galaxy = dbShared.dbInsertSafe(path[0])
	cookies['galaxy'] = path[0]
	cookies['galaxy']['path'] = '/'
	print cookies

totalAmt = 0.00
conn = dbShared.ghConn()
cursor = conn.cursor()
if (cursor):
	sqlStr = 'SELECT Sum(paymentGross) AS totalAmt FROM tPayments WHERE YEAR(completedDate)=YEAR(NOW()) AND MONTH(completedDate)=MONTH(NOW());'
	cursor.execute(sqlStr)
	row = cursor.fetchone()
	if row[0] != None:
		totalAmt = float(row[0])
cursor.close()
conn.close()

percentOfGoal = totalAmt/20
totalAmt = str(int(totalAmt))
pictureName = dbShared.getUserAttr(currentUser, 'pictureName')
print 'Content-type: text/html\n'
env = Environment(loader=FileSystemLoader('templates'))
env.globals['BASE_SCRIPT_URL'] = ghShared.BASE_SCRIPT_URL
env.globals['MOBILE_PLATFORM'] = ghShared.getMobilePlatform(os.environ['HTTP_USER_AGENT'])
template = env.get_template('home.html')
print template.render(uiTheme=uiTheme, galaxy=galaxy, loggedin=logged_state, currentUser=currentUser, loginResult=loginResult, linkappend=linkappend, url=url, pictureName=pictureName, totalAmt=totalAmt, percentOfGoal=percentOfGoal, imgNum=ghShared.imgNum, resourceGroupListShort=ghLists.getResourceGroupListShort(), professionList=ghLists.getProfessionList(galaxy), planetList=ghLists.getPlanetList(galaxy), resourceGroupList=ghLists.getResourceGroupList(), resourceTypeList=ghLists.getResourceTypeList(), galaxyList=ghLists.getGalaxyList())
