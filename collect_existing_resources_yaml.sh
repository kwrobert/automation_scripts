#!/bin/bash

#####################################################################################################
# Script: collect_existing_resources_yaml.sh 
# Author: Kyle Robertson
# Date: August 10, 2015
# Useage: ./collect_existing_resources.sh control_ip_address master_rc_file_path rc_file_name openstack_password
# Description: This script is intended to be executed on the Fuel Master node within Mirantis 
# Openstack. It uses SSH to access the control node from the master node and executes CLI commands for
# all relevant Openstack services that return desirable info as strings to stdout in YAML format. This
# makes it much easier to load the information into python scripts for manipulation.
#####################################################################################################

# Get command line args
control_ip=$1
master_rc_file_path=$2
rc_file_name=$3
os_pswd=$4
echo $os_pswd
# Copy RC file to control node
scp $master_rc_file_path "$control_ip:~/"
# Execute commands on control node
ssh $control_ip '
source '"$rc_file_name"' <<< '"$(echo $os_pswd)"'
command_list_nova=(aggregate-list flavor-list floating-ip-list image-list list net-list)
command_list_neutron=(gateway-device-list net-external-list net-gateway-list net-list port-list router-list security-group-list security-group-rule-list subnet-list)
command_list_cinder=(list type-list)
command_list_swift=(list)
command_list_glance=(image-list)
command_list_keystone=(role-list tenant-list user-list)
service_list=(keystone nova neutron cinder swift glance)
for service in "${service_list[@]}"; do
    arr=command_list_$service[@]
    for cmd in "${!arr}"; do
        exc="$service $cmd -f yaml"
        echo "---"; echo "- command: $service $cmd"; $exc
    done
done
'
