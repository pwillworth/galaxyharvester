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
import re
from http import cookies
import hashlib
import uuid
import pymysql
import json
import urllib
import requests
import smtplib
from email.message import EmailMessage
import dbSession
import dbShared
import ghShared
sys.path.append("../")
import dbInfo
import keyInfo
import mailInfo


def getCAPTCHA(token):
    # prepare data for request
    values = {"secret": keyInfo.RECAPTCHA_KEY, "response": token}
    # reads the response back from Google
    try:
        response = requests.post(ghShared.RECAPTCHA_URL, values)
        cResult = json.loads(response.content)
        if cResult['success'] and cResult['action'] == 'submitJoin':
            return cResult['score']
        else:
            sys.stderr.write("Captcha failure: {0}\n".format(str(cResult)))
            return -1
    except requests.RequestException as e:
        sys.stderr.write("Communication with reCAPTCHA URL failure: {0}".format(str(e)))
        return -1
    except KeyError as e:
        sys.stderr.write("Failed to decode response for captcha: {0}\n{1}".format(response.status_code, str(e)))
        return -1
    except AttributeError as e:
        sys.stderr.write("Failed to interpret reCAPTCHA response: {0}\n{1}".format(response.status_code, str(e)))
        return -1

def sendVerificationMail(user, address, code):
    # send message
    message = EmailMessage()
    message['From'] = "\"Galaxy Harvester Activation\" <{0}>".format(mailInfo.REGMAIL_USER)
    message['To'] = address
    message['Subject'] = "Galaxy Harvester Account Verification"
    link = "http://galaxyharvester.net/verifyUser.py?vc={0}".format(code)
    message.set_content("Hello " + user + ",\n\nYou have created a new account on galaxyharvester.net using this email address.  Before you can use your new account, you must verify this email with us by clicking the link below.  If the link does not work, please copy the link and paste it into your browser address box.\n\n" + link + "\n\nThanks,\n-Galaxy Harvester Administrator\n")
    message.add_alternative("<div><img src='http://galaxyharvester.net/images/ghLogoLarge.png'/></div><p>Hello " + user + ",</p><br/><p>You have created a new account on galaxyharvester.net using this email address.  Before you can use your new account, you must verify this email with us by clicking the link below.  If the link does not work, please copy the link and paste it into your browser address box.</p><p><a style='text-decoration:none;' href='" + link + "'><div style='width:170px;font-size:18px;font-weight:600;color:#feffa1;background-color:#003344;padding:8px;margin:4px;border:1px solid black;'>Click Here To Verify</div></a><br/>or copy and paste link: " + link + "</p><br/><p>Thanks,</p><p>-Galaxy Harvester Administrator</p>", subtype='html')
    mailer = smtplib.SMTP(mailInfo.MAIL_HOST)
    mailer.login(mailInfo.REGMAIL_USER, mailInfo.MAIL_PASS)
    mailer.send_message(message)
    mailer.quit()
    return 'email sent'

C = cookies.SimpleCookie()
useCookies = 1
errorstr = ''
try:
    C.load(os.environ["HTTP_COOKIE"])
except KeyError:
    useCookies = 0

form = cgi.FieldStorage()

uname = form.getfirst("uname")
email = form.getfirst("email")
userpass = form.getfirst("userpass")
tokenCAPTCHA = form.getfirst("g-recaptcha-response")
# escape input to prevent sql injection
uname = dbShared.dbInsertSafe(uname)
email = dbShared.dbInsertSafe(email)
userpass = dbShared.dbInsertSafe(userpass)

result = "createusersuccess"

if uname == None or email == None or userpass == None:
    errorstr = "Missing user parameters"
else:
    if len(uname) < 3:
        errorstr = errorstr + "The login name must be at least 3 characters.\n"
    if len(email) < 6:
        errorstr = errorstr + "That was not a valid email address.\n"
    if len(userpass) < 6:
        errorstr = errorstr + "The password must be at least 6 characters.\n"
    if re.search('\W', uname):
        errorstr = errorstr + "Error: user name contains illegal characters.\n"
    if re.search('[><"&\']', email):
        errorstr = errorstr + "Error: email address contains illegal characters.\n"
    if '@eyepaste.com' in email:
        errorstr = errorstr + "Error: disposable emails not allowed.\n"

# CAPTCHAv3 validation https://developers.google.com/recaptcha/docs/v3
if ghShared.RECAPTCHA_ENABLED:
    if tokenCAPTCHA:
        scoreCAPTCHA = getCAPTCHA(tokenCAPTCHA)
        if scoreCAPTCHA == -1:
            errorstr = errorstr + "Error: CAPTCHA problem, please contact support."
        elif not scoreCAPTCHA > 0.5:
            sys.stderr.write("Registration failure due to low CAPTCHA score {0}".format(str(scoreCAPTCHA)))
            errorstr = errorstr + "Error: Robot detected\n"
    else:
        if 'HTTP_USER_AGENT' in os.environ and ghShared.getMobilePlatform(os.environ["HTTP_USER_AGENT"]) != '':
            errorstr = errorstr + "Error: Sorry, mobile joining is temporarily unavailable.  Please visit Galaxy Harvester from a web browser to join.  https://galaxyharvester.net"
        else:
            errorstr = errorstr + "Error: No CAPTCHA token found\n"

if errorstr != "":
    result = "createuserfail"
else:
    # For passing in to message for on success
    errorstr = email
    # Prepare encrypted password and verification code
    passString = dbInfo.DB_KEY3 + userpass
    crypt_pass = hashlib.sha1(passString.encode()).hexdigest()
    verify_code = uuid.uuid4().hex

    conn = dbShared.ghConn()
    # Do not allow duplicate email
    ecursor = conn.cursor()
    ecursor.execute("SELECT userID FROM tUsers WHERE emailAddress='" + email + "' AND userState > 0;")
    erow = ecursor.fetchone()
    if erow != None:
        result = "createuserfail"
        errorstr = "That e-mail address is already registered under another user, please use another."
    else:
        cursor = conn.cursor()
        cursor.execute("SELECT userID, userState FROM tUsers WHERE userID='" + uname + "';")
        row = cursor.fetchone()
        if row != None and row[1] > 0:
            result = "createuserfail"
            errorstr = "That login name is already used, please try another."
        else:
            if row != None:
                # Update existing user row that has not been verified yet incase verification expired
                updatestr = "UPDATE tUsers SET emailAddress='" + email + "', userPassword='" + crypt_pass + "', created=Now(), verificationCode='" + verify_code + "' WHERE userID='" + uname + "';"
            else:
                updatestr = "INSERT INTO tUsers (userID, emailAddress, userPassword, created, verificationCode) VALUES ('" + uname + "','" + email + "','" + crypt_pass + "', Now(), '" + verify_code + "');"
            cursor.execute(updatestr)
            sendVerificationMail(uname, email, verify_code)
        cursor.close()

    ecursor.close()
    conn.close()

if os.environ.get("HTTP_REFERER", "none") == 'none':
    print('Content-Type: text/html\n')
    print(result + '-' + errorstr)
else:
    if useCookies:
        C["create_result"] = result
        C["create_error"] = errorstr
        print(C)

    print('Status: 303 See Other')
    print('Location: /message.py?action=' + result + '&actionreason=' + urllib.parse.quote_plus(errorstr))
    print('')
