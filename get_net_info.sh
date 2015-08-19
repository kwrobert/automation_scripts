#!/bin/bash

#####################################################################################################
# Script: get_net_info.sh 
# Author: Kyle Robertson
# Date: August 12, 2015
# Useage: ./get_net_info.sh control_ip_address master_rc_file_path rc_file_name openstack_password network_name
# Description: Retreves more detailed information about a given Openstack network. Outputs that info
# in YAML format
#####################################################################################################

# Get command line args
control_ip=$1
master_rc_file_path=$2
rc_file_name=$3
os_pswd=$4
net_name=$5
# Copy RC file to control node
scp $master_rc_file_path "$control_ip:~/"
# Execute commands on control node
ssh $control_ip '
source '"$rc_file_name"' <<< '"$(echo $os_pswd)"'
neutron net-show'" $net_name"'
'