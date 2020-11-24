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

import sys
import os
import cgi
from http import cookies
import pymysql
import dbSession
import dbShared
import urllib
import re
import time
from datetime import timedelta, datetime
import ghObjects
import postResource
import markUnavailable


def updatePlanetSpawns(planetID, classID, resources, galaxyID, userID):
	result = ''
	conn = dbShared.ghConn()
	cursor = conn.cursor()
	spawnAddCount = 0
	spawnVerifyCount = 0
	spawnRemovedCount = 0
	spawnErrorCount = 0
	errors = ''

	for spawn in resources:
		# first check if spawn has been reported or not
		cursor.execute("SELECT unavailable, spawnID, OQ FROM tResources WHERE galaxy=%s AND spawnName=%s;", [galaxyID, spawn.spawnName])
		row = cursor.fetchone()
		if row != None:
			if row[0] != None:
				# Resource was previously unavailable - bringing it back
				timeSinceRemoved =  datetime.fromtimestamp(time.time()) - row[0]
				# only add back if recently but not too recently marked unavailable
				if (timeSinceRemoved.days < 3 and timeSinceRemoved.days > 0) or (timeSinceRemoved.days == 0 and timeSinceRemoved.seconds > 7200):
					status = postResource.addResPlanet(row[1], planetID, spawn.spawnName, userID, galaxyID)
					if (status.find("Error:") > -1):
						spawnErrorCount += 1
						errors = errors + status + '\n<br />'
					else:
						spawnAddCount += 1
			else:
				# Verify already listed resource
				status = postResource.addResPlanet(row[1], planetID, spawn.spawnName, userID, galaxyID)
				if row[2] == None and spawn.stats.OQ > 0:
					status = postResource.addResStats(row[1], '', spawn.stats.CR, spawn.stats.CD, spawn.stats.DR, spawn.stats.FL, spawn.stats.HR, spawn.stats.MA, spawn.stats.PE, spawn.stats.OQ, spawn.stats.SR, spawn.stats.UT, spawn.stats.ER, '', userID, galaxyID) + '  ' + status
				if (status.find("Error:") > -1):
					spawnErrorCount += 1
					errors = errors + status + '\n<br />'
				else:
					spawnVerifyCount += 1
		else:
			# Post as new resource
			# Only post if a valid type was found
			typecursor = conn.cursor()
			typecursor.execute("SELECT resourceTypeName FROM tResourceType WHERE resourceType=%s", [spawn.resourceType])
			typerow = typecursor.fetchone()
			if typerow != None:
				status = postResource.addResource(spawn.spawnName, galaxyID, spawn.resourceType, str(spawn.stats.CR), str(spawn.stats.CD), str(spawn.stats.DR), str(spawn.stats.FL), str(spawn.stats.HR), str(spawn.stats.MA), str(spawn.stats.PE), str(spawn.stats.OQ), str(spawn.stats.SR), str(spawn.stats.UT), str(spawn.stats.ER), userID)
				if (status.find("Error:") == -1):
					spawnID = dbShared.getSpawnID(spawn.spawnName, galaxyID)
					status = postResource.addResPlanet(spawnID, planetID, spawn.spawnName, userID, galaxyID) + '   ' + status

				if (status.find("Error:") > -1):
					spawnErrorCount += 1
					errors = errors + status + '\n<br />'
				else:
					spawnAddCount += 1
			else:
				spawnErrorCount += 1
				errors = errors + 'Error: Resource type not found.\n<br />'
			typecursor.close()

	# Check for resources that have despawned
	if len(resources) > 0 and classID != '' and spawnErrorCount == 0:
		cursor.execute("SELECT tResources.spawnID, spawnName FROM tResources INNER JOIN tResourcePlanet ON tResources.spawnID = tResourcePlanet.spawnID INNER JOIN (SELECT resourceType FROM tResourceTypeGroup WHERE resourceGroup='" + classID + "' GROUP BY resourceType) rtg ON tResources.resourceType = rtg.resourceType WHERE tResources.galaxy=%s AND tResourcePlanet.unavailable IS NULL AND tResourcePlanet.planetID=%s;", [galaxyID, planetID])
		row = cursor.fetchone()
		while row != None:
			stillAvailable = False
			for spawn in resources:
				if row[1] == spawn.spawnName:
					stillAvailable = True
			if not stillAvailable:
				# available spawn was not in report, so mark it unavailable
				status = markUnavailable.removeSpawn(row[0], planetID, userID, galaxyID)
				if (status.find("Error:") > -1):
					spawnErrorCount += 1
					errors = errors + status + '\n<br />'
				else:
					spawnRemovedCount += 1

			row = cursor.fetchone()

	cursor.close()
	conn.close()

	result = "Report Upload Complete...\n<br/>{0} Errors\n<br/>{1} Spawns Added\n<br/>{2} Spawns Verified\n<br/>{3} Spawns Removed.\n<br/>{4}".format(spawnErrorCount, spawnAddCount, spawnVerifyCount, spawnRemovedCount, errors)
	return result

def getSpawnsJSON(planetID, resources, message):
	result = '{  "response" : { "message" : "' + message + '", "planet" : ' + str(planetID) + ', "resources" : ['
	for spawn in resources:
		result = result + '{'
		result = result + spawn.getJSON()
		result = result[:-2] + '},\n'

	if len(resources) > 0:
		result = result[:-2]
	result = result + '  ] } }\n'
	return result


def main():
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

	errstr=''

	if not "reportFile" in form:
		errstr = "No report file sent."
	else:
		rpt_data = form["reportFile"]
		if not rpt_data.file: errstr = "report data is not a file."

	src_url = form.getfirst('src_url', '/surveyList.py')
	galaxyID = form.getfirst('reportGalaxy', '')
	dataAction = form.getfirst('dataAction', '')
	# escape input to prevent sql injection
	sid = dbShared.dbInsertSafe(sid)
	galaxyID = dbShared.dbInsertSafe(galaxyID)

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
	if not galaxyID.isdigit():
		errstr = errstr + "Galaxy ID must be a valid number. \r\n"
	if errstr == '':
		rptName = rpt_data.filename
	if (logged_state == 0):
		errstr = errstr + "You must be logged in to post resources. \r\n"

	if (errstr != ''):
		result = "Your report could not be posted because of the following errors:\r\n" + errstr
	else:
		result = ''
		isNGE = False

		# process file
		thisSpawn = ghObjects.resourceSpawn()
		resourcesFound = []
		planetID = 0
		classID = ''
		headerMatch = None
		planetMatch = None
		classMatch = None
		resourceStart = None
		typeMatch = None
		nameMatch = None
		statMatch = None
		conn = dbShared.ghConn()
		cursor = conn.cursor()
		if (cursor):
			cursor.execute('SELECT galaxyNGE FROM tGalaxy WHERE galaxyID={0};'.format(str(galaxyID)))
			row = cursor.fetchone()
			if (row != None) and (row[0] > 0):
				isNGE = True
			cursor.close()
		# NGE version of droid report has different format with more indent and group levels
		if isNGE:
			typePattern = ' +([a-zA-Z][a-zA-Z0-9\- ]+)'
			namePattern = ' +\\\#pcontrast1 (\w+)\\\#'
			statPattern = ' +(?:\\\#\w{6,6})? *(ER|CR|CD|DR|FL|HR|MA|PE|OQ|SR|UT): *(?:\\\#\w{6,6})? *(\d+)'
		else:
			typePattern = '\t([a-zA-Z0-9\- ]+)'
			namePattern = '\t\t\\\#pcontrast1 (\w+)\\\#'
			statPattern = '\t\t\t(ER|CR|CD|DR|FL|HR|MA|PE|OQ|SR|UT): (\d+)'

		while 1:
			line = rpt_data.file.readline()
			if not line: break;
			if headerMatch == None:
				headerMatch = re.match("Interplanetary Survey: (\w+) - (\w+)", line)
			if planetMatch == None:
				planetMatch = re.match("\\\#pcontrast\d\sPlanet: \\\#pcontrast\d\s(.+)", line)
			if classMatch == None:
				classMatch = re.match("\\\#pcontrast\d\sResource Class: \\\#pcontrast\d\s(.+)", line)

			if resourceStart == None:
				resourceStart = re.match("\\\#pcontrast\d\sResources located.*", line)
			else:
				typeMatch = re.match(typePattern, line)
				nameMatch = re.match(namePattern, line)
				if typeMatch:
					thisType = dbShared.getResourceTypeID(conn, typeMatch.group(1))
					thisTypeName = typeMatch.group(1)
				if nameMatch:
					if thisSpawn.spawnName != '':
						resourcesFound.append(thisSpawn)
					thisName = nameMatch.group(1)
					thisSpawn = ghObjects.resourceSpawn()
					thisSpawn.spawnName = thisName.lower()
					thisSpawn.resourceType = thisType
					thisSpawn.resourceTypeName = thisTypeName
				# Check for resource stats from enhanced droid reports
				statMatch = re.match(statPattern, line)
				if statMatch:
					setattr(thisSpawn.stats, statMatch.group(1), int(statMatch.group(2)))

		conn.close()

		if thisSpawn.spawnName != '':
			resourcesFound.append(thisSpawn)

		# Update planet data if valid results
		if headerMatch:
			planetID = dbShared.getPlanetID(headerMatch.group(1))
			classID = headerMatch.group(2).lower()
		elif planetMatch:
			planetID = dbShared.getPlanetID(planetMatch.group(1))
		else:
			result = "Error: No planet found in file header."
		if classMatch:
			classID = classMatch.group(1).lower()

		if planetID > 0:
			if dataAction == 'returnJSON':
				result = getSpawnsJSON(planetID, resourcesFound, "{0} spawns loaded from report".format(len(resourcesFound)))
			else:
				result = updatePlanetSpawns(planetID, classID, resourcesFound, galaxyID, currentUser)
		else:
			result = "Error: Could not determine planet from file header."

	if dataAction == 'returnJSON':
		# add resources page uses json data to populate grid
		print("Content-Type: text/json\n")
		print(result)
	else:
		# survey list page will load result message from cookie after redirect
		if useCookies:
			C['surveyReportAttempt'] = result
			C['surveyReportAttempt']['max-age'] = 60
			print(cookies)
		else:
			linkappend = linkappend + '&surveyReportAttempt=' + urllib.quote(result)

		print("Content-Type: text/html\n")
		if src_url != None:
			print('<html><head><script type=text/javascript>document.location.href="' + src_url + linkappend + '"</script></head><body></body></html>')
		else:
			print(result)

	if result.find("Error:") > -1:
		sys.exit(500)
	else:
		sys.exit(200)

if __name__ == "__main__":
	main()

