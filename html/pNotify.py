#!/usr/bin/python
"""

 Copyright 2011 Paul Willworth <ioscode@gmail.com>

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

import urllib
import urllib2
import cgi
import dbShared
import MySQLdb
import sys

PP_URL = "https://www.sandbox.paypal.com/cgi-bin/webscr"
#PP_URL = "https://www.paypal.com/cgi-bin/webscr"


def verify_ipn(data):
	# prepares provided data set to inform PayPal we wish to validate the response
	data["cmd"] = "_notify-validate"
	params = urllib.urlencode(data)
 
	# sends the data and request to the PayPal Sandbox
	req = urllib2.Request(PP_URL, params)
	req.add_header("Content-type", "application/x-www-form-urlencoded")
	# reads the response back from PayPal
	response = urllib2.urlopen(req)
	status = response.read()
 
	# If not verified
	if not status == "VERIFIED":
		return False
 
	# if not the correct receiver
	if not data["receiver_email"] == "galaxyharvester@gmail.com":
		return False
 
	# otherwise...
	return True

# Process Payment Notification
form = cgi.FieldStorage()
data = {}
for key in form.keys():
	data[key] = form[key].value

completedStrCol = ""
completedStrVal = ""
result = ""

if not "txn_id" in data:
	result = "Error: Payment notification attempted with no data.  " + str(data)
	sys.stderr.write(result)
if not verify_ipn(data):
	result = "Invalid payment attempted.  " + str(data)
	sys.stderr.write(result)
else:
	transactionID = ""
	rcvEmail = None
	rcvID = None
	payerEmail = None
	payerID = None
	payerStatus = None
	firstName = None
	lastName = None
	paymentStatus = None
	paymentGross = None
	paymentFee = None
	shippingAmount = None
	handlingAmount = None
	currency = None
	paymentDate = None
	transactionType = None
	addressCity = None
	addressCountryCode = None
	addressState = None
	addressStatus = None
	addressStreet = None
	addressZip = None
	customInfo = None

	try:
		transactionID = data["txn_id"]
		paymentDate = dbShared.n2n(data["payment_date"])
		rcvEmail = dbShared.n2n(data["receiver_email"])
		rcvID = dbShared.n2n(data["receiver_id"])
		payerEmail = dbShared.n2n(data["payer_email"])
		payerID = dbShared.n2n(data["payer_id"])
		payerStatus = dbShared.n2n(data["payer_status"])
		paymentStatus = dbShared.n2n(data["payment_status"])
		firstName = dbShared.n2n(data["first_name"])
		lastName = dbShared.n2n(data["last_name"])
		paymentGross = dbShared.n2n(data["mc_gross"])
		paymentFee = dbShared.n2n(data["mc_fee"])
		currency = dbShared.n2n(data["mc_currency"])
		transactionType = dbShared.n2n(data["txn_type"])
		addressCity = dbShared.n2n(data["address_city"])
		addressCountryCode = dbShared.n2n(data["address_country_code"])
		addressState = dbShared.n2n(data["address_state"])
		addressStatus = dbShared.n2n(data["address_status"])
		addressStreet = dbShared.n2n(data["address_street"])
		addressZip = dbShared.n2n(data["address_zip"])
		customInfo = dbShared.n2n(data["custom"])
		shippingAmount = dbShared.n2n(data["shipping"])
		handlingAmount = dbShared.n2n(data["handling_amount"])

	except KeyError:
		# don't care if all fields not present
		result = ""

	# Look up existing payment
	conn = dbShared.ghConn()
	cursor = conn.cursor()

	cursor.execute('SELECT payerEmail FROM tPayments WHERE transactionID=%s;', (transactionID,))
	row = cursor.fetchone()

	if (row != None):
		# Update an existing transaction
		if paymentStatus == "Completed":
			completedStrCol = "completedDate="
			completedStrVal = "NOW(), "
		tempSQL = "UPDATE tPayments SET " + completedStrCol + completedStrVal + "recvEmail=%s, recvID=%s, payerEmail=%s, payerID=%s, payerStatus=%s, firstName=%s, lastName=%s, paymentStatus=%s, paymentGross=%s, paymentFee=%s, shippingAmount=%s, handlingAmount=%s, currency=%s, paymentDate=%s, transactionType=%s, addressCity=%s, addressCountryCode=%s, addressState=%s, addressStatus=%s, addressStreet=%s, addressZip=%s, customInfo=%s WHERE transactionID=%s"
	else:
		# Add the new transaction
		if paymentStatus == "Completed":
			completedStrCol = "completedDate, "
			completedStrVal = "NOW(), "
		tempSQL = "INSERT INTO tPayments (" + completedStrCol + "recvEmail, recvID, payerEmail, payerID, payerStatus, firstName, lastName, paymentStatus, paymentGross, paymentFee, shippingAmount, handlingAmount, currency, paymentDate, transactionType, addressCity, addressCountryCode, addressState, addressStatus, addressStreet, addressZip, customInfo, transactionID) VALUES (" + completedStrVal + "%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
	
	try:
		cursor.execute(tempSQL, (rcvEmail, rcvID, payerEmail, payerID, payerStatus, firstName, lastName, paymentStatus, paymentGross, paymentFee, shippingAmount, handlingAmount, currency, paymentDate, transactionType, addressCity, addressCountryCode, addressState, addressStatus, addressStreet, addressZip, customInfo, transactionID))
	except Exception, ex:
		result = 'Error: Add Failed.' + str(ex)

	cursor.close()
	conn.close()

if (result.find("Error:") > -1):
	sys.stderr.write(result)
	print 'Status: 500 Internal Server Error\r\n\r\n'
else:
	print 'Status: 200 Ok\r\n\r\n'

