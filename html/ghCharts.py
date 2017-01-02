#!/usr/bin/python
"""

 Copyright 2016 Paul Willworth <ioscode@gmail.com>

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

import ghLists
import dbShared

def getChartURL(chartType, chartSize, dataType, resType, available, groupType, galaxy):

	chartStr = "http://chart.apis.google.com/chart?cht=" + chartType + "&chs=" + chartSize
	chartData = "&chd=t:"
	chartLabels = ""
	chartMax = 0
	if chartType == 'bhs':
		# just display y axis and data values for bar chart
		chartAxes = '&chxt=y&chm=N,000000,0,-1,11'
	else:
		chartAxes = '&chxt=x,y'
	galaxyCriteria = ''
	if galaxy != None and galaxy <> '':
		galaxyCriteria = ' AND mt.galaxy=' + galaxy

	conn = dbShared.ghConn()
	cursor = conn.cursor()
	if (cursor):
		if groupType == 'user':
			# group by userID charts
			if resType == 'all':
				sqlStr = 'SELECT userID, ' + dataType + ' FROM tUserStats mt WHERE 1=1' + galaxyCriteria + ' ORDER BY ' + dataType + ' DESC LIMIT 5;'
			else:
				sqlStr = 'SELECT userID, Count(eventTime) AS numActions FROM tResourceEvents mt INNER JOIN tResources ON mt.spawnID = tResources.spawnID INNER JOIN tResourceTypeGroup ON tResources.resourceType = tResourceTypeGroup.resourceType WHERE resourceGroup = \'' + resType + '\'' + galaxyCriteria
				if available != 0:
					sqlStr += ' AND unavailable IS NULL'
				sqlStr += ' AND eventType=\'' + dataType + '\' GROUP BY userID ORDER BY Count(eventTime) DESC LIMIT 5;'
		else:
			# group by time period charts
			if groupType == 'day':
				dateSelect = 'DAY(eventTime)'
				dateGroup = 'YEAR(eventTime), MONTH(eventTime), DAY(eventTime)'
			elif groupType == 'week':
				dateSelect = 'WEEK(eventTime)'
				dateGroup = 'YEAR(eventTime), WEEK(eventTime)'
			else:
				dateSelect = 'YEAR(eventTime)'
				dateGroup = 'YEAR(eventTime)'

			sqlStr = 'SELECT ' + dateSelect + ' AS eDate, Count(eventTime) AS numActions FROM tResourceEvents mt INNER JOIN tResources ON mt.spawnID = tResources.spawnID INNER JOIN tResourceTypeGroup ON tResources.resourceType = tResourceTypeGroup.resourceType WHERE resourceGroup = \'' + resType + '\'' + galaxyCriteria + ' AND eventType=\'' + dataType + '\' AND eventTime > DATE_SUB(CURDATE(),INTERVAL ' + str(available) + ' DAY) GROUP BY ' + dateGroup + ' ORDER BY ' + dateGroup + ';'
		cursor.execute(sqlStr)
		row = cursor.fetchone()

		while (row != None):
			# keep track of maximum data value for scale
			if row[1] > chartMax:
				chartMax = row[1]
			# build chart data and label strings (dont know why labels need to be opposite order for bar charts)
			chartData = chartData + str(row[1]) + ','
			chartLabels = '|' + str(row[0]) + chartLabels
			row = cursor.fetchone()

		cursor.close()
		# strip trailing comma
		if len(chartData) > 1:
			chartData = chartData[:-1]

	conn.close()
	# add proper value scaling to y axis on line chart
	if chartType == 'lc':
		chartAxes = chartAxes + '&chxr=1,0,' + str(chartMax)

	return chartStr + chartData + '&chco=e8d43d&chds=0,' + str(int(chartMax*1.03)) + chartAxes + '&chxl=0:' + chartLabels
