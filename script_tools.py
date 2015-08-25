#####################################################################################################
# Script: script_tools.py
# Author: Kyle Robertson
# Date: August 11, 2015
# Company: Worlcom Exchange Inc.
# Description: This module provides some simple, reusable functions for other scripts
#####################################################################################################

try:
    import subprocess
    import re 
    import paramiko
    import os
except ImportError, output:
    print "%s installed on your machine or within your current Python environment. \
Please install that package and re-run this script."%output
    quit()

################################################################################ 
def sh(cmd):
    '''Executes commands directly to the native bash shell using subprocess.Popen, and retrieves stdout and stderr. 
    
    !!!IMPORTANT NOTE!!!: Passing unsanitized input into this function can be a huge security threat. Tread carefully. 
    !!!IMPORTANT NOTE!!!: Passing in a command that generates excessive output might freeze the program depending on buffer sizes
    Useage: out, err = sh(bash_command)
    Input: - bash_command: string
    Output: - out: string
            - err: string'''
    return subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE).communicate()
################################################################################
def pingTest(ip):
    '''Tests network connectivity to an IP address by pinging it.
    Useage: pingTest(IP_address)
    Input: - IP_address: string
    Output: None'''
    print "\nAttempting to ping the IP address %s ..."%ip
    out, err = sh("ping -t 2 %s"%ip)
    if "Request timeout" in out:
        print "\nIt seems that you do not have IP connectivity to %s. Check your \
network configuration and re-try\n"%ip
        quit()
    else:
        print "\n !! Network connectivity verified !! \n "
################################################################################    
def CheckUserInput(usr_input,regex):
    '''Checks to see if user input matches the expected useage pattern. If not, it quits
    Useage: CheckUserInput(user_input,regex_pattern)
    Input: - user_input: string
           - regex: string. Uses standard regular expression syntax
    Output: None'''
    search = re.search(regex,usr_input)    
    if search:
        inputmatch = search.group(0)
        return inputmatch
    else:
        print "\nWARNING! The user input does not match the intended pattern! Quitting now! \n"
        quit()
################################################################################
def ResponseLoop(usr_input,regex,prompt):
    '''Checks to see if user input matches the expected useage pattern. If not, it enters
a loop that gives the user 5 attempts to enter the corrent input. After 5 attempts, it quits.
    Useage: CheckUserInput(user_input,regex_pattern,input_prompt)
    Input: - user_input: string
           - regex: string. Uses standard regular expression syntax
           - input_prompt: string. Prompt to give user when requesting input
    Output: inputmatch: - string. User input that matches expected pattern'''
    search = re.search(regex,usr_input)
    if search:
        inputmatch = search.group(0)
        return inputmatch 
    else:
        test = False
        n = 0
        while not test:
            print "Your input does not match the expected pattern. Please try again"
            user_input = raw_input(prompt)
            search = re.search(regex,user_input)
            if search:
                test = True
                inputmatch = search.group(0)
                return str(inputmatch)
            else:
                n += 1
                if n >= 5:
                    print "Exceeded maximum of 5 attempts. Quitting now"
                    quit()
################################################################################
def CreateSSHConnection(IP,username,password):
    '''Checks to see if user input matches the expected useage pattern. If not, it quits
    Useage: CheckUserInput(user_input,regex_pattern)
    Input: - IP: string
           - username: string. Must lack any whitespace
           - password: string
    Output: - paramiko SSHClient object'''
    
    print "Attempting to establish the SSH connection ..."
    ssh = paramiko.SSHClient()
    try:
        ssh.load_host_keys(os.path.expanduser(os.path.join("~", ".ssh", "known_hosts")))
        ssh.connect(IP,username=username,password=password)
        return ssh
    except paramiko.ssh_exception.SSHException:
        print "It appears that the public key of the remote server you are trying \
to acces is not located in your known_keys file. This script can add the server's \
public key to your ~/.ssh/known_keys file if you would like. If not this script \
will exit"
        inpt = str(raw_input("Would you like to add the target server's public key?(y/n): "))
        while not (inpt=="y" or inpt =="n"):
            inpt = str(raw_input("Please enter either y or n: "))
        if inpt == "y":
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(IP,username=username,password=password)
            return ssh
        else:
            ssh.close()
            quit()
################################################################################
def TableParser(text):
    '''Parses the tables/text spit out by the service resource list commands in 
Openstack. 
    Useage: TableParser(table_string)
    Input: - text: string. Can be any of the table types or just lines of text
    Output: - list. Each element of this list is a row of the table.'''
    # Check to see if the text is a table
    text = text.strip("\n")
    if "|" in text:
        # Check to see if it's a boxed table
        if text[0] == "+":
            # Its a table with an outer box. Split the rows
            text = text.splitlines()
            # Remove the borders
            del text[0]
            del text[1]
            del text[-1]
            # Split each row of the table into a list where each list element is 
            # one of the cells in that row
            for i in range(len(text)):
                text[i] = text[i].split("|")
                del text[i][0]
                del text[i][-1]
                text[i] = [string.strip() for string in text[i]]  
            # Check for any row entries that span multiple lines and fix them
            del_list = []
            for n in range(1,len(text)):
                row = text[n]
                true_els = len(filter(None,row))
                false_els = len(row) - true_els
                # If the number of empty elements is greater than the number of filled elements
                # this row is supposed to be additional data in cells of the previous row. So
                # fix it
                if false_els > true_els:
                    prev_row = text[n-1]
                    for i in range(len(row)):
                        prev_row[i] = prev_row[i]+","+row[i]
                        prev_row[i] = prev_row[i].strip(', ')
                    text[n-1] = prev_row
                    del_list.append(n)
            for ind in del_list:
                del text[ind]
            # Get the headers
            headers = text.pop(0)
            headers = [header.lower().replace(" ","_") for header in headers]
            # Build the list of dictionaries. Each row in the table gets its own dictionary
            # so each element of this list corresponds to a row in the table. The keys of the 
            # dict are the column headers, values the value of the header cell in that particular
            # row
            data = [{headers[i]: row[i] for i in range(len(row))} for row in text]
            return data
        else:
            # its an unboxed table. Split the rows
            text = text.splitlines()
            # Remove the separator between headers and body
            del text[1]
            for i in range(len(text)):
                text[i] = text[i].split("|")
                text[i] = [string.lstrip().rstrip() for string in text[i]]
            # Get the headers
            headers = text.pop(0)
            # Build the list of dictionaries
            data = [{headers[i]: row[i] for i in range(len(row))} for row in text]
            return data    
    elif text:
        # Its just plain rows of text
        data = text.splitlines() 
        return data
    else:
        return None
################################################################################        
