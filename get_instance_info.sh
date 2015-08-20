#!/bin/bash

#####################################################################################################
# Script: get_instance_info.sh 
# Author: Kyle Robertson
# Date: August 12, 2015
# Company: Worlcom Exchange Inc.
# Useage: ./get_instance_info.sh control_ip_address master_rc_file_path rc_file_name openstack_password instance_name
# Description: Collects more detailed information about a given Openstack Instance. Outputs that information
# in YAML format. 
#####################################################################################################

# Get command line args
control_ip=$1
master_rc_file_path=$2
rc_file_name=$3
os_pswd=$4
inst_name=$5
# Copy RC file to control node
scp $master_rc_file_path "$control_ip:~/"
# Execute commands on control node
ssh $control_ip '
source '"$rc_file_name"' <<< '"$(echo $os_pswd)"'
nova show'" $inst_name"'
'