#!/bin/bash

while ps -p $1 > /dev/null; do sleep 1; done

$2 &