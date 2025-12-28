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
import pymysql
import dbShared
import optparse

# Return position among server best
def getPosition(conn, spawnID, galaxy, statWeights, resourceGroup, serverBestMode):
    obyStr = ''
    obyStr2 = ''
    maxCheckStr = ''

    # calculate column sort by based on quality weights
    for k, v in statWeights.items():
        weightVal = '%.2f' % v
        obyStr = ''.join((obyStr, '+CASE WHEN ', k, 'max > 0 THEN (', k, ' / 1000)*', weightVal, ' ELSE ', weightVal, '*.25 END'))
        obyStr2 = ''.join((obyStr2, '+', weightVal))
        maxCheckStr = ''.join((maxCheckStr, '+', k, 'max'))

    if (obyStr != ''):
        obyStr = obyStr[1:]
        obyStr2 = obyStr2[1:]
        maxCheckStr = maxCheckStr[1:]
    else:
        # No stat weights to calculate
        return 0

    if serverBestMode == 'current':
        minimumPercentOfBest = .8
    else:
        minimumPercentOfBest = .95

    sqlStr1 = ''.join(('SELECT spawnID, (', obyStr, ') / (', obyStr2, ') AS overallScore, ', maxCheckStr, ' FROM tResources INNER JOIN tResourceType ON tResources.resourceType = tResourceType.resourceType',
              ' INNER JOIN (SELECT resourceType FROM tResourceTypeGroup WHERE resourceGroup="', resourceGroup, '" OR resourceType="', resourceGroup, '" GROUP BY resourceType) rtg ON tResources.resourceType = rtg.resourceType'
              ' WHERE galaxy=', str(galaxy), ' ORDER BY (', obyStr, ') / (' + obyStr2 + ')'
              ' DESC LIMIT 8;'))
    cursor = conn.cursor()

    spawnPos = 0
    if (cursor):
        cursor.execute(sqlStr1)
        row = cursor.fetchone()
        # Check is spawn in top 8 and within 5% quality of 1st
        rowPos = 1
        topScore = 0.0
        while row != None and row[1] != None:
            if rowPos == 1:
                topScore = row[1]
            if row[1] / topScore < minimumPercentOfBest:
                break
            if str(row[0]) == spawnID and row[2] != 0:
                spawnPos = rowPos
                break

            rowPos += 1
            row = cursor.fetchone()

        cursor.close()

    return spawnPos

def checkSchematics(conn, spawnID, galaxy, prof, resourceTypes, serverBestMode, allPositions):
    bestPositions = {}
    # Select schematics where ingredient in type or groups of type
    sqlStr2 = 'SELECT tSchematic.schematicID, ingredientObject, Sum(ingredientContribution), schematicName, resName FROM tSchematicIngredients INNER JOIN tSchematic ON tSchematicIngredients.schematicID = tSchematic.schematicID INNER JOIN tSkillGroup ON tSchematic.skillGroup = tSkillGroup.skillGroup  LEFT JOIN (SELECT resourceGroup AS resID, groupName AS resName FROM tResourceGroup UNION ALL SELECT resourceType, resourceTypeName FROM tResourceType) res ON ingredientObject = res.resID WHERE profID={0} AND tSchematic.schematicID NOT IN (SELECT schematicID FROM tSchematicOverrides WHERE galaxyID={1}) AND tSchematic.galaxy IN ({3}, {1}) AND ingredientObject IN ({2}) GROUP BY tSchematic.schematicID, ingredientObject, resName, ingredientQuantity, ingredientName ORDER BY tSchematic.schematicID, ingredientQuantity DESC, ingredientName;'.format(prof, galaxy, resourceTypes, dbShared.getBaseProfs(galaxy))
    ingCursor = conn.cursor()
    ingCursor.execute(sqlStr2)
    ingRow = ingCursor.fetchone()
    # Iterate over ingredients of matching schematics
    while ingRow != None:
        # get quality attributes for schematic
        stats = {}
        lastStats = {}
        tmpGroup = ''
        spawnPosition = 0
        # Select the quality groups for this ingredient
        expSQL = 'SELECT expGroup, statName, Sum(statWeight)/Sum(weightTotal)*100 AS wp FROM tSchematicQualities INNER JOIN tSchematicResWeights ON tSchematicQualities.expQualityID = tSchematicResWeights.expQualityID WHERE schematicID="' + ingRow[0] + '" GROUP BY expGroup, statName ORDER BY expGroup;'
        expCursor = conn.cursor()
        expCursor.execute(expSQL)
        expRow = expCursor.fetchone()
        while (expRow != None):
            if expRow[0] != tmpGroup:
                if tmpGroup != '':
                    # Check for top 3 status
                    if stats != lastStats:
                        allKey = '{0}|{1}'.format(str(stats), ingRow[1])
                        if allKey in allPositions:
                            spawnPosition = allPositions[allKey]
                        else:
                            spawnPosition = getPosition(conn, spawnID, galaxy, stats, ingRow[1], serverBestMode)
                            allPositions[allKey] = spawnPosition
                    if spawnPosition > 0:
                        if spawnPosition == 1:
                            eventDetail = ''.join(('New server best spawn for ', ingRow[3], ' ', tmpGroup.replace('exp_','').replace('exp','').replace('_', ' '), ', ingredient ', ingRow[4], '.'))
                        else:
                            eventDetail = ''.join(('Almost server best spawn for ', ingRow[3], ' ', tmpGroup.replace('exp_','').replace('exp','').replace('_', ' '), ', ingredient ', ingRow[4], '.'))
                        eventDetail = dbShared.dbInsertSafe(eventDetail)
                        if ingRow[0] in bestPositions:
                            bestPositions[ingRow[0]].append(eventDetail)
                        else:
                            bestPositions[ingRow[0]] = [eventDetail]
                        dbShared.logSchematicEvent(spawnID, galaxy, ingRow[0], tmpGroup, str(spawnPosition), eventDetail, serverBestMode)
                    lastStats = stats
                    stats = {}
                tmpGroup = expRow[0]
            if expRow[1] in stats:
                stats[expRow[1]] = stats[expRow[1]] + float(expRow[2])
            else:
                stats[expRow[1]] = float(expRow[2])
            expRow = expCursor.fetchone()

        # Check for top 3 status on last ingredient
        if stats != lastStats:
            allKey = '{0}|{1}'.format(str(stats), ingRow[1])
            if allKey in allPositions:
                spawnPosition = allPositions[allKey]
            else:
                spawnPosition = getPosition(conn, spawnID, galaxy, stats, ingRow[1], serverBestMode)
                allPositions[allKey] = spawnPosition
        if spawnPosition > 0:
            if spawnPosition == 1:
                eventDetail = ''.join(('New server best spawn for ', ingRow[3], ' ', tmpGroup.replace('exp_','').replace('exp','').replace('_', ' '), ', ingredient ', ingRow[4], '.'))
            else:
                eventDetail = ''.join(('Almost server best spawn for ', ingRow[3], ' ', tmpGroup.replace('exp_','').replace('exp','').replace('_', ' '), ', ingredient ', ingRow[4], '.'))
            eventDetail = dbShared.dbInsertSafe(eventDetail)
            if ingRow[0] in bestPositions:
                bestPositions[ingRow[0]].append(eventDetail)
            else:
                bestPositions[ingRow[0]] = [eventDetail]
            dbShared.logSchematicEvent(spawnID, galaxy, ingRow[0], tmpGroup, str(spawnPosition), eventDetail, serverBestMode)
        expCursor.close()

        ingRow = ingCursor.fetchone()
    ingCursor.close()

    return [allPositions, bestPositions]

def checkSpawn(spawnID, serverBestMode):
    # Look up additional spawn info needed
    allPositions = {}
    professions = []
    profresults = []
    hasResults = False
    conn = dbShared.ghConn()
    cursor = conn.cursor()
    cursor.execute('SELECT galaxy, resourceType, (SELECT GROUP_CONCAT(resourceGroup SEPARATOR "\',\'") FROM tResourceTypeGroup rtg WHERE rtg.resourceType=tResources.resourceType) FROM tResources WHERE spawnID=%s;', [spawnID])
    row = cursor.fetchone()
    if row != None:
        # Check each profession separately but ignore ones that do not care about quality
        pc = conn.cursor()
        pc.execute('SELECT profID, profName FROM tProfession WHERE craftingQuality > 0;')
        pcRow = pc.fetchone()
        while pcRow != None:
            result = checkSchematics(conn, str(spawnID), row[0], pcRow[0], "".join(("'", row[1], "','", str(row[2]), "'")), serverBestMode, allPositions)
            allPositions = result[0]
            if result[1] != None and len(result[1]) > 0:
                professions.append(str(pcRow[0]))
                profresults.append(result[1])
                hasResults = True

            pcRow = pc.fetchone()

        if len(profresults) == 0:
            dbShared.logSchematicEvent(spawnID, row[0], '', 'Good For Nada', '0', 'Found no server best results.', serverBestMode)
    else:
        sys.stderr.write('Could not find that spawn.')
    cursor.close()
    conn.close()

    return [professions, profresults]

def main():
    # get the spawn id we are checking
    parser = optparse.OptionParser()
    parser.add_option('-s', '--spawn', dest='spawn')
    (opts, args) = parser.parse_args()
    if opts.spawn is None:
	    sys.stderr.write("missing required options.\n")
	    exit(-1)
    else:
        print(checkSpawn(opts.spawn, 'history'))

if __name__ == "__main__":
    main()
