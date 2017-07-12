#!/bin/bash
alertname=$1
target=$2
losspattern=$3
rtt=$4
hostname=$5
script="$( cd "$( dirname "$0"  )" && pwd  )""/record.py"

/usr/bin/python $script $alertname $target $losspattern $rtt $hostname
