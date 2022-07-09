#!/bin/bash
perl -e 'print "\x00" x 1440; print ":00"' > /dev/tcp/bitpanel.bitlair.nl/1337
