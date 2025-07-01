#!/bin/bash
#https://stackoverflow.com/questions/1058047/wait-for-a-process-to-finish

while ps -p $1 > /dev/null; do sleep 1; done

$2 &
