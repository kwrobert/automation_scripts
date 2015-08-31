#!/bin/bash

#####################################################################################################
# Script: deploy_stack.sh 
# Author: Kyle Robertson
# Date: August 10, 2015
# Company: Worlcom Exchange Inc.
# Useage: ./deploy_stack.sh control_ip_address master_rc_file_path rc_file_name openstack_password template_file
# Description: This script is intended to be executed on the Fuel Master node within Mirantis 
# Openstack. It uses SCP to copy template files and RC files from the master node to the control node.
# It then uses SSH to access the control node from the master node and executes Heat CLI commands
# to create and deploy the stack specified by the template files 
#####################################################################################################

# Get command line args
control_ip=$1
master_rc_file_path=$2
rc_file_name=$3
os_pswd=$4
template_file=$5
# Copy RC file and template file to control node
scp $master_rc_file_path "$control_ip:~/"
scp "/root/scripts/$template_file" "$control_ip:~/"
# Execute commands on control node
DATE=`date +%Y-%m-%d_hr%H-min%M-sec%S`
ssh $control_ip '
source '"$rc_file_name"' <<< '"$(echo $os_pswd)"'
heat stack-create -f '"$template_file"' -t 60 --enable-rollback Stack_'"$DATE"'
'