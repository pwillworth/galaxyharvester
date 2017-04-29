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

import sys
import os
import cgi
import Cookie
import MySQLdb
import dbSession
import dbShared
import Image
import urllib
import time
import subprocess
import json
import difflib
import ghObjects

# Get current url
try:
    url = os.environ['SCRIPT_NAME']
except KeyError:
    url = ''

form = cgi.FieldStorage()
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
else:
    currentUser = ''
    loginResult = 'success'
    sid = form.getfirst('gh_sid', '')


def lookupResourceType(typeName):
    try:
        conn = dbShared.ghConn()
        cursor = conn.cursor()
    except Exception:
        result = "Error: could not connect to database"

    resourceType = "no match"

    if (cursor):
        sqlStr = 'SELECT resourceType, resourceTypeName FROM tResourceType WHERE enterable > 0;'
        cursor.execute(sqlStr)
        row = cursor.fetchone()

        while (row != None):
            #find a close enough match to ocr detected name
            if len(difflib.get_close_matches(typeName, [row[1]], 1, 0.90)) > 0:
                resourceType = row[0]
                break

            row = cursor.fetchone()

        cursor.close()

    conn.close()

    return resourceType


errstr=''
if not form.has_key("capture"):
    errstr = "Error: No capture image sent."
else:
    img_data = form["capture"]
    if not img_data.file: errstr = "Error: capture is not a file."

# escape input to prevent sql injection
sid = dbShared.dbInsertSafe(sid)

# Get a session
logged_state = 0

sess = dbSession.getSession(sid)
if (sess != ''):
    logged_state = 1
    currentUser = sess
    if (useCookies == 0):
        linkappend = 'gh_sid=' + sid

s = ghObjects.resourceSpawn()
#  Check for errors
if errstr == '':
    imgName = img_data.filename
if (logged_state == 0):
    errstr = errstr + "Error: You must be logged in to add resources. \r\n"
try:
    im = Image.open(img_data.file)
except:
    errstr = errstr + "Error: I don't recognize the file you uploaded as an image (" + imgName + ").  Please make sure it is a jpg, gif, or png.  \r\n"

if (errstr != ''):
    result = "Error: Could not detect resource because of the following errors:\r\n" + errstr
else:
    result = ''

    #resize to improve ocr speed if too big, quality if too small
    xsize, ysize = im.size
    newwidth = xsize
    newheight = ysize
    if (ysize > 1000 or ysize < 800):
        if xsize >= ysize:
            newwidth = int(xsize * (900.0/ysize))
            newheight = 900
        elif ysize > xsize:
            newheight = int(ysize * (900.0/xsize))
            newwidth = 900
        # also convert to greyscale to improve recognition
        try:
            im = im.resize((newwidth,newheight), Image.ANTIALIAS).convert("L")
        except IOError:
            result = "Error: I can't handle that type of image file, please try a different one."

    if result == '':
        # write image file
        imageName = currentUser + str(time.time())
        im.save("temp/"+imageName+".png", dpi=(300,300))

        # detect text with tesseract
        ocrOutput = ""
        try:
            ocrOutput = subprocess.check_output(["tesseract", "temp/"+imageName+".png", "temp/"+imageName])
            #ocrOutput = subprocess.check_output(["bash", "-c", "export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/home/pwillworth/tesseract/lib;export TESSDATA_PREFIX=/home/pwillworth/tesseract/share;/home/pwillworth/tesseract/bin/tesseract temp/"+imageName+".png temp/"+imageName])
        except subprocess.CalledProcessError:
            result = "Error: Image could not be processed."
        except OSError:
            result = "Error: OCR service temporarily unavailable."

        # interpret tesseract output
        if result == "":
            lastLine = ""
            f = open("temp/"+imageName+".txt", "r")
            for line in f:
                adjLine = line.replace("'","").replace("-","").strip()
                if ":" in adjLine:
                    vp = adjLine.split(":")
                    if len(difflib.get_close_matches(vp[0], ["Resource Type"], 1, 0.7)) > 0:
                        s.spawnName = vp[1].strip()
                    if len(difflib.get_close_matches(vp[0], ["Resource Class"], 1, 0.7)) > 0:
                        s.resourceTypeName = vp[1].strip()
                        lastLine = "class"
                    else:
                        lastLine = ""

                    if len(difflib.get_close_matches(vp[0], ["Entangle Resistance"], 1, 0.8)) > 0:
                        try:
                            s.stats.ER = int(vp[1].strip())
                        except:
                            pass
                    if len(difflib.get_close_matches(vp[0], ["Cold Resistance"], 1, 0.8)) > 0:
                        try:
                            s.stats.CR = int(vp[1].strip())
                        except:
                            pass
                    if len(difflib.get_close_matches(vp[0], ["Conductivity"], 1, 0.8)) > 0:
                        try:
                            s.stats.CD = int(vp[1].strip())
                        except:
                            pass
                    if len(difflib.get_close_matches(vp[0], ["Decay Resistance"], 1, 0.8)) > 0:
                        try:
                            s.stats.DR = int(vp[1].strip())
                        except:
                            pass
                    if len(difflib.get_close_matches(vp[0], ["Flavor"], 1, 0.8)) > 0:
                        try:
                            s.stats.FL = int(vp[1].strip())
                        except:
                            pass
                    if len(difflib.get_close_matches(vp[0], ["Heat Resistance"], 1, 0.8)) > 0:
                        try:
                            s.stats.HR = int(vp[1].strip())
                        except:
                            pass
                    if len(difflib.get_close_matches(vp[0], ["Malleability"], 1, 0.8)) > 0:
                        try:
                            s.stats.MA = int(vp[1].strip())
                        except:
                            pass
                    if len(difflib.get_close_matches(vp[0], ["Potential Energy"], 1, 0.8)) > 0:
                        try:
                            s.stats.PE = int(vp[1].strip())
                        except:
                            pass
                    if len(difflib.get_close_matches(vp[0], ["Overall quality"], 1, 0.8)) > 0:
                        try:
                            s.stats.OQ = int(vp[1].strip())
                        except:
                            pass
                    if len(difflib.get_close_matches(vp[0], ["Shock Resistance"], 1, 0.8)) > 0:
                        try:
                            s.stats.SR = int(vp[1].strip())
                        except:
                            pass
                    if len(difflib.get_close_matches(vp[0], ["Unit Toughness"], 1, 0.8)) > 0:
                        try:
                            s.stats.UT = int(vp[1].strip())
                        except:
                            pass
                else:
                    if lastLine == "class":
                        s.resourceTypeName = s.resourceTypeName + " " + adjLine.strip()

            s.resourceType = lookupResourceType(s.resourceTypeName)
            f.close()
            result = "image scanned"
            # remove temp files
            os.remove("temp/"+imageName+".txt")
        os.remove("temp/"+imageName+".png")


print "Content-Type: text/json\n"
if (s.spawnName != "" or s.resourceType != "no match"):
    print json.dumps({"result": result, "spawnData": {"spawnName": s.spawnName, "resourceType": s.resourceType, "resourceTypeName": s.resourceTypeName, "ER": s.stats.ER, "CR": s.stats.CR, "CD": s.stats.CD, "DR": s.stats.DR, "FL": s.stats.FL, "HR": s.stats.HR, "MA": s.stats.MA, "PE": s.stats.PE, "OQ": s.stats.OQ, "SR": s.stats.SR, "UT": s.stats.UT}})
else:
    print json.dumps({"result": result})

if (result.find("Error:") > -1):
    sys.exit(500)
else:
    sys.exit(200)
