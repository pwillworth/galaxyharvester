#!/bin/bash

force_stop_apache2ctl () {
  apache2ctl -k stop
}

trap "force_stop_apache2ctl" EXIT

apache2ctl -DFOREGROUND
