#!/bin/sh
echo "Compare Template Files against Home Dir..."
echo
diff -ryd --suppress-common-lines ../home/ ~/ | grep -v "^Only in"
