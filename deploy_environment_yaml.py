#####################################################################################################
# Script: deploy_environment.py
# Author: Kyle Robertson
# Date: August 11, 2015
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
    if len(lines) > 3:
        environments = lines[1:]
        env_ids = []
        for env in environments:
            if env[1] == "operational":
                env_ids.append(env[0])
        print env_ids
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
    script_names = [rc_file_name,"collect_existing_resources.sh","collect_existing_resources_yaml.sh","get_net_info.sh","get_instance_info.sh"]
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
    
    #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    #OS_passwd = getpass.getpass("What is your Openstack password? (This is the password you use to log in to the Horizon Dashboard): ")
    OS_passwd = "admin"
    #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    
    stdin,stdout,stderr = master_ssh.exec_command("./scripts/collect_existing_resources.sh %s %s %s %s"%(control_ip,remote_rcfile_loc,rc_file_name,OS_passwd))
    text = stdout.read()
    # Split script output on the table separator, specified in collect_existing_resources.sh. Use regex to split
    # the output and grab the command corresponding to the table out of the center of the separator 
    text = re.split("#[\*]+([^\*]+)[\*]+#",text)
    # Remove the empty first element
    del text[0]
    # Loop through split output. Every even element (including 0) is the command and every following 
    # odd element is the table. Build the user output for pretty display
    usr_output = """"""
    for i in range(0,len(text),2):
        cmd = text[i]
        cmd = cmd.lstrip().rstrip()
        table = text[i+1]
        usr_output += "\nHere are the results of running >> %s << on the control node"%cmd
        usr_output += table

    # Execute YAML resource collection script to be used for building existing infrastructure object
    stdin,stdout,stderr = master_ssh.exec_command("./scripts/collect_existing_resources_yaml.sh %s %s %s %s"%(control_ip,remote_rcfile_loc,rc_file_name,OS_passwd))
    data = stdout.read()
    print data
    quit()
    result_dict = {}
    # For the YAML output of every command executed in the above script, use the 
    # pyYAML module to convert the output to useable python objects
    for cmd_data in yaml.load_all(data):
        print cmd_data
        # The output of a command is stored as a list. The first element is a dictionary containing the command itself as
        # {"command" : ACTUAL_COMMAND}. Pop that element off the list and retrieve the actual command
        cmd = cmd_data.pop(0)["command"]
        # The remaining elements are dictionaries containing all the information about the objects presented by the command.
        # Think of these dictionaries as the rows in the table, each row corresponding to a unique object 
        # If the data was in table format, the keys would be the headers and the values are the value corresponding to that 
        # header for a particular object. Add the command to the result_dict as a key, the list of object dicts corresponding
        # to the command as the value. 
        result_dict[cmd] = cmd_data
        
    # Retrieve more detailed information about each network. All the more specific info about each network is stored
    # in a dictionary. The key of that dictionary is the network name, the value is a list. Each element of the list
    # is a dictionary of the form { 'Field' : 'FIELD_VAL', 'Value' : 'ACTUAL_VAL' }
    network_info = {}
    for network in result_dict["neutron net-list"]:
        name = network["name"]
        stdin,stdout,stderr = master_ssh.exec_command("./scripts/get_net_info.sh %s %s %s %s %s"%(control_ip,remote_rcfile_loc,rc_file_name,OS_passwd,name))
        text = stdout.read()
        data = yaml.load(text)        
        network_info[name] = data
    result_dict["neutron net-show"] = network_info
    # Retrieve more detailed information about each instance. The format here mimics that above
    instance_info = {}
    for instance in result_dict["nova list"]:
        name = instance["name"]
        stdin,stdout,stderr = master_ssh.exec_command("./scripts/get_instance_info.sh %s %s %s %s %s"%(control_ip,remote_rcfile_loc,rc_file_name,OS_passwd,name))
        text = stdout.read()
        data = yaml.load(text)
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
    
    return result_dict
################################################################################
def BuildExistingInfrastructureObject(existing_resources,master_IP,master_usrname,master_pass,template_version):

    # Build an object that will contain all the information about the pre-existing environment in 
    # an organized and easily accessible way
    ExistingInfrastructure = sT.OpenStackVirtualInfrastructure(template_version)
    network_info = existing_resources["neutron net-list"]
    for network in network_info[1:]:
        name = network[1]
        raw_props = existing_resources["neutron net-show"][name]
        attributes = {}
        for prop in raw_props:
            attributes[prop[0]] = prop[1]
        properties = {"admin_state_up":attributes["admin_state_up"],"name":attributes["name"],"shared":attributes["shared"],"tenant_id":attributes["tenant_id"]}
        NetworkObject = sT.BasicObject("Neutron","Net",name,attributes,properties)
        ExistingInfrastructure.AddNetwork(NetworkObject)
    image_info = existing_resources["glance image-list"]
    for image in image_info[1:]:
        uuid = image[0]
        name = image[1]
        disk_format = image[2]
        container_format = image[3]
        size = image[4]
        properties = {"name":name,"uuid":uuid,"disk_format":disk_format,"container_format":container_format,"size":size}
        attributes = properties
        ImageObject = sT.BasicObject("Glance","Image",name,attributes,properties)
        ExistingInfrastructure.AddImage(ImageObject)
    flavor_info = existing_resources["nova flavor-list"]
    for flavor in flavor_info[1:]:
        uuid = flavor[0]
        name = flavor[1]
        ram = flavor[2]
        disk = flavor[3]
        ephemeral = flavor[4]
        swap = flavor[5]
        vcpus = flavor[6]
        rxtx_factor = flavor[7]
        properties = {"name":name,"uuid":uuid,"ram":ram,"disk":disk,"ephemeral":ephemeral,"swap":swap,"vcpus":vcpus,"rxtx_factor":rxtx_factor}
        attributes = properties
        FlavorObject = sT.BasicObject("Nova","Flavor",name,attributes,properties)
        ExistingInfrastructure.AddFlavor(FlavorObject)
    volume_info = existing_resources["cinder list"]
    for volume in volume_info[1:]:
        uuid = volume[0]
        status = volume[1]
        name = volume[2]
        size = volume[3]
        volume_type = volume[4]
        attachments = volume[5]
        properties = {"name":name,"volume_type":volume_type,"size":size}
        attributes = {"id":uuid,"status":status,"name":name,"volume_type":volume_type,"size":size,"attachments":attachments}
        VolumeObject = sT.BasicObject("Cinder","Volume",name,attributes,properties)
        ExistingInfrastructure.AddVolume(VolumeObject)
    instance_info = existing_resources["nova list"]
    for instance in instance_info[1:]:
        uuid = instance[0]
        name = instance[1]
        networks = instance[5].split(";")
        networks_dict = {}
        for i in range(len(networks)):
            net_info = [el.lstrip().rstrip() for el in networks[i].split("=")]
            networks[i] = ("network",net_info[0])
            networks_dict[net_info[0]] = net_info[1]
        raw_props = existing_resources["nova show"][name]
        attributes = {}
        for prop in raw_props:
            attributes[prop[0]] = prop[1]
        attributes["flavor"] = attributes["flavor"].split()[0]
        properties = {"name":name,"networks":networks,"flavor":attributes["flavor"]}
        InstanceObject = sT.BasicObject("Nova","Server",name,attributes,properties)
        print "Attributes are: ",InstanceObject.attributes
        print "Properties are: ",InstanceObject.properties 
        ExistingInfrastructure.AddInstance(InstanceObject)
    print ExistingInfrastructure

################################################################################
def CheckOldResources(new_name, existing_resources, command):
    old_names = existing_resources[command]
    chain = itertools.chain.from_iterable(old_names)
    n = 0
    while new_name in chain:
        new_name = str(raw_input("That name is already in use by an existing resource! Please pick another one: "))
        new_name = str(sT.ResponseLoop(new_name,"^\S+$","Your name did not match the expected pattern. Please ensure there are no spaces and try again: "))
        n += 1 
        if n >= 5:
            print "Exceed limit of 5 attempts. Review your existing resources and try again."
            quit()
    return new_name             
################################################################################   
def BuildNewInfrastructure(existing_resources, template_version):
    # Instantiate new virtual infrastructure object
    NewInfrastructure = cL.OpenStack_Virtual_Infrastructure(template_version)
    # Add all the networks
    prompt = "How many networks would you like in your environment?: "
    num_nets = raw_input(prompt)
    num_nets = int(sT.ResponseLoop(num_nets,"^[0-9]+$",prompt))
    prompt = "Please enter the name you wish to give this network. There must be no spaces: "
    for i in range(1,num_nets+1):
        print "Building network %i"%i
        net_name = raw_input(prompt)
        net_name = sT.ResponseLoop(net_name,'^\S+$',prompt)
        net_name = str(CheckOldResources(net_name,existing_resources,"neutron net-list"))
        NewInfrastructure.AddNetwork(net_name,{},{})
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
            subnet_name = str(CheckOldResources(subnet_name,existing_resources,"neutron subnet-list"))
            prompt = "Please enter the CIDR for this subnet: "
            cidr = raw_input(prompt)
            cidr = sT.ResponseLoop(cidr,'^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+/[0-9]+$',prompt)
            NewInfrastructure.AddSubnet(subnet_name,{},{"cidr":cidr,"network_id":"{ get_resource: %s }"%network_object.name})
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
        router_name = str(CheckOldResources(router_name,existing_resources,"neutron router-list"))
        NewInfrastructure.AddRouter(router_name,{},{"external_gateway_info":"{ network: net04_ext }"}) # REMOVE THIS HARD CODING!!!!
        prompt = "Which subnets would you like to connect this router to? Please enter the subnet names as a comma separated list with no spaces: "
        subnet_names_str = raw_input(prompt)
        subnet_names_str = sT.ResponseLoop(subnet_names_str,'([\S+][,\S+]*)',prompt)
        subnet_names_list = subnet_names_str.split(",")
        for subnet_name in subnet_names_list:
            interface_name = router_name+"_to_"+subnet_name+"_interface"
            NewInfrastructure.AddRouterInterface(interface_name,NewInfrastructure.resources["Router_"+router_name],NewInfrastructure.resources["Subnet_"+subnet_name])
    # Create all instances
    #prompt = "How many virtual machines would you like in your environment?: "
    #num_instances = raw_input(prompt)
    #num_instances = int(sT.ResponseLoop(num_routers,"^[0-9]+$",prompt))     
    #for i in range(num_instances):
    #    print "Building instance %i"%i
    #    prompt = "Please enter the name you wish to give this instance. There must be no spaces: "
    #    inst_name = raw_input(prompt)
    #    inst_name = str(sT.ResponseLoop(inst_name,'^\S+$',prompt))
    #    inst_name = str(CheckOldResources(inst_name,existing_resources,"nova list"))
    #    prompt = "What flavor would you like to use to specify the virtual resources of this instance? Please choose from %s:"%str()
    
    
    with open("deployment_test.yaml",'w+') as template_file:
        template_file.write(NewInfrastructure.__repr__())
    
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
    #fuel_mstr_ip = str(raw_input("Please type the IP address of your Fuel Master Node: "))
    #sT.CheckUserInput(fuel_mstr_ip,'[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+')
    #fuel_usr = str(raw_input("Please type the root user name for your Fuel Master Node. There must be no spaces: "))
    #sT.CheckUserInput(fuel_usr,'^\S+?')
    #fuel_passwd = getpass.getpass(prompt="Enter root password:")
    fuel_mstr_ip = "10.20.1.4"
    fuel_usr="root"
    fuel_passwd="Worldcom2015"
    
    # Verify network connectivity to Fuel Master Node
    sT.pingTest(fuel_mstr_ip)
    
    # Establish connection
    fuel_master_ssh = sT.CreateSSHConnection(fuel_mstr_ip,fuel_usr,fuel_passwd)
    
    # Get the dictionary that has all the  information about the preexisting resources in the user's virtual environment
    existing_resources = CollectExistingResources(fuel_master_ssh,args.env_RCfile)
    print existing_resources 
    for key, value in existing_resources.iteritems():
        print
        print "KEY: ",key
        print "VALUE: ",value
    quit()
    # Build the object that organizes and contains information about all the existing virtual infrastructure 
    #existing_infrastructure = BuildExistingInfrastructureObject(existing_resources,fuel_mstr_ip,fuel_usr,fuel_passwd,args.template_version)
    
    # Poll the user about the resources they would like to create/add. Use their responses to build a new virtual infrastructure
    new_resources = BuildNewInfrastructure(existing_resources,args.template_version)
    
    #!!!! It might be a nice feature to create a YAML file that can be used to redeploy the existing
    #!!!! environment from the information just collected
    #
    # 1) Use existing resources dictionary to build a full old_infrastructure object for existing resources
    # 2) Build YAML file for old infrastructure 
    # 3) Use old_infrastructure object to fill necessary info for new_infrastructure object (images, flavors, etc.) 
    # 4) Collect input from user to determine new resources 
    # 5) Use new_infrastructure object to build new infrastructure YAML template
    # 6) Send out script that executes new YAML template
    #new_resources = DetermineNewResources(existing_resources)
    #with open("test_stack.yaml",'a+') as template:
    #    # Prepare the file with proper version
    #    template.write("heat_template_version: %s\n\nresources:\n"%args.template_version)
        
    
    #props = {"image" : "Ubuntu12.05", "ram" : "8GB","networks":[("network","public"),("network","private"),("network","test")]}
    #atts = {"thing":"AnImportantThing","AnotherThing":"LessImportantThing"}
    #test = cL.Instance("TestInstance",atts,props)
    #print test
    #string = test.__repr__()
    #print string
    #
if __name__=='__main__':
    main()
