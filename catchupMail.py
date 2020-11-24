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

emailIDs = ['spawns', 'activity']

def ghConn():
	conn = pymysql.connect(host = dbInfo.DB_HOST,
		db = dbInfo.DB_NAME,
		user = dbInfo.DB_USER,
		passwd = dbInfo.DB_PASS)
	conn.autocommit(True)
	return conn


def sendAlertMail(conn, userID, msgText, link, alertID, alertTitle, emailIndex):
	# Don't try to send mail if we exceeded quota within last hour
	lastFailureTime = datetime(2000, 1, 1, 12)
	currentTime = datetime.fromtimestamp(time.time())
	timeSinceFailure = currentTime - lastFailureTime

	try:
		f = open("last_notification_failure_" + emailIDs[emailIndex] + ".txt")
		lastFailureTime = datetime.strptime(f.read().strip(), "%Y-%m-%d %H:%M:%S")
		f.close()
		timeSinceFailure = currentTime - lastFailureTime
	except IOError as e:
		sys.stdout.write("No last failure time\n")

	if timeSinceFailure.days < 1 and timeSinceFailure.seconds < 3660:
		sys.stderr.write(str(timeSinceFailure.seconds) + " less than 3660 no mail.\n")
		return 1

	# look up the user email
	cursor = conn.cursor()
	cursor.execute("SELECT emailAddress FROM tUsers WHERE userID='" + userID + "';")
	row = cursor.fetchone()
	if row == None:
		result = "bad username"
	else:
		email = row[0]
		if (email.find("@") > -1 and email.find(".") > -1):
			# send message
			message = EmailMessage()
			message['From'] = "\"Galaxy Harvester Alerts\" <" + emailIDs[emailIndex] + "@galaxyharvester.net>"
			message['To'] = email
			message['Subject'] = "".join(("Galaxy Harvester ", alertTitle))
			message.set_content("".join(("Hello ", userID, ",\n\n", msgText, "\n\n", link, "\n\n You can manage your alerts at http://galaxyharvester.net/myAlerts.py\n")))
			message.add_alternative("".join(("<div><img src='http://galaxyharvester.net/images/ghLogoLarge.png'/></div><p>Hello ", userID, ",</p><br/><p>", msgText.replace("\n", "<br/>"), "</p><p><a style='text-decoration:none;' href='", link, "'><div style='width:170px;font-size:18px;font-weight:600;color:#feffa1;background-color:#003344;padding:8px;margin:4px;border:1px solid black;'>View in Galaxy Harvester</div></a><br/>or copy and paste link: ", link, "</p><br/><p>You can manage your alerts at <a href='http://galaxyharvester.net/myAlerts.py'>http://galaxyharvester.net/myAlerts.py</a></p><p>-Galaxy Harvester Administrator</p>")), subtype='html')
			mailer = smtplib.SMTP(mailInfo.MAIL_HOST)
			mailer.login(emailIDs[emailIndex] + "@galaxyharvester.net", mailInfo.MAIL_PASS)
			try:
				mailer.send_message(message)
				result = 'email sent'
			except SMTPRecipientsRefused as e:
				result = 'email failed'
				sys.stderr.write('Email failed - ' + str(e))
				trackEmailFailure(datetime.fromtimestamp(time.time()).strftime("%Y-%m-%d %H:%M:%S"), emailIndex)
			mailer.quit()

			# update alert status
			if ( result == 'email sent' ):
				cursor.execute('UPDATE tAlerts SET alertStatus=1, statusChanged=NOW() WHERE alertID=' + str(alertID) + ';')
		else:
			result = 'Invalid email.'

	cursor.close()


def main():
	emailIndex = 0
	# check for command line argument for email to use
	if len(sys.argv) > 1:
		emailIndex = int(sys.argv[1])
	conn = ghConn()
	# try sending any backed up alert mails
	retryPendingMail(conn, emailIndex)


def trackEmailFailure(failureTime, emailIndex):
	# Update tracking file
	try:
		f = open("last_notification_failure_" + emailIDs[emailIndex] + ".txt", "w")
		f.write(failureTime)
		f.close()
	except IOError as e:
		sys.stderr.write("Could not write email failure tracking file")

def retryPendingMail(conn, emailIndex):
	# open email alerts that have not been sucessfully sent less than 48 hours old
	minTime = datetime.fromtimestamp(time.time()) - timedelta(days=4)
	cursor = conn.cursor()
	cursor.execute("SELECT userID, alertTime, alertMessage, alertLink, alertID FROM tAlerts WHERE alertType=2 AND alertStatus=0 and alertTime > '" + minTime.strftime("%Y-%m-%d %H:%M:%S") + "' and alertMessage LIKE '% - %';")
	row = cursor.fetchone()
	# try to send as long as not exceeding quota
	while row != None:
		fullText = row[2]
		splitPos = fullText.find(" - ")
		alertTitle = fullText[:splitPos]
		alertBody = fullText[splitPos+3:]
		result = sendAlertMail(conn, row[0], alertBody, row[3], row[4], alertTitle, emailIndex)
		if result == 1:
			sys.stderr.write("Delayed retrying rest of mail since quota reached.\n")
			break
		row = cursor.fetchone()

	cursor.close()


if __name__ == "__main__":
	main()
