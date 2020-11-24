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

import cgi
import os
from datetime import datetime
from time import localtime, strptime, strftime
import pymysql
import dbSession
import dbShared

def renderFeed(path):
	newest = dbShared.getLastResourceChange()
	resTitles = ['CR', 'CD', 'DR', 'FL', 'HR', 'MA', 'PE', 'OQ', 'SR', 'UT', 'ER']
	rfc822time = "%a, %d %b %Y %H:%M:%S -0800"
	print("Content-Type: text/xml; charset=iso-8859-15\n")
	print("<?xml version=\"1.0\" encoding=\"iso-8859-15\"?>")
	print("<rss version=\"2.0\"")
	print("xmlns:content=\"http://purl.org/rss/1.0/modules/content/\"")
	print(">")
	print("<channel>")
	resGroup = ""
	if len(path) >= 1:
		if (path[0] == "creature"):
			resGroup = "creature_resources"
		elif (path[0] == "flora"):
			resGroup = "flora_resources"
		elif (path[0] == "chemical"):
			resGroup = "chemical"
		elif (path[0] == "water"):
			resGroup = "water"
		elif (path[0] == "mineral"):
			resGroup = "mineral"
		elif (path[0] == "gas"):
			resGroup = "gas"
		elif (path[0] == "energy"):
			resGroup = "energy_renewable"
	if resGroup != "":
		print("<title>Galaxy Harvester Resource Activity: " + resGroup + "</title>")
	else:
		print("<title>Galaxy Harvester Resource Activity</title>")
	print("<link>http://galaxyharvester.net</link>")
	print("<description>Latest additions to Galaxy Harvester resource listing</description>")
	print("<pubDate>" + newest.strftime(rfc822time) + "</pubDate>")
	print("<lastBuildDate>" + newest.strftime(rfc822time) + "</lastBuildDate>")
	print("<generator>http://galaxyharvester.net/resourceList.py</generator>")
	print("<language>en</language>")

	# print resources
	conn = dbShared.ghConn()
	cursor = conn.cursor()
	criteriaStr = " WHERE unavailable IS NULL"
	if (cursor):
		if (resGroup != "any" and resGroup != ""):
			criteriaStr = criteriaStr + " AND tResourceType.resourceType IN (SELECT resourceType FROM tResourceTypeGroup WHERE resourceGroup='" + resGroup + "' GROUP BY resourceType)"
		sqlStr1 = 'SELECT spawnID, spawnName, galaxy, entered, enteredBy, tResources.resourceType, resourceTypeName, resourceGroup,'
		sqlStr1 += ' CR, CD, DR, FL, HR, MA, PE, OQ, SR, UT, ER,'
		sqlStr1 += ' CASE WHEN CRmax > 0 THEN ((CR-CRmin) / (CRmax-CRmin))*100 ELSE 0 END AS CRperc, CASE WHEN CDmax > 0 THEN ((CD-CDmin) / (CDmax-CDmin))*100 ELSE 0 END AS CDperc, CASE WHEN DRmax > 0 THEN ((DR-DRmin) / (DRmax-DRmin))*100 ELSE 0 END AS DRperc, CASE WHEN FLmax > 0 THEN ((FL-FLmin) / (FLmax-FLmin))*100 ELSE 0 END AS FLperc, CASE WHEN HRmax > 0 THEN ((HR-HRmin) / (HRmax-HRmin))*100 ELSE 0 END AS HRperc, CASE WHEN MAmax > 0 THEN ((MA-MAmin) / (MAmax-MAmin))*100 ELSE 0 END AS MAperc, CASE WHEN PEmax > 0 THEN ((PE-PEmin) / (PEmax-PEmin))*100 ELSE 0 END AS PEperc, CASE WHEN OQmax > 0 THEN ((OQ-OQmin) / (OQmax-OQmin))*100 ELSE 0 END AS OQperc, CASE WHEN SRmax > 0 THEN ((SR-SRmin) / (SRmax-SRmin))*100 ELSE 0 END AS SRperc, CASE WHEN UTmax > 0 THEN ((UT-UTmin) / (UTmax-UTmin))*100 ELSE 0 END AS UTperc, CASE WHEN ERmax > 0 THEN ((ER-ERmin) / (ERmax-ERmin))*100 ELSE 0 END AS ERperc,'
		sqlStr1 += ' galaxyName FROM tResources INNER JOIN tResourceType ON tResources.resourceType = tResourceType.resourceType INNER JOIN tGalaxy ON tResources.galaxy = tGalaxy.galaxyID'
		sqlStr1 = sqlStr1 + criteriaStr + ' ORDER BY entered DESC LIMIT 25;'
		cursor.execute(sqlStr1)
		row = cursor.fetchone()
		while (row != None):
			print("<item>")
			print("<title>" + row[1] + " Added by " + row[4] + " on " + row[30] + "</title>")
			print("<link>http://galaxyharvester.net/resource.py/" + str(row[2]) + "/" + row[1] + "</link>")
			print("<pubDate>" + row[3].strftime(rfc822time) + "</pubDate>")
			print("<guid isPermalink=\"true\">http://galaxyharvester.net/resource.py/" + str(row[2]) + "/" + row[1] + "</guid>")
			print("<description><![CDATA[ " + row[6] + " ]]></description>")
			print("<content:encoded><![CDATA[")
			print("<br />" + row[6] + "<br />")
			for i in range(11):
				if (row[i+8] != None and row[i+19] != None):
					print(resTitles[i] + ": " + str(row[i+8]) + " (" + ("%.0f" % float(row[i+19])) + "%)<br />")
			print("]]></content:encoded>")
			print("</item>")
			row = cursor.fetchone()

	print("</channel>")
	print("</rss>")

# get path info and render feed
def main():
	path = ['']
	if 'PATH_INFO' in os.environ:
		path = os.environ['PATH_INFO'].split('/')[1:]
		path = [p for p in path if p != '']

	renderFeed(path)

if __name__ == "__main__":
	main()
