#!/bin/sh
cat sensor*.log | cut -d , -f 2 | sort | uniq -c
