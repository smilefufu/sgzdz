#!/bin/bash

echo "select cards from pigs_"$1";" | sqlite3 data.db | tr "," "\n" | grep -v 小乔 | egrep -v "^张辽" | egrep -v "^$" | sort | uniq -c | sort -k1n
