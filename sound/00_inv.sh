#!/bin/bash
find . -name '*.wav' -exec printf \\n{}\\n >&2 \; -exec sox {} -n stats \;
