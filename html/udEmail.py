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
import cgi
import Cookie
import MySQLdb
import dbSession
import dbShared


def sendVerificationMail(user, address, code):
    # send message
    message = Message(From="\"Galaxy Harvester Registration\" <registration@galaxyharvester.net>",To=address)
    message.Subject = "Galaxy Harvester Email Change Verification"
    link = "http://galaxyharvester.net/verifyUser.py?vc={0}&vt=mail".format(code)
    message.Body = "Hello " + user + ",\n\nYou have updated your e-mail address on galaxyharvester.net to this email address.  You must verify this email with us by clicking the link below before the change can be completed.  If the link does not work, please copy the link and paste it into your browser address box.\n\n" + link + "\n\nThanks,\n-Galaxy Harvester Administrator\n"
    message.Html = "<div><img src='http://galaxyharvester.net/images/ghLogoLarge.png'/></div><p>Hello " + user + ",</p><br/><p>You have updated your e-mail address on galaxyharvester.net to this email address.  You must verify this email with us by clicking the link below before the change can be completed.  If the link does not work, please copy the link and paste it into your browser address box.</p><p><a style='text-decoration:none;' href='" + link + "'><div style='width:170px;font-size:18px;font-weight:600;color:#feffa1;background-color:#003344;padding:8px;margin:4px;border:1px solid black;'>Click Here To Verify</div></a><br/>or copy and paste link: " + link + "</p><br/><p>Thanks,</p><p>-Galaxy Harvester Administrator</p>"
    mailer = Mailer(mailInfo.MAIL_HOST)
    mailer.login(mailInfo.REGMAIL_USER, mailInfo.MAIL_PASS)
    mailer.send(message)
    return 'email sent'


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
email = form.getfirst("email")
# escape input to prevent sql injection
sid = dbShared.dbInsertSafe(sid)
email = dbShared.dbInsertSafe(email)
# Get a session
logged_state = 0
linkappend = ''

sess = dbSession.getSession(sid, 2592000)
if (sess != ''):
    logged_state = 1
    currentUser = sess
    linkappend = 'gh_sid=' + sid

#  Check for errors
errstr=''
if (len(email) < 6):
    errstr = errstr + "That is not a valid email address. \r\n"
if (logged_state == 0):
    errstr = errstr + "You must be logged in to update your email address. \r\n"

if (errstr != ''):
    result = "Your E-mail Address could not be updated because of the following errors:\r\n" + errstr
else:
    conn = dbShared.ghConn()
    # Do not allow duplicate email
    ecursor = conn.cursor()
    ecursor.execute("SELECT userID FROM tUsers WHERE emailAddress='" + email + "' AND userState > 0;")
    erow = ecursor.fetchone()
    if erow != None:
        result = "That e-mail is already in use by another user."
    else:
        cursor = conn.cursor()
        updatestr = "UPDATE tUsers SET verificationCode='" + verify_code + "', emailChange='" + email + "' WHERE userID='" + currentUser + "';"
        sendVerificationMail(uname, email, verify_code)
        result = "E-Mail Address Update Verification Email Sent.  Check your e-mail at this new address to finalize the change."
        cursor.close()

    conn.close()


print "Content-Type: text/html\n"
print result
