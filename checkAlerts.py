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
import pymysql
import dbInfo
import optparse
import smtplib
from email.message import EmailMessage
from smtplib import SMTPRecipientsRefused
import time
from datetime import timedelta, datetime
import mailInfo
sys.path.append("galaxyharvester.net")
sys.path.append("html")
import ghNames
import serverBest
import dbShared

def ghConn():
	conn = pymysql.connect(host = dbInfo.DB_HOST,
	db = dbInfo.DB_NAME,
	user = dbInfo.DB_USER,
	passwd = dbInfo.DB_PASS)
	conn.autocommit(True)
	return conn

# Creates alert records for specified alert types
def addAlert(userID, alertTypes, msgText, link, alertTitle):
	msgText = dbShared.dbInsertSafe(msgText)
	alertTitle = dbShared.dbInsertSafe(alertTitle)
	if len(msgText) + len(alertTitle) + 3 > 1023:
		# Truncate the message so it will fit
		msgText = msgText[:(1020 - len(alertTitle))]
		msgText = msgText[:msgText[:-9].rfind("\n")]
		msgText = msgText + "\n more..."
	conn = ghConn()
	cursor = conn.cursor()

	if (alertTypes % 2 == 1):
		cursor.execute("".join(("INSERT INTO tAlerts (userID, alertType, alertTime, alertMessage, alertLink, alertStatus) VALUES ('", userID, "', 1, NOW(), '", alertTitle, " - ", msgText, "', '", link, "', 0);")))
		homeid = cursor.lastrowid
	if (alertTypes >= 4):
		cursor.execute("".join(("INSERT INTO tAlerts (userID, alertType, alertTime, alertMessage, alertLink, alertStatus) VALUES ('", userID, "', 4, NOW(), '", alertTitle, " - ", msgText, "', '", link, "', 0);")))
		mobileid = cursor.lastrowid
	if (alertTypes != 1 and alertTypes != 4 and alertTypes != 5):
		cursor.execute("".join(("INSERT INTO tAlerts (userID, alertType, alertTime, alertMessage, alertLink, alertStatus) VALUES ('", userID, "', 2, NOW(), '", alertTitle, " - ", msgText, "', '", link, "', 0);")))
		emailid = cursor.lastrowid
		cursor.close()
		sendAlertMail(conn, userID, msgText, link, emailid, alertTitle)
	else:
		cursor.close()

def sendAlertMail(conn, userID, msgText, link, alertID, alertTitle):
	# Don't try to send mail if we exceeded quota within last hour
	lastFailureTime = datetime(2000, 1, 1, 12)
	currentTime = datetime.fromtimestamp(time.time())
	timeSinceFailure = currentTime - lastFailureTime
	try:
		f = open("last_email_failure.txt")
		lastFailureTime = datetime.strptime(f.read().strip(), "%Y-%m-%d %H:%M:%S")
		f.close()
		timeSinceFailure = currentTime - lastFailureTime
	except IOError as e:
		sys.stdout.write("No last failure time\n")

	if timeSinceFailure.days < 1 and timeSinceFailure.seconds < 3660:
		return 1

	# look up the user email
	cursor = conn.cursor()
	cursor.execute("SELECT emailAddress FROM tUsers WHERE userID='" + userID + "';")
	row = cursor.fetchone()
	if row == None:
		result = "bad username"
	else:
		email = row[0]
		if (email.find("@") > -1):
			# send message
			message = EmailMessage()
			message['From'] = "".join(("\"Galaxy Harvester Alerts\" <", mailInfo.ALERTMAIL_USER, "@galaxyharvester.net>"))
			message['To'] = email
			message['Subject'] = "".join(("Galaxy Harvester ", alertTitle))
			message.set_content("".join(("Hello ", userID, ",\n\n", msgText, "\n\n", link, "\n\n You can manage your alerts at http://galaxyharvester.net/myAlerts.py\n")))
			message.add_alternative("".join(("<div><img src='http://galaxyharvester.net/images/ghLogoLarge.png'/></div><p>Hello ", userID, ",</p><br/><p>", msgText.replace("\n", "<br/>"), "</p><p><a style='text-decoration:none;' href='", link, "'><div style='width:170px;font-size:18px;font-weight:600;color:#feffa1;background-color:#003344;padding:8px;margin:4px;border:1px solid black;'>View in Galaxy Harvester</div></a><br/>or copy and paste link: ", link, "</p><br/><p>You can manage your alerts at <a href='http://galaxyharvester.net/myAlerts.py'>http://galaxyharvester.net/myAlerts.py</a></p><p>-Galaxy Harvester Bot</p>")), subtype='html')
			mailer = smtplib.SMTP(mailInfo.MAIL_HOST)
			mailer.login(mailInfo.ALERTMAIL_USER, mailInfo.MAIL_PASS)
			try:
				mailer.send_message(message)
				result = 'email sent'
			except SMTPRecipientsRefused as e:
				result = 'email failed'
				sys.stderr.write('Email failed - ' + str(e))
				trackEmailFailure(datetime.fromtimestamp(time.time()).strftime("%Y-%m-%d %H:%M:%S"))
			mailer.quit()

			# update alert status
			if ( result == 'email sent' ):
				cursor.execute('UPDATE tAlerts SET alertStatus=1, statusChanged=NOW() WHERE alertID=' + str(alertID) + ';')
		else:
			result = 'Invalid email.'


	cursor.close()

def checkSpawnAlerts(conn, spawnName, alertValue, galaxy, enteredBy, stats, galaxyName):
	# array of stat titles for making message
	statNames = ["CR","CD","DR","FL","HR","MA","PE","OQ","SR","UT","ER"]
	# open filters for the type
	cursor = conn.cursor()
	cursor.execute("SELECT userID, alertTypes, CRmin, CDmin, DRmin, FLmin, HRmin, MAmin, PEmin, OQmin, SRmin, UTmin, ERmin, fltType, fltValue, minQuality FROM tFilters WHERE galaxy=" + str(galaxy) + " AND alertTypes > 0 AND ((fltType = 1 AND fltValue = '" + alertValue + "') OR (fltType = 2 AND '" + alertValue + "' IN (SELECT resourceType FROM tResourceTypeGroup WHERE resourceGroup=fltValue)))")
	row = cursor.fetchone()
	# check each filter for this resource type/group
	while row != None:
		sendAlert = True
		statStr = ""
		alertMessage = ""
		if row[15] is not None and row[15] > 0:
			# Check resource to see if it hits min quality
			qualityTotal = 0.0
			for x in range(11):
				if row[x+2] > 0 and stats[x] != None:
					thisValue = 1.0*stats[x]*(row[x+2]/100.0)
					qualityTotal = qualityTotal + thisValue
					statStr = statStr + statNames[x] + " " + str(row[x+2]) + "% "
			if qualityTotal < row[15]:
				sendAlert = False
			else:
				alertMessage = ' named {0} added to {1} with quality score {2:.0f} for {3}'.format(spawnName, galaxyName, qualityTotal, statStr)
		else:
			# check  to see if min stats hit
			for x in range(11):
				if (row[x+2]) > 0:
					if stats[x] is None or (stats[x] < row[x+2]):
						sendAlert = False
					else:
						statStr = statStr + statNames[x] + ": " + str(stats[x]) + ", "
			if len(statStr) > 1:
				statStr = statStr[:-2]
			if sendAlert:
				alertMessage = ' named {0} added to {1} with stats {2}'.format(spawnName, galaxyName, statStr)
		# add alert records if stats or quality triggered
		if sendAlert:
			# Look up the name for the alert value
			typeGroup = row[14]
			if row[13] == 1:
				typeGroup = ghNames.getResourceTypeName(row[14])
			else:
				typeGroup = ghNames.getResourceGroupName(row[14])

			addAlert(row[0], row[1], typeGroup + alertMessage, 'http://galaxyharvester.net/resource.py/' + str(galaxy) + '/' + spawnName, 'Resource Spawn Alert')

		row = cursor.fetchone()
	cursor.close()

def checkDespawnAlerts(conn, spawnID, spawnName, galaxyName, unavailable, galaxy):
	cursor = conn.cursor()
	cursor.execute('SELECT userID, despawnAlert FROM tFavorites WHERE itemID={0} AND despawnAlert > 0;'.format(spawnID))
	row = cursor.fetchone()
	while row != None:
		addAlert(row[0], row[1], 'Resource named ' + spawnName + ' on ' + galaxyName + ' despawned at ' + str(unavailable), 'http://galaxyharvester.net/resource.py/' + str(galaxy) + '/' + spawnName, 'Resource Despawn Alert')
		row = cursor.fetchone()

	cursor.close()

def checkServerBest(conn, spawnID, spawnName, galaxy, galaxyName):
	result = serverBest.checkSpawn(spawnID, 'history')
	for x in range(len(result[1])):
		schematicStr = ''
		bestStr = ''
		for k, v in result[1][x].items():
			quoteSchem = "".join(("'", k, "'"))
			schematicStr = ','.join((schematicStr, quoteSchem))
			bestStr = '\n'.join((bestStr, '\n'.join(v)))
		if len(schematicStr) > 0:
			schematicStr = schematicStr[1:]
		# open people with favorites for the professions involved
		cursor = conn.cursor()
		cursor.execute("SELECT tFavorites.userID, defaultAlertTypes, profName FROM tFavorites INNER JOIN tUsers ON tFavorites.userID = tUsers.userID INNER JOIN tProfession ON tFavorites.itemID = tProfession.profID WHERE tFavorites.galaxy={1} AND favType=3 AND itemID={0} GROUP BY tFavorites.userID, defaultAlertTypes, profName;".format(result[0][x], galaxy))
		row = cursor.fetchone()
		# Add alert for each user watching for profession server bests hit by this spawn
		while row != None:
			addAlert(row[0], row[1], bestStr, ''.join(('http://galaxyharvester.net/resource.py/', str(galaxy), '/', spawnName)), ''.join((row[2], ' Server best alert for ', galaxyName)))
			row = cursor.fetchone()

		cursor.close()

		# open people with favorites for the schematics involved
		cursor = conn.cursor()
		cursor.execute("SELECT tFavorites.userID, defaultAlertTypes, schematicID, schematicName FROM tFavorites INNER JOIN tUsers ON tFavorites.userID = tUsers.userID INNER JOIN tSchematic ON tFavorites.favGroup = tSchematic.schematicID WHERE tFavorites.galaxy={1} AND favType=4 AND favGroup IN ({0}) GROUP BY tFavorites.userID, defaultAlertTypes, schematicID, schematicName;".format(schematicStr, galaxy))
		row = cursor.fetchone()
		# Add alert for each user watching for schematic server bests hit by this spawn
		while row != None:
			addAlert(row[0], row[1], '\n'.join(result[1][x][row[2]]), ''.join(('http://galaxyharvester.net/resource.py/', str(galaxy), '/', spawnName)), ''.join((row[3], ' Server best alert for ', galaxyName)))
			row = cursor.fetchone()

		cursor.close()

def checkDespawnReputation(conn, spawnID, spawnName, entered, galaxy):
	# open events for this despawned resource
	users = {}
	lastEventTime = None
	alreadyRemovedFlag = False
	editedFlag = False
	cursor = conn.cursor()
	cursor.execute("SELECT galaxy, userID, eventTime, eventType, planetID, eventDetail FROM tResourceEvents WHERE spawnID={0} ORDER BY eventTime DESC;".format(spawnID))
	row = cursor.fetchone()
	if row != None:
		lastEventTime = row[2]
	# Summarize reputation bonus for each user involved
	while row != None:
		if row[1] not in users:
			users[row[1]] = 0
		if row[3] == 'a':
			if editedFlag == False:
				users[row[1]] = users[row[1]] + 3
			else:
				users[row[1]] = users[row[1]] + 1
		if row[3] == 'p':
			users[row[1]] = users[row[1]] + 1
		if row[3] == 'v':
			users[row[1]] = users[row[1]] + 2
		if row[3] == 'r':
			users[row[1]] = users[row[1]] + 1
		if row[3] == 'r' and row[4] == 0:
			users[row[1]] = users[row[1]] + 2
		if row[3] == 'e':
			users[row[1]] = users[row[1]] + 2
			editedFlag = True
		if row[3] == 'w':
			users[row[1]] = users[row[1]] + 2
		if row[3] == 'n':
			users[row[1]] = users[row[1]] + 2
		if row[3] == 'g':
			users[row[1]] = users[row[1]] + 2
		if row[5] == 'previously unavailable':
			alreadyRemovedFlag = True

		row = cursor.fetchone()
	cursor.close()

	if lastEventTime != None and alreadyRemovedFlag == False:
		timeSinceEntered = lastEventTime - entered
		tmpDays = timeSinceEntered.days
		# If resource has not been available for at least a few days its being removed prematurely and not valid for rep awards
		if tmpDays > 3:
			link = "/resource.py/" + str(galaxy) + "/" + spawnName
			message = "You gained reputation for your contribution to tracking resource " + spawnName + "!"
			for k, v in users.items():
                # Award rep for users contributing at least "4 points" and exclude automated users
				if v >= 4 and k != "etas" and k != "default" and k != "c0pp3r":
					dbShared.logEvent("INSERT INTO tUserEvents (userID, targetType, targetID, eventType, eventTime) VALUES ('" + k + "', 'r', " + str(spawnID) + ", '+', NOW());", "+", k, galaxy, spawnID)
					cursor = conn.cursor()
					cursor.execute("INSERT INTO tAlerts (userID, alertType, alertTime, alertMessage, alertLink, alertStatus) VALUES ('" + k + "', 1, NOW(), '" + message + "', '" + link + "', 0);")
					cursor.close()


def main():
	conn = ghConn()
    # First try sending any backed up alert mails
	retryPendingMail(conn)

	f = None
	lastAddedCheckTime = ""
	lastRemovedCheckTime = ""
	try:
		f = open("last_alerts_check_added.txt")
		lastAddedCheckTime = f.read().strip()
		f.close()
	except IOError as e:
		sys.stdout.write("No last added check time\n")

	try:
		f = open("last_alerts_check_removed.txt")
		lastRemovedCheckTime = f.read().strip()
		f.close()
	except IOError as e:
		sys.stdout.write("No last removed check time\n")

	# Check for despawn alerts
	checkRemovedStart = datetime.fromtimestamp(time.time()).strftime("%Y-%m-%d %H:%M:%S")
	if lastRemovedCheckTime == "":
		sys.stderr.write("Skipping removed check.\n")
	else:
		# look up the despawn info
		cursor = conn.cursor()
		cursor.execute("SELECT spawnName, galaxy, enteredBy, resourceType, CR, CD, DR, FL, HR, MA, PE, OQ, SR, UT, ER, galaxyName, unavailable, spawnID, entered FROM tResources INNER JOIN tGalaxy ON tResources.galaxy = tGalaxy.galaxyID WHERE unavailable >= '" + lastRemovedCheckTime + "';")
		row = cursor.fetchone()
		while row != None:
			spawnName = row[0]
			galaxyName = row[15]
			unavailable = row[16]
			checkDespawnAlerts(conn, row[17], spawnName, galaxyName, unavailable, row[1])
			checkDespawnReputation(conn, row[17], row[0], row[18], row[1])

			row = cursor.fetchone()

		cursor.close()

	# Update tracking file
	try:
		f = open("last_alerts_check_removed.txt", "w")
		f.write(checkRemovedStart)
		f.close()
	except IOError as e:
		sys.stderr.write("Could not write removed tracking file")

	# Check for spawn and server best alerts
	checkAddedStart = datetime.fromtimestamp(time.time()).strftime("%Y-%m-%d %H:%M:%S")
	if lastAddedCheckTime == "":
		sys.stderr.write("Skipping added check.\n")
	else:
		# look up the spawn info
		cursor = conn.cursor()
		cursor.execute("SELECT spawnName, galaxy, enteredBy, resourceType, CR, CD, DR, FL, HR, MA, PE, OQ, SR, UT, ER, galaxyName, unavailable, spawnID FROM tResources INNER JOIN tGalaxy ON tResources.galaxy = tGalaxy.galaxyID WHERE entered >= '" + lastAddedCheckTime + "' AND galaxyState=1 and unavailable IS NULL ORDER BY entered;")
		row = cursor.fetchone()
		while row != None:
			alertValue = row[3]
			galaxy = row[1]
			spawnName = row[0]
			enteredBy = row[2]
			stats = [row[4],row[5],row[6],row[7],row[8],row[9],row[10],row[11],row[12],row[13],row[14]]
			galaxyName = row[15]
			checkSpawnAlerts(conn, spawnName, alertValue, galaxy, enteredBy, stats, galaxyName)
			checkServerBest(conn, row[17], spawnName, galaxy, galaxyName)
			row = cursor.fetchone()

		cursor.close()

	conn.close()

	# Update tracking file
	try:
		f = open("last_alerts_check_added.txt", "w")
		f.write(checkAddedStart)
		f.close()
	except IOError as e:
		sys.stderr.write("Could not write added tracking file")


def trackEmailFailure(failureTime):
	# Update tracking file
	try:
		f = open("last_email_failure.txt", "w")
		f.write(failureTime)
		f.close()
	except IOError as e:
		sys.stderr.write("Could not write email failure tracking file")

def retryPendingMail(conn):
	# open email alerts that have not been sucessfully sent less than 48 hours old
	minTime = datetime.fromtimestamp(time.time()) - timedelta(days=2)
	cursor = conn.cursor()
	cursor.execute("SELECT userID, alertTime, alertMessage, alertLink, alertID FROM tAlerts WHERE alertType=2 AND alertStatus=0 and alertTime > '" + minTime.strftime("%Y-%m-%d %H:%M:%S") + "';")
	row = cursor.fetchone()
	# try to send as long as not exceeding quota
	while row != None:
		fullText = row[2]
		splitPos = fullText.find(" - ")
		alertTitle = fullText[:splitPos]
		alertBody = fullText[splitPos+3:]
		result = sendAlertMail(conn, row[0], alertBody, row[3], row[4], alertTitle)
		if result == 1:
			sys.stderr.write("Delayed retrying rest of mail since quota reached.\n")
			break
		row = cursor.fetchone()

	cursor.close()


if __name__ == "__main__":
	main()
