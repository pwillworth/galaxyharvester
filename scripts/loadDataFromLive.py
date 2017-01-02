#!/usr/bin/python
import os
import sys
import MySQLdb
import urllib
import urllib2

liveService = 'http://galaxyharvester.net/resourcesDump.py'
#liveService = 'http://192.168.0.3/resourcesDump.py'
liveKey1 = 'dbpass'
liveKey3 = 'orderpass'
liveKey4 = 'resetpass'
liveKey5 = 'redirpass'

tableNames = ['tGalaxy', 'tResources', 'tResourcePlanet', 'tResourceEvents', 'tUsers', 'tUserStats', 'tUserWaypoints', 'tWaypoint', 'tSchematicImages']
# key 4 reset table list
#tableNames = ['tResources', 'tResourcePlanet', 'tResourceEvents', 'tUsers', 'tUserStats', 'tUserWaypoints', 'tWaypoint', 'tSchematicImages', 'tFavorites', 'tObjectType', 'tPlanet', 'tProfession', 'tResourceGroup', 'tResourceGroupCategory', 'tResourceType', 'tResourceTypeCreature', 'tResourceTypeGroup', 'tSchematic', 'tSchematicIngredients', 'tSchematicQualities', 'tSchematicResWeights', 'tSkillGroup']
# for key 5 so it just runs once
#tableNames = ['tWaypoint']

indexFile = 'index.htm'
indexContent = '<html><head>\n<title>gh redirect</title>\n<script type="text/javascript">\ndocument.location.href="http://www.galaxyharvester.com";\n</script>\n</head><body>Loading...</body></html>'

localHost = 'localhost'
localUser = 'webusr'
localPass = ''
localName = 'swgresource'

conn = MySQLdb.connect(host = localHost,
	db = localName,
	user = localUser,
	passwd = localPass,
	local_infile = 1)
conn.autocommit(True)
cursor = conn.cursor()

# fetch table data
for i in range(len(tableNames)):
	print '-- Getting ' + tableNames[i] + ' --'
	try:
		# send live key 4 also to reset
		tableResult = urllib2.urlopen(liveService + '?key1=' + liveKey1 + '&key2=' + tableNames[i] + '&key3=' + liveKey3)
		#tableResult = urllib2.urlopen(liveService + '?key1=' + liveKey1 + '&key2=' + tableNames[i] + '&key3=' + liveKey3 + '&key4=' + liveKey4)
		#send live key 5 to redirect
		#tableResult = urllib2.urlopen(liveService + '?key1=' + liveKey1 + '&key2=' + tableNames[i] + '&key3=' + liveKey3 + '&key5=' + liveKey5 + '&iFile=' + urllib.quote(indexFile) + '&iContent=' + urllib.quote(indexContent))
	except urllib2.URLError, e:
		tableResult = None
		print tableNames[i] + ' failed. ' + str(e)

	if tableResult != None:
		print '-- Saving ' + tableNames[i] + ' --'
		# save a file copy here
		f = open(tableNames[i] + '.txt', 'w')
		f.write(tableResult.read())
		f.close()

		print '-- Loading ' + tableNames[i] + '.txt --'
		# load into database
		cursor.execute('DELETE FROM ' + tableNames[i] + ';')
		cursor.execute('LOAD DATA LOCAL INFILE \'' + os.getcwd() + '/' + tableNames[i] + '.txt\' INTO TABLE ' + tableNames[i] + ';')
			
cursor.close()
conn.close()

