"""

This file is part fo Kukkaisvoima. Kukkaisvoima a lightweight weblog
system.

Copyright (C) 2006-2008 Petteri Klemola

This is config file. Kukkaisvoima's license don't affect this file.

You should keep this file private and see that this in not readable
from public web. For example when using Apache webserver create
.htaccess file with the following entry:

<files kukkaisvoima_settings.py>
 order allow,deny
 deny from all
</files>

"""

# Config variables
# Url of the blog (without trailing /)
baseurl = 'http://localhost/blog.py'
blogname = 'Galaxy Harvester News'
slogan = 'What\'s new with the Galaxy Harvester Application'
description = "Latest news and updates on the resource tracking tool for SWGEmu."
encoding = 'iso-8859-15'
stylesheet = '/style/kukka.css'
feedicon = '/images/feed-icon-14x14.png'
defaultauthor = 'anonymous'
favicon = 'http://localhost/favicon.ico'
doctype = '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">'
# Email to send comments to
blogemail = 'galaxyharvester@gmail.com'
# Language for the feed
language = 'en'
# Number of entries per page
numberofentriesperpage = 10
# Directory which contains the blog entries
datadir = 'posts'
# Directory which contains the index and comments. Must be script
# writable directory
indexdir = 'temp'
# Maximum comments per entry. Use -1 for no comments and 0 for no
# restriction
maxcomments = 30
# answer to spamquestion (question variable is l_nospam_question)
nospamanswer = '5'
# This is admin password to manage comments. password should be
# something other than 'password'
passwd = 'password'
# Entry and comment Date format
dateformat = "%F %T"
# Show only first paragraph when showing many entries
entrysummary = False

# Language variables
l_archives = 'Archives'
l_categories = 'Categories'
l_comments = 'Comments'
l_comments2 = 'Comments'
l_date = 'Date'
l_nextpage = 'Next page'
l_previouspage = 'Previous page'
l_leave_reply = 'Leave reply'
l_no_comments_allowed = 'No comments allowed'
l_no_comments = 'No comments'
l_name_needed = 'Name (needed)'
l_email_needed = 'Email (needed)'
l_webpage = 'Webpage'
l_no_html = 'No html allowed in reply'
l_nospam_question = 'What\'s 2 + 3?'
l_delete_comment = 'Delete comment'
l_passwd = 'Admin password'
l_admin = 'Admin'
l_admin_comments = 'Manage comments'
l_do_you_delete = 'Your about to delete comment this, are you sure you want to that?'
# new in version 8
l_search = "Search"
l_search2 = "No matches"
