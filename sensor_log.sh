#!/bin/bash
watch -n 5 "./sensor.sh | tee -a sensor.log"
