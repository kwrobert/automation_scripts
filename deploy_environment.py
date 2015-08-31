#####################################################################################################
# Script: deploy_environment.py
# Author: Kyle Robertson
# Date: August 11, 2015
# Company: Worlcom Exchange Inc.
# Useage: python deploy_environment.py -h
# Description: This script is intended to be executed on the Fuel Master node within Mirantis 
# Openstack. It uses SSH to access the control node from the master node and harvests all the 
# important information about any preexisting resources in a virtual environment. 
#####################################################################################################

try:
    import yaml
    import argparse 
    import script_tools as sT
    import subprocess
    import paramiko
    import getpass 
    import time
    import os 
    import re
    import itertools
    import openstack_objects as cL 
    import copy
except ImportError,output:
    print "%s installed on your machine or within your current Python environment. \
Please install that package and re-run this script."%output
    quit()

################################################################################   
def sh(cmd):
    return subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE).communicate()
################################################################################     
def CollectExistingResources(master_ssh,rc_file_path):
        
    # Determine what environments already exist and ask the user to pick one
    stdin,stdout,stderr = master_ssh.exec_command("fuel env list")
    text = stdout.read()
    lines = sT.TableParser(text)
    if len(lines) >= 2:
        env_ids = []
        for env in lines:
            if env['status'] == "operational":
                env_ids.append(env['id'])
        print "\nIt appears you have deployed multiple Openstack environments. Which environment would \
like to operate on from the following list?\n"
        print text
        env_id = str(raw_input("\nPlease enter the ID of the environment you wish to deploy your virtual infrastructure in: "))    
        while env_id not in env_ids:
            env_id = str(raw_input("Please enter the ID of the environment you wish to deploy your virtual infrastructure in: "))       
        # Get control node IP for the specified environment
        stdin,stdout,stderr = master_ssh.exec_command("fuel node list --env-id %s"%env_id)
        for line in stdout.readlines():
            datalist = line.split("|")
            if ("controller" in datalist[6]) and (datalist[1].lstrip().rstrip() == "ready"):
                control_ip = datalist[4].lstrip().rstrip()
        if not control_ip:
            print "Could not find a running control node in your list of deployed nodes! Please verify that your control node is up and running and that \
    its presence has been recognized and added to the Fuel database."
            quit()
             
        print "The IP of your control node appears to be %s"%control_ip
    # If there is only one environment deployed, get the control node IP for the 
    # default environment
    else:
        stdin,stdout,stderr = master_ssh.exec_command("fuel node list")
        for line in stdout.readlines():
            datalist = line.split("|")
            if ("controller" in datalist[6]) and (datalist[1].lstrip().rstrip() == "ready"):
                control_ip = datalist[4].lstrip().rstrip()
        if not control_ip:
            print "Could not find a running control node in your list of deployed nodes! Please verify that your control node is up and running and that \
    its presence has been recognized and added to the Fuel database."
            quit() 
        print "The IP of your control node appears to be %s"%control_ip          
    # Get root dir of master node. Almost always is /root but this is safer and for some reason 
    # paramiko does not like ~ expansion.
    stdin,stdout,stderr = master_ssh.exec_command("echo ~/")
    master_root = stdout.read().rstrip("\n")
    scripts_dir = os.path.join(master_root,"scripts")
    rc_file_name = os.path.split(rc_file_path)[1]
    remote_rcfile_loc = os.path.join(scripts_dir,rc_file_name)
    # Add any scripts you would like to be copied here. Make sure they exist in the same directory
    # as this script. 
    script_names = [rc_file_name,"collect_existing_resources.sh","get_net_info.sh","get_instance_info.sh"]
    # Open secure file transfer and copy all scripts to Fuel master node
    master_ftp = master_ssh.open_sftp()
    print "Staging resource collection scripts ..."
    for script in script_names:
        localpath = os.path.join(os.getcwd(),script)
        destpath = os.path.join(scripts_dir,script)
        try:
            master_ftp.put(localpath,destpath)
            master_ftp.chmod(destpath,1)
        except IOError:
            master_ftp.mkdir(scripts_dir)
            master_ftp.put(localpath,destpath)
            master_ftp.chmod(destpath,1)    
    # Execute the main resource collection script and collect/display the output 
    print "Success! Executing resource collection scripts ..."
    
    # Get password used to source RC file
    OS_passwd = getpass.getpass("What is your Openstack password? (This is the password you use to log in to the Horizon Dashboard): ")
    
    stdin,stdout,stderr = master_ssh.exec_command("./scripts/collect_existing_resources.sh %s %s %s %s"%(control_ip,remote_rcfile_loc,rc_file_name,OS_passwd))
    text = stdout.read()
    # Split script output on the table separator, specified in collect_existing_resources.sh. Use regex to split
    # the output and grab the command corresponding to the table out of the center of the separator 
    text = re.split("#[\*]+([^\*]+)[\*]+#",text)
    # Remove the empty first element
    del text[0]
    result_dict = {}
    # Loop through split output. Every even element (including 0) is the command and every following 
    # odd element is the table. Build the user output
    usr_output = """"""
    for i in range(0,len(text),2):
        cmd = text[i]
        cmd = cmd.strip()
        table = text[i+1]
        usr_output += "\nHere are the results of running >> %s << on the control node"%cmd
        usr_output += table
        data = sT.TableParser(table)
        result_dict[cmd] = data
    # Retrieve more detailed information about each network
    network_info = {}
    for network in result_dict["neutron net-list"]:
        name = network["name"]
        stdin,stdout,stderr = master_ssh.exec_command("./scripts/get_net_info.sh %s %s %s %s %s"%(control_ip,remote_rcfile_loc,rc_file_name,OS_passwd,name))
        text = stdout.read()
        text = text.strip("Please enter your OpenStack Password:")
        data = sT.TableParser(text) 
        # Remove the Field, Value key nonsense and make a normal dictionary where key is the property
        # and value is the state of that property
        data = { el["field"]:el["value"] for el in data}       
        network_info[name] = data
    result_dict["neutron net-show"] = network_info
    # Retrieve more detailed information about each instance
    instance_info = {}
    for instance in result_dict["nova list"]:
        name = instance["name"]
        stdin,stdout,stderr = master_ssh.exec_command("./scripts/get_instance_info.sh %s %s %s %s %s"%(control_ip,remote_rcfile_loc,rc_file_name,OS_passwd,name))
        text = stdout.read()
        text = text.strip("Please enter your OpenStack Password:")
        data = sT.TableParser(text)
        data = { el["property"]:el["value"] for el in data} 
        instance_info[name] = data
    result_dict["nova show"] = instance_info
        
    print "Success! Please see below for information about what already exists in your virtual environment"
    time.sleep(2)
    print "#"*150
    print "#"*150
    print usr_output
    print "#"*150
    print "#"*150
    print "!!IMPORTANT NOTE!! Please DO NOT deploy any new resources with the same name as any of \
the resources shown above, as this can cause conflicts and \nerrors during deployment"
    stdin.close()
    stdout.close()
    stderr.close()
    master_ftp.close()
    master_ssh.close()
    
    return result_dict, control_ip
################################################################################
def BuildExistingInfrastructureObject(existing_resources,master_IP,master_usrname,master_pass,template_version):

    # Build an object that will contain all the information about the pre-existing environment in 
    # an organized and easily accessible way
    ExistingInfrastructure = cL.OpenStack_Virtual_Infrastructure(template_version)
    network_info = existing_resources["neutron net-list"]
    more_network_info = existing_resources["neutron net-show"]
    for network in network_info:
        name = network['name']
        props = more_network_info[name]
        attributes = {"admin_state_up":props["admin_state_up"],"name":name,"status":props["status"],"subnets":props['subnets'],'tenant_id':props['tenant_id'],'id':network['id'],'router:external':props['router:external']}
        properties = {"admin_state_up":props["admin_state_up"],"name":name,"shared":props["shared"],"tenant_id":props["tenant_id"]}
        ExistingInfrastructure.AddNetwork(name,attributes,properties)
    subnet_info = existing_resources['neutron subnet-list']
    for subnet in subnet_info:
        name = subnet['name']
        ID = subnet['id']
        # Find the parent network
        for network_key,network_obj in ExistingInfrastructure.GetObjectType('Network').iteritems():
            if ID in network_obj.attributes['subnets']:
                network_id = network_obj.attributes['id']
                tenant_id = network_obj.attributes['tenant_id']
        allocation_pools = str(subnet['allocation_pools'].split(','))
        allocation_pools = allocation_pools.replace("'","")
        properties = {'name':name,'network':network_id,'tenant_id':tenant_id,'allocation_pools':allocation_pools,'cidr':subnet['cidr']}
        attributes = subnet.copy()
        attributes['network_id'] = network_id
        attributes['tenant_id'] = tenant_id
        ExistingInfrastructure.AddSubnet(name,attributes,properties)
    image_info = existing_resources["glance image-list"] 
    for image in image_info:
        properties = {key.lower().replace(" ","_"):value for key,value in image.iteritems()}
        del properties['status']
        del properties['size']
        ExistingInfrastructure.AddImage(properties['name'],image,properties)
    flavor_info = existing_resources["nova flavor-list"]
    for flavor in flavor_info:
        properties = {key.lower().replace(" ","_"):value for key,value in flavor.iteritems()}
        ExistingInfrastructure.AddFlavor(properties['name'],flavor,properties)
    volume_info = existing_resources["cinder list"]
    for volume in volume_info:
        volume = {key.lower().replace(" ","_"):value for key,value in volume.iteritems()}
        properties = volume.copy()
        properties['name'] = properties['display_name']
        for prop in ('display_name','id','attached_to','bootable','status'):
            del properties[prop]
        volume['attachments'] = volume['attached_to'] 
        del volume['attached_to']
        ExistingInfrastructure.AddVolume(properties['name'],volume,properties)
    instance_info = existing_resources["nova list"]
    for instance in instance_info:
        properties = {key.lower().replace(" ","_"):value for key,value in instance.iteritems()}
        raw_props = existing_resources['nova show'][properties['name']]
        properties['flavor'] = raw_props['flavor'].split().pop(0)
        net_info = properties['networks'].split(";")
        networks = []
        for network in net_info:
            items = network.split("=")
            net_name = items[0].strip()
            ip = items[1].strip()
            name_tup = ("network",net_name)
            ip_tup = ('fixed_ip',ip)
            networks.append(name_tup)
            networks.append(ip_tup)
        properties['networks'] = networks
        for key in ('power_state','task_state','id','status'):
            del properties[key]
        properties['image'] = raw_props['image'].split().pop(-1).lstrip('(').rstrip(')')
        ExistingInfrastructure.AddInstance(properties['name'],raw_props,properties)

    return ExistingInfrastructure
################################################################################
def CheckOldResources(new_name, existing_resources, object_type):
    object_key = object_type+"_"+new_name
    n = 0
    while object_key in existing_resources.resources.keys():
        new_name = str(raw_input("That name is already in use by an existing resource! Please pick another one: "))
        new_name = str(sT.ResponseLoop(new_name,"^\S+$","Your name did not match the expected pattern. Please ensure there are no spaces and try again: "))
        n += 1 
        if n >= 5:
            print "Exceed limit of 5 attempts. Review your existing resources and try again."
            quit()
    return new_name             
################################################################################   
def BuildNewInfrastructure(existing_infrastructure, template_version):
    # Instantiate new virtual infrastructure object
    NewInfrastructure = cL.OpenStack_Virtual_Infrastructure(template_version)
    # Instantiate hydrid infrastructure object by initializing from old infrastructure
    HybridInfrastructure = copy.deepcopy(existing_infrastructure)
    # Add all the networks
    prompt = "How many networks would you like in your environment?: "
    num_nets = raw_input(prompt)
    num_nets = int(sT.ResponseLoop(num_nets,"^[0-9]+$",prompt))
    prompt = "Please enter the name you wish to give this network. There must be no spaces: "
    for i in range(1,num_nets+1):
        print "Building network %i"%i
        net_name = raw_input(prompt)
        net_name = sT.ResponseLoop(net_name,'^\S+$',prompt)
        net_name = str(CheckOldResources(net_name,HybridInfrastructure,"Network"))
        NewInfrastructure.AddNetwork(net_name,{},{})
        HybridInfrastructure.AddNetwork(net_name,{},{})
    # Add all the subnets to each network
    networks = NewInfrastructure.GetObjectType("Network")
    for network_name,network_object in networks.iteritems():
        prompt = "How many subnets would you like to add to the network named \"%s\"?: "%network_object.name
        num_subnets = raw_input(prompt)
        num_subnets = int(sT.ResponseLoop(num_subnets,"^[0-9]+$",prompt))
        for i in range(1,num_subnets+1):
            print "Building subnet %i"%i
            prompt = "Please enter the name you wish to give this subnet. There must be no spaces: "
            subnet_name = raw_input(prompt)
            subnet_name = sT.ResponseLoop(subnet_name,'^\S+$',prompt)
            subnet_name = str(CheckOldResources(subnet_name,HybridInfrastructure,"Subnet"))
            prompt = "Please enter the CIDR for this subnet: "
            cidr = raw_input(prompt)
            cidr = sT.ResponseLoop(cidr,'^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+/[0-9]+$',prompt)
            NewInfrastructure.AddSubnet(subnet_name,{'network_id':network_name},{"cidr":cidr,"network_id":"{ get_resource: %s }"%network_object.name})
            HybridInfrastructure.AddSubnet(subnet_name,{'network_id':network_name},{"cidr":cidr,"network_id":"{ get_resource: %s }"%network_object.name})
            network_object.UpdateSubnets(subnet_name)
    # Create all the routers and router interfaces needed to interconnect subnets
    prompt = "How many routers would you like in your environment?: "
    num_routers = raw_input(prompt)
    num_routers = int(sT.ResponseLoop(num_routers,"^[0-9]+$",prompt))
    for i in range(1,num_routers+1):
        print "Building router %i"%i
        prompt = "Please enter the name you wish to give this router. There must be no spaces: "
        router_name = raw_input(prompt)
        router_name = str(sT.ResponseLoop(router_name,'^\S+$',prompt))
        router_name = str(CheckOldResources(router_name,HybridInfrastructure,"Router"))
        ext_nets = []
        # Ask the user which external network they would like to use for the external gateway of the router
        for network_name,network_obj in HybridInfrastructure.GetObjectType("Network").iteritems():
            if ('router:external' in network_obj.attributes) and (network_obj.attributes['router:external'] == 'True'):
                ext_nets.append(network_name)    
        prompt = "What external network would you like to use to give this router internet access? Please choose from %s: "%str(ext_nets)
        ext_gateway = raw_input(prompt)
        ext_gateway = str(sT.ResponseLoop(ext_gateway,'^\S+$',prompt))
        while ext_gateway not in ext_nets:
            ext_gateway = str(sT.ResponseLoop(ext_gateway,'^\S+$',prompt))   
        NewInfrastructure.AddRouter(router_name,{},{"external_gateway_info":"{ network: %s }"%ext_gateway}) #!!! REMOVE THIS HARD CODING!!!!
        HybridInfrastructure.AddRouter(router_name,{},{"external_gateway_info":"{ network: %s }"%ext_gateway}) #!!! REMOVE THIS HARD CODING!!!!
        prompt = "Which subnets would you like to connect this router to? Please enter the subnet names as a comma separated list with no spaces: "
        subnet_names_str = raw_input(prompt)
        subnet_names_str = sT.ResponseLoop(subnet_names_str,'([\S+][,\S+]*)',prompt)
        subnet_names_list = subnet_names_str.split(",")
        for subnet_name in subnet_names_list:
            interface_name = router_name+"_to_"+subnet_name+"_interface"
            NewInfrastructure.AddRouterInterface(interface_name,NewInfrastructure.resources["Router_"+router_name],NewInfrastructure.resources["Subnet_"+subnet_name])
            HybridInfrastructure.AddRouterInterface(interface_name,HybridInfrastructure.resources["Router_"+router_name],HybridInfrastructure.resources["Subnet_"+subnet_name])
    # Create all instances
    prompt = "How many virtual machines would you like in your environment?: "
    num_instances = raw_input(prompt)
    num_instances = int(sT.ResponseLoop(num_instances,"^[0-9]+$",prompt))     
    for i in range(num_instances):
        print "Building instance %i"%i
        prompt = "Please enter the name you wish to give this instance. There must be no spaces: "
        inst_name = raw_input(prompt)
        inst_name = str(sT.ResponseLoop(inst_name,'^\S+$',prompt))
        inst_name = str(CheckOldResources(inst_name,HybridInfrastructure,"Instance"))
        prompt = "What flavor would you like to use to specify the virtual resources of this instance? Please choose from %s: "%str(existing_infrastructure.GetObjectType("Flavor").keys())
        flavor = raw_input(prompt)
        flavor = str(sT.ResponseLoop(flavor,'^\S+$',prompt))
        while flavor not in existing_infrastructure.GetObjectType("Flavor").keys():
            flavor = str(sT.ResponseLoop(flavor,'^\S+$',prompt))
        prompt = "What image would you like to use to boot this instance? Please choose from %s: "%str(existing_infrastructure.GetObjectType("Image").keys())
        image = raw_input(prompt)
        image = str(sT.ResponseLoop(image,'^\S+$',prompt))
        while image not in existing_infrastructure.GetObjectType("Image").keys():
            image = str(sT.ResponseLoop(image,'^\S+$',prompt))
        # Create all the network ports and attach them to subnets. Create list of port attachments for instance
        prompt = "Which subnets would you like to connect this instance to? Please enter the subnet names as a comma separated list with no spaces: "
        subnet_names_str = raw_input(prompt)
        subnet_names_str = sT.ResponseLoop(subnet_names_str,'([\S+][,\S+]*)',prompt)
        subnet_names_list = subnet_names_str.split(",")
        ports = []
        for subnet in subnet_names_list:
            subnet_obj = NewInfrastructure.GetObject("Subnet",subnet)
            network_obj = NewInfrastructure.GetObject('Network',subnet_obj.attributes['network_id'])
            name = inst_name+'_to_'+subnet+'_port'
            ports.append(('port','{ get_resource: %s }'%name))
            NewInfrastructure.AddNetworkPort(name,network_obj,subnet_obj)
            HybridInfrastructure.AddNetworkPort(name,network_obj,subnet_obj)
        # Add instances to virtual infrastructure
        NewInfrastructure.AddInstance(inst_name,{},{'name':inst_name,'image':image,'flavor':flavor,'networks':ports})
        HybridInfrastructure.AddInstance(inst_name,{},{'name':inst_name,'image':image,'flavor':flavor,'networks':ports})
    # Build template files 
    with open("new_infrastructure.yaml",'w+') as template_file:
        template_file.write(NewInfrastructure.__repr__())
    with open("old_infrastructure.yaml",'w+') as template_file:
        template_file.write(existing_infrastructure.__repr__())
    with open("hybrid_infrastructure.yaml",'w+') as template_file:
        template_file.write(HybridInfrastructure.__repr__())
################################################################################
def DeployEnvironment(fuel_IP,fuel_usr,fuel_passwd,control_ip,rc_file_path):
    master_ssh = sT.CreateSSHConnection(fuel_IP,fuel_usr,fuel_passwd)
    # Get root dir of master node. Almost always is /root but this is safer and for some reason 
    # paramiko does not like ~ expansion.
    stdin,stdout,stderr = master_ssh.exec_command("echo ~/")
    master_root = stdout.read().rstrip("\n")
    stdin.close()
    stdout.close()
    stderr.close()
    scripts_dir = os.path.join(master_root,"scripts")
    rc_file_name = os.path.split(rc_file_path)[1]
    remote_rcfile_loc = os.path.join(scripts_dir,rc_file_name)
    # Add any template files and scripts you would like to be copied here. Make sure they exist 
    # in the same directory as this script. 
    file_names = [rc_file_name,"new_infrastructure.yaml","old_infrastructure.yaml","hybrid_infrastructure.yaml","deploy_stack.sh"]
    # Open secure file transfer and copy all files to Fuel master node
    master_ftp = master_ssh.open_sftp()
    print "Staging template files and deployment scripts ..."
    for script in file_names:
        localpath = os.path.join(os.getcwd(),script)
        destpath = os.path.join(scripts_dir,script)
        try:
            master_ftp.put(localpath,destpath)
            if script == "deploy_stack.sh":
                master_ftp.chmod(destpath,1)
        except IOError:
            master_ftp.mkdir(scripts_dir)
            master_ftp.put(localpath,destpath) 
            if script == "deploy_stack.sh":
                master_ftp.chmod(destpath,1)  
    print "Success! Executing script to deploy the requested environment!"
            
             
    # Get password needed to source RC file
    OS_passwd = getpass.getpass("What is your Openstack password? (This is the password you use to log in to the Horizon Dashboard): ")

    # Execute deploy_stack to deploy environment specified by template file
    stdin,stdout,stderr = master_ssh.exec_command("./scripts/deploy_stack.sh %s %s %s %s %s"%(control_ip,remote_rcfile_loc,rc_file_name,OS_passwd,"new_infrastructure.yaml"))
    out = stdout.read()
    err = stderr.read()
    print out
    print err
    print "Success! You can view the progress of your deployment from the Horizon Dashboard"
    
################################################################################
def main():
    
    parser=argparse.ArgumentParser(description="""A script for creating Heat Openstack Orchestation YAML template file and executing the template file as a "stack" 
will automatically deploy the requested virtual environment. This script must be executed on a Unix/Linux machine with SSH capabilities. It also requires Python 2.7+ 
and a few external Python libraries. Attempting to run the script will immediately identify any missing libraries.""")
    parser.add_argument('--template_version',type=str,default="2013-05-23",help="The template file version. Please see the Heat documentation for details")
    parser.add_argument('env_RCfile',type=str,help="Absolute path to the evironment RC file that is sourced by any remote scripts to set the environment variables necessary for using service CLIs")
    args= parser.parse_args()
       
    print "\n"+"#"*88+"\n"
    print """Hello! This script will attempt to walk you through the process of specifying
the resources you wish to deploy in your virtual Openstack infrastructure. It will then 
automatically deploy that set of resources for you. Note you will need the IP address of
your Fuel Master Node,the root username, the root password, and the cababiliy to SSH 
into that node."""
    print "\n"+"#"*88+"\n"
    
    # Get the SSH connection credentials for the user's Fuel Master Node.
    fuel_mstr_ip = str(raw_input("Please type the IP address of your Fuel Master Node: "))
    sT.CheckUserInput(fuel_mstr_ip,'[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+')
    fuel_usr = str(raw_input("Please type the root user name for your Fuel Master Node. There must be no spaces: "))
    sT.CheckUserInput(fuel_usr,'^\S+?')
    fuel_passwd = getpass.getpass(prompt="Enter root password:")
    
    # Verify network connectivity to Fuel Master Node
    sT.pingTest(fuel_mstr_ip)
    
    # Establish connection
    fuel_master_ssh = sT.CreateSSHConnection(fuel_mstr_ip,fuel_usr,fuel_passwd)
    
    # Get the dictionary that has all the information about the preexisting resources in the user's virtual environment
    existing_resources, control_IP = CollectExistingResources(fuel_master_ssh,args.env_RCfile)

    # Build the object that organizes and contains information about all the existing virtual infrastructure 
    existing_infrastructure = BuildExistingInfrastructureObject(existing_resources,fuel_mstr_ip,fuel_usr,fuel_passwd,args.template_version)
    
    # Poll the user about the resources they would like to create/add. Use their responses to build a new virtual infrastructure
    BuildNewInfrastructure(existing_infrastructure,args.template_version)
    
    # Copy files to control node and use Heat to deploy environment 
    DeployEnvironment(fuel_mstr_ip,fuel_usr,fuel_passwd,control_IP,args.env_RCfile)
    
if __name__=='__main__':
    main()
