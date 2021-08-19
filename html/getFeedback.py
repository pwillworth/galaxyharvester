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
import ghShared

def getFeedbackComments(conn, feedbackID):
		comments = ''
		# fetch comments
		comcursor = conn.cursor()
		comcursor.execute("SELECT entered, tFeedbackComments.userID, comment, pictureName, tFeedbackComments.entered FROM tFeedbackComments LEFT JOIN tUsers ON tFeedbackComments.userID = tUsers.userID WHERE feedbackID=" + str(feedbackID) + " ORDER BY entered;")
		comrow = comcursor.fetchone()
		comments = comments + '<div class="comments" id="comments_' + str(feedbackID) + '">'
		while comrow != None:
			if (comrow[3] == None):
				userText = comrow[1] + ' - <small>' + str(comrow[4]) + '</small>'
			else:
				userText = '<a href="' + ghShared.BASE_SCRIPT_URL + 'user.py/' + comrow[1] + '" class="nameLink"><img src="/images/users/'+ comrow[3] + '" class="tinyAvatar" /><span style="vertical-align:4px;">'+ comrow[1] +  '</span></a> <span style="vertical-align:4px;"><small>'+ str(comrow[4]) +'</small><span>'
			
			commentWithLines = re.sub(r'\n{3,}', r'\n', comrow[2])
			commentWithLines = re.sub(r'\n', r'<br>', commentWithLines)
			comments = comments + '<p class="commentItem">' + commentWithLines + '</p><p>' + userText + '</p>'
			comrow = comcursor.fetchone()

		comcursor.close()

		return comments

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
sort = form.getfirst("sort", "rank")
perPage = form.getfirst("perPage", "10")
lastItem = form.getfirst("lastItem", "")

# escape input to prevent sql injection
sid = dbShared.dbInsertSafe(sid)
perPage = dbShared.dbInsertSafe(perPage)
lastItem = dbShared.dbInsertSafe(lastItem)


# Get a session
logged_state = 0

sess = dbSession.getSession(sid)
if (sess != ''):
	logged_state = 1
	currentUser = sess

fltCount = 0
result = ""
orderStr = ""

#  Check for errors
errstr = ""

if (perPage.isdigit() != True):
	errstr = errstr + "Error: Invalid number provided for number per page. \r\n"

if (sort == "time"):
    orderStr = " ORDER BY entered DESC"
else:
    orderStr = " ORDER BY rank DESC"

filterStr = " WHERE feedbackState = 1"
if (lastItem != ""):
	try:
		if (sort == "rank"):
			float(lastItem)
			filterStr = filterStr + " AND (SELECT SUM(vote) FROM tFeedbackVotes WHERE tFeedbackVotes.feedbackID = tFeedback.feedbackID) * 1.0 + ((DATEDIFF(CURDATE(), tFeedback.entered) + (TIME_TO_SEC(tFeedback.entered)/86400)) / 999999) < " + str(lastItem)
		else:
			filterStr = filterStr + " AND tFeedback.entered < '" + lastItem + "'"
	except ValueError:
		errstr = errstr + "That is not a valid last item. \r\n"

print('Content-type: text/html\n')

# Only process if no errors
if (errstr == ""):
	if (logged_state > 0):
		joinStr = ' LEFT JOIN tFeedbackVotes fv ON tFeedback.feedbackID = fv.feedbackID AND "' + currentUser + '" = fv.userID'
		joinCols = ', fv.vote'
	else:
		joinStr = ''
		joinCols = ''
	result = '  <ul class="feedback">'
	conn = dbShared.ghConn()
	# open list of feedback
	cursor = conn.cursor()
	cursor.execute("SELECT tFeedback.feedbackID, tFeedback.entered, tFeedback.userID, feedback, pictureName, (SELECT IFNULL(SUM(vote),0) FROM tFeedbackVotes WHERE tFeedbackVotes.feedbackID = tFeedback.feedbackID) * 1.0 + ((DATEDIFF(CURDATE(), tFeedback.entered) + (TIME_TO_SEC(tFeedback.entered)/86400)) / 9999999) AS rank" + joinCols + " FROM tFeedback LEFT JOIN tUsers ON tFeedback.userID = tUsers.userID" + joinStr + filterStr + orderStr + " LIMIT " + str(perPage) + ";")

	row = cursor.fetchone()
	while row != None:
		if (logged_state > 0 and currentUser != row[2]):
			upColor = 'Grey'
			downColor = 'Grey'
			upVote = '1'
			downVote = '-1'
			if (row[6] != None):
				if (row[6] > 0):
					upColor = 'Green'
					upVote = '0'
				if (row[6] < 0):
					downColor = 'Red'
					downVote = '0'

			voteTools = '<div><div class="inlineBlock" id="voteup_' + str(row[0]) + '"><a alt="I like this idea" title="Vote Up" style="cursor: pointer;" onclick="voteFeedback(this,' + str(row[0]) + ',' + upVote + ');"><img src="/images/check' + upColor + '24.png" style="padding:5px;"/></a></div><div class="inlineBlock" id="votedown_' + str(row[0]) + '"><a alt="Not so much." title="Vote Down" style="cursor: pointer;" onclick="voteFeedback(this,' + str(row[0]) + ',' + downVote + ');"><img src="/images/x' + downColor + '24.png" style="padding:5px;"/></a></div></div>'
		else:
			if (currentUser != row[2]):
				voteTools = "<div>Login to vote</div>"
			else:
				voteTools = "<div>Yours, thanks!</div>"

		if (row[4] == None):
			userText = row[2] + ' - <small>' + str(row[1]) + '</small>'
		else:
			userText = '<a href="' + ghShared.BASE_SCRIPT_URL + 'user.py/' + row[2] + '" class="nameLink"><img src="/images/users/'+ row[4] + '" class="tinyAvatar" /><span style="vertical-align:4px;">'+ row[2] + '</span></a> <span style="vertical-align:4px;"><small>'+ str(row[1]) +'</small><span>'
		if logged_state > 0:
			userText = userText + '<button type="button" id="addFeedbackComment_' + str(row[0]) + '" class="ghButton" onclick="addFeedbackComment(this)" style="float:right;">Add Comment</button>'

		result = result + '<li id="feedback_' + str(row[0]) + '"><div class="feedbackBox"><div class="inlineBlock" style="width:85%"><p class="feedbackItem">' + row[3] + '</p><p>' + userText + '</p>'
		result = result + getFeedbackComments(conn, row[0])
		result = result + '</div></div><div class="inlineBlock" style="padding: 8px;vertical-align:top;"><div class="standOut rankBox">rank<br/>' + str(int(row[5])) + '</div>' + voteTools + '</div></div></li>'

		if (sort == "rank"):
			lastItem = row[5]
		else:
			lastItem = row[1]
		row = cursor.fetchone()

	if result.find("<li") > -1:
		result = result + "  </ul>"
		if (str(cursor.rowcount) == perPage):
			result = result + '<div style="text-align:center;"><button id="moreButton" class="ghButton" onclick="moreFeedback(\''+ str(lastItem) + '\');">More</button></div>'
	else:
		result = "No Feedback Yet"

	cursor.close()
	conn.close()
else:
	result = errstr

print(result)

if (result.find("Error:") > -1):
	sys.exit(500)
else:
	sys.exit(200)
