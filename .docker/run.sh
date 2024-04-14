#!/bin/bash

# symlink the cache for last alert check files to be available in www root
# (Note: used by `checkAlerts.py`)
ln -s /var/www/cache/last_alerts_check_added.txt /var/www/last_alerts_check_added.txt
ln -s /var/www/cache/last_alerts_check_removed.txt /var/www/last_alerts_check_removed.txt

# trap exits and kill them properly
force_stop_apache2ctl () {
  apache2ctl -k stop
}
trap "force_stop_apache2ctl" EXIT

# start server
apache2ctl -DFOREGROUND
