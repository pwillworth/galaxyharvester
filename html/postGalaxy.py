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
import re
from http import cookies
import dbSession
import dbShared
import cgi
import pymysql
import smtplib
from email.message import EmailMessage
from xml.dom import minidom
import ghNames
import ghShared
sys.path.append("../")
import mailInfo

#
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
galaxy = form.getfirst("galaxyID", "")
galaxyName = form.getfirst("galaxyName", "")
galaxyState = form.getfirst("galaxyState", "")
galaxyNGE = form.getfirst("galaxyNGE", "0")
galaxyWebsite = form.getfirst("galaxyWebsite", "")
galaxyPlanets = form.getfirst("galaxyPlanets", "")
galaxyResourceTypes = form.getfirst("galaxyResourceTypes", "")
galaxyAdmins = form.getfirst("galaxyAdmins", "")
# escape input to prevent sql injection
sid = dbShared.dbInsertSafe(sid)
galaxy = dbShared.dbInsertSafe(galaxy)
galaxyName = dbShared.dbInsertSafe(galaxyName)
galaxyState = dbShared.dbInsertSafe(galaxyState)
galaxyNGE = dbShared.dbInsertSafe(galaxyNGE)
galaxyWebsite = dbShared.dbInsertSafe(galaxyWebsite)
galaxyPlanets = dbShared.dbInsertSafe(galaxyPlanets)
galaxyResourceTypes = dbShared.dbInsertSafe(galaxyResourceTypes)
galaxyAdmins = dbShared.dbInsertSafe(galaxyAdmins)

galaxyPlanets = galaxyPlanets.split(",")
galaxyResourceTypes = galaxyResourceTypes.split(",")
galaxyAdmins = galaxyAdmins.split(",")

result = ""
# Get a session
logged_state = 0

sess = dbSession.getSession(sid)
if (sess != ''):
	logged_state = 1
	currentUser = sess

def sendGalaxyNotifyMail(galaxyID, galaxyName, user):
	# send message
	message = EmailMessage()
	message['From'] = "\"Galaxy Harvester Registration\" <admin@galaxyharvester.net>"
	message['To'] = "galaxyharvester@gmail.com"
	message['Subject'] = "New Galaxy Submitted For Review"
	link = "http://galaxyharvester.net/galaxy.py/{0}".format(galaxyID)
	message.set_content(user + " has submitted a new galaxy for review.\n\n" + link)
	message.add_alternative("<div><img src='http://galaxyharvester.net/images/ghLogoLarge.png'/></div><p>" + user + " has submitted a new galaxy for review.</p><p><a style='text-decoration:none;' href='" + link + "'><div style='width:170px;font-size:18px;font-weight:600;color:#feffa1;background-color:#003344;padding:8px;margin:4px;border:1px solid black;'>Click Here To Review</div></a><br/>or copy and paste link: " + link + "</p>", subtype='html')
	mailer = smtplib.SMTP(mailInfo.MAIL_HOST)
	mailer.login(mailInfo.MAIL_USER, mailInfo.MAIL_PASS)
	mailer.send_message(message)
	mailer.quit()
	return 'email sent'

def addGalaxy(galaxyName, galaxyNGE, galaxyWebsite, galaxyPlanets, galaxyResourceTypes, userID, galaxyAdmins):
	# Add new draft galaxy
	returnStr = "Galaxy submit failed."
	result = 0
	conn = dbShared.ghConn()
	cursor = conn.cursor()
	
	tempSQL = "INSERT INTO tGalaxy (galaxyName, galaxyState, galaxyNGE, website, submittedBy) VALUES (%s, %s, %s, %s, %s);"
	try:
		cursor.execute(tempSQL, (galaxyName, 0, galaxyNGE, galaxyWebsite, userID))
		result = cursor.rowcount
	except Exception as e:
		returnStr = 'Error: Add Failed. {0}'.format(e)

	cursor.execute('SELECT LAST_INSERT_ID();')
	row = cursor.fetchone()
	if row != None:
		galaxyID = row[0]
	else:
		galaxyID = 0

	for planet in galaxyPlanets:
		if planet.isdigit():
			cursor.execute("INSERT INTO tGalaxyPlanet (galaxyID, planetID) VALUES (LAST_INSERT_ID(), %s)", [planet])
			result = result + cursor.rowcount

	for resourceType in galaxyResourceTypes:
		if isinstance(resourceType, str) and len(resourceType) > 0:
			cursor.execute('INSERT INTO tGalaxyResourceType (galaxyID, resourceType) VALUES (LAST_INSERT_ID(), %s)', [resourceType])
			result = result + cursor.rowcount

	for user in galaxyAdmins:
		if len(user) > 0:
			cursor.execute("INSERT INTO tGalaxyUser (galaxyID, userID, roleType) VALUES (LAST_INSERT_ID(), %s, %s);", [user, "a"])
			result = result + cursor.rowcount

	if returnStr.find("Error:") == -1 and result > 0:
		sendGalaxyNotifyMail(galaxyID, galaxyName, userID)
		returnStr = "Galaxy submitted for review."
	cursor.close()
	conn.close()
	return returnStr

def updateGalaxy(galaxyID, galaxyName, galaxyState, galaxyNGE, galaxyWebsite, galaxyPlanets, galaxyResourceTypes, galaxyAdmins):
	# Update galaxy information
	returnStr = ""
	result = 0
	conn = dbShared.ghConn()
	cursor = conn.cursor()
	
	tempSQL = "UPDATE tGalaxy SET galaxyName=%s, galaxyState=%s, galaxyNGE=%s, website=%s WHERE galaxyID=%s;"
	cursor.execute(tempSQL, (galaxyName, galaxyState, galaxyNGE, galaxyWebsite, galaxyID))
	result = cursor.rowcount

	cursor.execute("DELETE FROM tGalaxyPlanet WHERE galaxyID=%s;", [galaxyID])
	for planet in galaxyPlanets:
		if planet.isdigit():
			cursor.execute("INSERT INTO tGalaxyPlanet (galaxyID, planetID) VALUES (%s, %s)", [galaxyID, planet])
			result = result + cursor.rowcount

	cursor.execute("DELETE FROM tGalaxyResourceType WHERE galaxyID=%s;", [galaxyID])
	for resourceType in galaxyResourceTypes:
		if isinstance(resourceType, str) and len(resourceType) > 0:
			cursor.execute('INSERT INTO tGalaxyResourceType (galaxyID, resourceType) VALUES (%s, %s)', [galaxyID, resourceType])
			result = result + cursor.rowcount

	cursor.execute("DELETE FROM tGalaxyUser WHERE galaxyID=%s AND roleType='a';", [galaxyID])
	for user in galaxyAdmins:
		if len(user) > 0:
			cursor.execute("INSERT INTO tGalaxyUser (galaxyID, userID, roleType) VALUES (%s, %s, %s);", [galaxyID, user, "a"])
			result = result + cursor.rowcount
	if (result < 1):
		returnStr = "Error: galaxy data not updated."
	else:
		returnStr = " galaxy data updated."

	cursor.close()
	conn.close()
	return returnStr


#  Check for errors
errstr = ""

if not len(galaxyName) > 3:
	errstr = errstr + "Error: You must include the Galaxy name longer than 3 letters. \r\n"
if not len(galaxyWebsite) > 7 or not galaxyWebsite.startswith("http"):
	errstr = errstr + "Error: You must include a valid website so public server access can be verified.\r\n"
if (len(galaxy) > 0 and galaxy != 'new' and galaxy.isdigit() != True):
	errstr = errstr + "Error: Galaxy ID was not a valid number.\n"
if len(galaxy) > 0 and galaxy != 'new' and galaxyState.isdigit() != True:
	errstr = errstr + "Error: Galaxy State was not a valid number.\n"

if galaxyNGE == '1' or galaxyNGE == 'checked':
	galaxyNGE = 1
else:
	galaxyNGE = 0

# Only process if no errors or just verifying
if (errstr == ""):
	result = ""
	if (logged_state > 0):
		# Edit existing galaxy info or submit new draft
		if len(galaxy) > 0 and galaxy != 'new':
			# check owner
			try:
				conn = dbShared.ghConn()
				cursor = conn.cursor()
			except Exception:
				result = "Error: could not connect to database\n"

			if (cursor):
				# Forbid approval by normal users
				cursor.execute('SELECT galaxyState FROM tGalaxy WHERE galaxyID=%s', [galaxy])
				row = cursor.fetchone()
				cursor.close()
				if row[0] == 0 and galaxyState != '0' and currentUser != 'ioscode':
					result = "Error: You may not change the status of this galaxy until it has been approved by the site administrator.\n"
				else:
					# Get user galaxy admin status
					adminList = dbShared.getGalaxyAdminList(conn, currentUser)
					if '<option value="{0}">'.format(galaxy) in adminList:
						result = updateGalaxy(galaxy, galaxyName, galaxyState, galaxyNGE, galaxyWebsite, galaxyPlanets, galaxyResourceTypes, galaxyAdmins)
					else:
						result = "Error: You are not listed as an administrator of that galaxy.\n"
			else:
				result = "Error: No database connection\n"
			conn.close()

		else:
			try:
				conn = dbShared.ghConn()
				cursor = conn.cursor()
			except Exception:
				result = "Error: could not connect to database\n"

			if (cursor):
				cursor.execute("SELECT galaxyName FROM tGalaxy WHERE galaxyState=0 AND submittedBy=%s", [currentUser])
				row = cursor.fetchone()
				if row != None:
					errstr = errstr + "Error: You already have a galaxy waiting for review ({0}).  Please wait until it is approved before submitting another.".format(row[0])
				else:
					cursor.execute("SELECT galaxyID FROM tGalaxy WHERE galaxyState < 3 AND galaxyName=%s", [galaxyName])
					row = cursor.fetchone()
					if row != None:
						errstr = errstr + "Error: A galaxy already exists with that name, please choose a different name.\n"
				cursor.close()

				if errstr == "":
					result = addGalaxy(galaxyName, galaxyNGE, galaxyWebsite, galaxyPlanets, galaxyResourceTypes, currentUser, galaxyAdmins)
				else:
					result = errstr
			else:
				result = "Error: No Database connection.\n"
	else:
		result = "Error: must be logged in to add galaxy data\n"
else:
	result = errstr

print('Content-type: text/xml\n')
doc = minidom.Document()
eRoot = doc.createElement("result")
doc.appendChild(eRoot)

eText = doc.createElement("resultText")
tText = doc.createTextNode(result)
eText.appendChild(tText)
eRoot.appendChild(eText)
print(doc.toxml())

if (result.find("Error:") > -1):
	sys.exit(500)
else:
	sys.exit(200)
