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
except ImportError,output:
    print "%s installed on your machine or within your current Python environment. \
Please install that package and re-run this script."%output
    quit()

################################################################################ 
class BaseObject:
    def __init__(self, service, resource, resourcename, properties): ## properties should be a dictionary
        self.type = "OS::%s::%s"%(service,resource)
        self.name = resourcename 
        self.properties = properties
    def __repr__(self):
        base = """%s:
    type: %s
    properties:""" % (self.name,self.type)
        for prop, val in self.properties.iteritems():
            if type(val) == dict:
                base += "\n        %s:"%prop
                for subprop, subval in val.iteritems():
                    base += "\n            - %s: %s"%(subprop,subval)
            else:
                base += "\n        %s: %s"%(prop,val)
        return base
################################################################################   
def sh(cmd):
    return subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE).communicate()
################################################################################     
def CollectExistingResources(master_ssh):
        
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
    # Get root dir of master node. Almost always is /root but this is safer and for
    # some reason paramiko does not like ~ expansion. Build file copy paths
    stdin,stdout,stderr = master_ssh.exec_command("echo ~/")
    master_root = stdout.read().rstrip("\n")
    scripts_dir = os.path.join(master_root,"scripts")
    script = "collect_existing_resources.sh"
    localpath = os.path.join(os.getcwd(),script)
    destpath = os.path.join(scripts_dir,script)
    # Copy the resource harvesting BASH script to the master node
    print "Staging resource collection script ..."
    master_ftp = master_ssh.open_sftp()
    try:
        master_ftp.put(localpath,destpath)
        master_ftp.chmod(destpath,1)
    except IOError:
        master_ftp.mkdir(scripts_dir)
        master_ftp.put(localpath,destpath)
        master_ftp.chmod(destpath,1)

    # Execute the script and collect/display the output
    #!!!!!!!!!!!! Need to figure out how to handle putting the correct RC files that control environment variables
    #!!!!!!!!!!!! on the control node. The admin RC file is placed there by default but that shouldn't be relied on
    #!!!!!!!!!!!! and also does not handle tenant use cases. 
    print "Success! Executing resource collection script ..."
    stdin,stdout,stderr = master_ssh.exec_command("./scripts/collect_existing_resources.sh %s"%control_ip)
    text = stdout.read()
    text = re.split("#[\*]+([^\*]+)[\*]+#",text)
    del text[0]
    result_dict = {}
    print "Success! Please see below for information about your virtual environment"
    time.sleep(2)
    print "#"*150
    print "#"*150
    for i in range(0,len(text),2):
        cmd = text[i]
        cmd = cmd.lstrip().rstrip()
        table = text[i+1]
        print "\nHere are the results of running >> %s << on the control node"%cmd
        print table
        data = sT.TableParser(table)
        result_dict[cmd] = data
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
def main():
    
    parser=argparse.ArgumentParser(description="""A script for creating a YAML template file to be executed by HEAT Openstack Orchestation""")
    parser.add_argument('--template_version',type=str,default="2013_05_23")
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
    # Collect information about all the preexisting resources in the user's virtual environment
    existing_resources = CollectExistingResources(fuel_master_ssh)
    #with open("test_stack.yaml",'a+') as template:
    #    # Prepare the file with proper version
    #    template.write("heat_template_version: %s\n\nresources:\n"%args.template_version)
        
    
    #props = {"image" : "Ubuntu12.05", "ram" : "8GB","networks":{"private":"10.20.5.0/24","public":"10.20.2.0/24"}}
    #test = BaseObject("Neutron","Server","SampleInstance", props)
    #print test
    
if __name__=='__main__':
    main()
