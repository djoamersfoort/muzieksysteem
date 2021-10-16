#!/bin/bash

while true; do
    perl -e 'print ":00"; print "\xCC" x 1440; print "\x00"'
    sleep .1
    perl -e 'print ":00"; print "\xFF" x 1440; print "\x00"'
    sleep .1
done