#####################################################################################################
# Script: openstack_objects.py
# Author: Kyle Robertson
# Date: August 11, 2015
# Company: Worlcom Exchange Inc.
# Description: This module defines the classes that represent all the objects/resources contained within an OpenStack Virtual Environment 
#####################################################################################################
try:
    import script_tools as sT 
except ImportError,output:
    print "%s installed on your machine or within your current Python environment. \
Please install that package, or move the module to the directory of this file, and re-run."%output
    quit()
################################################################################ 
class OpenStack_Virtual_Infrastructure(object):
    '''This class is designed to represent an entire Openstack Virtual Infrastructure.
    It is the interface through which scripts/apps interact with individual Openstack
    objects. It contains all the information about the objects that have been 
    instantiated and generates the string representation of the environment that is 
    in valid Heat Template Format. It keeps track of all objects in the environment 
    via a master dictionary containing all object types, where the key is OBJECTTYPE_OBJECTNAME 
    and the value is the instance of the object itself.'''
    #--------------------------------------------------------------------------#
    def __init__(self,template_version):
        self.template_version = template_version
        self.resources = {}
        self.object_types = ["Network","Subnet","NetworkPort","Volume","VolumeAttachment","Instance","Router","RouterInterface","Image","Flavor"]
        # List determines what resources will be skipped when building Heat template
        self.skiplist = ["Image","Flavor"]
    #--------------------------------------------------------------------------#
    def AddNetwork(self,net_name,attributes,properties):
        '''Creates a network object and adds it to the virtual infrastructure'''
        network_object = Network(net_name,attributes,properties)
        key = network_object.type+"_"+network_object.name
        if key in self.resources.keys():
            prompt = "An object of this type and name already exists in your environment, adding it\
again will erase the old object! Are you sure you want to overwrite the old object? (y/n): "
            usr_inpt = raw_input(prompt) 
            response = sT.ResponseLoop(usr_inpt,"[yn]",prompt)
            if response == "y":
                self.resources[key] = network_object
            else:
                pass
        else:
            self.resources[key] = network_object
    #--------------------------------------------------------------------------#
    def AddSubnet(self,subnet_name,attributes,properties):
        '''Creates a subnet object and adds it to the virtual infrastructure'''
        subnet_object = Subnet(subnet_name,attributes,properties)
        key = subnet_object.type+"_"+subnet_object.name
        if key in self.resources.keys():
            prompt = "An object of this type and name already exists in your environment, adding it\
again will erase the old object! Are you sure you want to overwrite the old object? (y/n): "
            usr_inpt = raw_input(prompt) 
            response = sT.ResponseLoop(usr_inpt,"[yn]",prompt)
            if response == "y":
                self.resources[key] = subnet_object
            else:
                pass
        else:
            self.resources[key] = subnet_object 
    #--------------------------------------------------------------------------#
    def AddInstance(self,instance_name,attributes,properties):
        '''Creates an instance object and adds it to the virtual infrastructure'''
        instance_object = Instance(instance_name,attributes,properties)
        key = instance_object.type+"_"+instance_object.name
        if key in self.resources.keys():
            prompt = "An object of this type and name already exists in your environment, adding it\
again will erase the old object! Are you sure you want to overwrite the old object? (y/n): "
            usr_inpt = raw_input(prompt) 
            response = sT.ResponseLoop(usr_inpt,"[yn]",prompt)
            if response == "y":
                self.resources[key] = instance_object
            else:
                pass
        else:
            self.resources[key] = instance_object
    #--------------------------------------------------------------------------#
    def AddVolume(self,volume_name,attributes,properties):
        '''Creates a volume object and adds it to the virtual infrastructure'''
        volume_object = Volume(volume_name,attributes,properties)
        key = volume_object.type+"_"+volume_object.name
        if key in self.resources.keys():
            prompt = "An object of this type and name already exists in your environment, adding it\
again will erase the old object! Are you sure you want to overwrite the old object? (y/n): "
            usr_inpt = raw_input(prompt) 
            response = sT.ResponseLoop(usr_inpt,"[yn]",prompt)
            if response == "y":
                self.resources[key] = volume_object
            else:
                pass
        else:
            self.resources[key] = volume_object
    #--------------------------------------------------------------------------#
    def AddRouter(self,router_name,attributes,properties):
        '''Creates a router object and adds it to the virtual infrastructure'''
        router_object = Router(router_name,attributes,properties)
        key = router_object.type+"_"+router_object.name
        if key in self.resources.keys():
            prompt = "An object of this type and name already exists in your environment, adding it\
again will erase the old object! Are you sure you want to overwrite the old object? (y/n): "
            usr_inpt = raw_input(prompt) 
            response = sT.ResponseLoop(usr_inpt,"[yn]",prompt)
            if response == "y":
                self.resources[key] = router_object
            else:
                pass
        else:
            self.resources[key] = router_object
    #--------------------------------------------------------------------------# 
    def AddImage(self,image_name,attributes,properties):
        '''Creates an image object and adds it to the list of virtual resources'''
        image_object = Image(image_name,attributes,properties)
        key = image_object.type+"_"+image_object.name
        if key in self.resources.keys():
            prompt = "An object of this type and name already exists in your environment, adding it\
again will erase the old object! Are you sure you want to overwrite the old object? (y/n): "
            usr_inpt = raw_input(prompt) 
            response = sT.ResponseLoop(usr_inpt,"[yn]",prompt)
            if response == "y":
                self.resources[key] = image_object
            else:
                pass
        else:
            self.resources[key] = image_object
    #--------------------------------------------------------------------------# 
    def AddFlavor(self,flavor_name,attributes,properties):
        '''Creates an image object and adds it to the list of virtual resources'''
        flavor_object = Flavor(flavor_name,attributes,properties)
        key = flavor_object.type+"_"+flavor_object.name
        if key in self.resources.keys():
            prompt = "An object of this type and name already exists in your environment, adding it\
again will erase the old object! Are you sure you want to overwrite the old object? (y/n): "
            usr_inpt = raw_input(prompt) 
            response = sT.ResponseLoop(usr_inpt,"[yn]",prompt)
            if response == "y":
                self.resources[key] = flavor_object
            else:
                pass
        else:
            self.resources[key] = flavor_object
    #--------------------------------------------------------------------------#
    def AddVolumeAttachment(self,attachment_name,docking_instance_name,attaching_volume_name):
        '''Creates a volume attachment between and existing instance and volume, then adds the 
        attachment to the virtual infrastructure'''
        # Ensure the docking instance and attaching volume exist
        instancekey = "Instance_"+docking_instance_name
        volumekey = "Volume_"+attaching_volume_name
        if instancekey in self.resources.keys():
            pass
        else:
            raise NameError("No instance named %s to attach to!"%docking_instance_name)
        if volumekey in self.resources.keys():
            pass
        else:
            raise NameError("No volume named %s to attach to instance!"%attaching_volume_name)
        # Create attachment object and key, instantiated object creates appropriate dock and attachment
        attachment_object = VolumeAttachment(attachment_name,docking_instance_name,attaching_volume_name)
        attachmentkey = attachment_object.type+"_"+attachment_object.name
        # Add to infrastructure
        if attachmentkey in self.resources.keys():
            prompt = "An object of this type and name already exists in your environment, adding it\
again will erase the old object! Are you sure you want to overwrite the old object? (y/n): "
            usr_inpt = raw_input(prompt) 
            response = sT.ResponseLoop(usr_inpt,"[yn]",prompt)
            if response == "y":
                self.resources[attachmentkey] = attachment_object
            else:
                pass
        else:
            self.resources[attachmentkey] = attachment_object
    #--------------------------------------------------------------------------#
    def AddRouterInterface(self,interface_name,docking_router_object,attaching_subnet_object):
        '''Creates a router interface, attaches a subnet to it, and adds it to the pool of 
        resources'''
        # Ensure the docking router and attaching subnet exist
        routerkey = "Router_"+docking_router_object.name
        subnetkey = "Subnet_"+attaching_subnet_object.name
        if routerkey in self.resources.keys():
            pass
        else:
            raise NameError("No router named %s to attach to!"%docking_router_object.name)
        if subnetkey in self.resources.keys():
            pass
        else:
            raise NameError("No subnet named %s to attach to router!"%attaching_subnet_object.name)
        # Create interface object and key
        interface_object = RouterInterface(interface_name,docking_router_object,attaching_subnet_object)
        interfacekey = interface_object.type+"_"+interface_object.name
        # Add to infrastructure
        if interfacekey in self.resources.keys():
            prompt = "An object of this type and name already exists in your environment, adding it\
again will erase the old object! Are you sure you want to overwrite the old object? (y/n): "
            usr_inpt = raw_input(prompt) 
            response = sT.ResponseLoop(usr_inpt,"[yn]",prompt)
            if response == "y":
                self.resources[interfacekey] = interface_object
            else:
                pass
        else:
            self.resources[interfacekey] = interface_object
    #--------------------------------------------------------------------------#
    def AddNetworkPort(self,port_name,dockingnetwork_name,attachingsubnet_name):
        '''Creates a network port, docks it on a network, attaches a subnet IP, then adds it to the 
        virtual infrastructure'''
        # Ensure the docking network and attaching subnet exist
        netkey = "Network_"+dockingnetwork_name
        subnetkey = "Subnet_"+attachingsubnet_name
        if netkey in self.resources.keys():
            pass
        else:
            raise NameError("No network named %s to attach to!"%dockingnetwork_name)
        if subnetkey in self.resources.keys():
            pass
        else:
            raise NameError("No subnet named %s to attach to!"%attachingsubnet_name)
        # Create port object and key, then add dock and attachment 
        port_object = NetworkPort(port_name,dockingnetwork_name,attachingsubnet_name)
        portkey = port_object.type+"_"+port_object.name
        # Add to infrastructure
        if portkey in self.resources.keys():
            prompt = "An object of this type and name already exists in your environment, adding it\
again will erase the old object! Are you sure you want to overwrite the old object? (y/n): "
            usr_inpt = raw_input(prompt) 
            response = sT.ResponseLoop(usr_inpt,"[yn]",prompt)
            if response == "y":
                self.resources[portkey] = port_object
            else:
                pass
        else:
            self.resources[portkey] = port_object
    #--------------------------------------------------------------------------# 
    def CheckType(self,object_type):
        if not object_type in self.object_types:
            raise TypeError("%s is not a valid Openstack object type, or this type has not yet been implemented"%object_type)
        else:
            pass
    #--------------------------------------------------------------------------#
    def GetObject(self,object_type,object_name):
        self.CheckType(object_type)
        key = object_type+"_"+object_name
        return self.resources[key]
    #--------------------------------------------------------------------------# 
    def GetObjectType(self,object_type):
        self.CheckType(object_type)
        keys = filter(lambda key: object_type in key,self.resources.keys())
        type_dict = {key: self.resources[key] for key in keys}
        return type_dict
    #--------------------------------------------------------------------------#  
    def __repr__(self):
        base = "heat_template_version: %s\n\nresources:\n"%self.template_version
        for key,resource in self.resources.iteritems():
            if resource.type in self.skiplist:
                pass
            else:
                resource_section = resource.__repr__()
                for line in resource_section.splitlines():
                    base += "    "+line+"\n"
        return base
################################################################################
                
#**************************** Parent Classes **********************************#

################################################################################ 
class BaseObject(object):
    '''The class that defines the basic functionality of an Openstack Resource object'''
    #--------------------------------------------------------------------------#
    def __init__(self,resourcename,attributes,properties): ## attributes and properties should be a dictionary
        self.name = resourcename 
        self.attributes = attributes
        self.properties = properties
    #--------------------------------------------------------------------------#
    def __repr__(self):
        base = """%s:
    type: %s\n""" % (self.name,self.identifier)
        if self.properties:
            base += """    properties:"""
            for prop, val in self.properties.iteritems():
                base += "\n        %s: %s"%(prop,val)
        return base
    #--------------------------------------------------------------------------#
    def AddProperty(self,key,value):
        if key in self.properties.keys():
            prompt = "This property already exists for the object and adding it will overwrite the\
current value! Are you sure you want to overwrite this property? (y/n): "
            usr_inpt = raw_input(prompt) 
            response = sT.ResponseLoop(usr_inpt,"[yn]",prompt)
            if response == "y":
                self.properties[key] = value
            else:
                pass
        else:
            self.properties[key] = value
    #--------------------------------------------------------------------------#
    def AddAttribute(self,key,value):
        if key in self.attributes.keys():
            prompt = "This property already exists for the object and adding it will overwrite the\
current value! Are you sure you want to overwrite this property? (y/n): "
            usr_inpt = raw_input(prompt) 
            response = sT.ResponseLoop(usr_inpt,"[yn]",prompt)
            if response == "y":
                self.attributes[key] = value
            else:
                pass
        else:
            self.attributes[key] = value
################################################################################
class BaseAttachmentObject(object):
    '''The class that defines the basic functionality of an Openstack Resource Attachment object. 
    Note that for attachment objects you need to pass in an actual instance of the objects being 
    attached. This prevents the user from attempting to attach objects that do not actually exist'''
    #--------------------------------------------------------------------------#
    def __init__(self,attachmentname,docking_object,attaching_object):
        self.name = attachmentname
        self.docking_object_name = docking_object.name
        self.attaching_object_name = attaching_object.name
    #--------------------------------------------------------------------------#
    def __repr__(self):
        base = """%s:
    type: %s\n""" % (self.name,self.identifier)
        if self.properties:
            base += """    properties:"""
            for prop, val in self.properties.iteritems():
                
                base += "\n        %s: %s"%(prop,val)
        return base
    #--------------------------------------------------------------------------#
    def AddProperty(self,key,value):
        if key in self.properties.keys():
            prompt = "This property already exists for the object and adding it will overwrite the\
current value! Are you sure you want to overwrite this property? (y/n): "
            usr_inpt = raw_input(prompt) 
            response = sT.ResponseLoop(usr_inpt,"[yn]",prompt)
            if response == "y":
                self.properties[key] = value
            else:
                pass
        else:
            self.properties[key] = value
    #--------------------------------------------------------------------------#
    def AddAttribute(self,key,value):
        if key in self.attributes.keys():
            prompt = "This property already exists for the object and adding it will overwrite the\
current value! Are you sure you want to overwrite this property? (y/n): "
            usr_inpt = raw_input(prompt) 
            response = sT.ResponseLoop(usr_inpt,"[yn]",prompt)
            if response == "y":
                self.attributes[key] = value
            else:
                pass
        else:
            self.attributes[key] = value  
################################################################################     

#***************************** Child Classes **********************************# 

################################################################################
class Network(BaseObject):
    '''This class defines the functionality for an OS Network object. Inherits from
BaseObject and has a Subnet. The creation and managemement of subnets are all handled
through this class because a subnet cannot exist and has no use without a network.'''
    def __init__(self,networkname,attributes,properties):
        self.identifier = "OS::Neutron::Net"
        self.type = "Network"
        super(Network,self).__init__(networkname,attributes,properties)
    def UpdateSubnets(self,subnetname):
        '''Updates list of subnets in master network attributes'''
        if "subnets" in self.attributes.keys():
            subnets = self.attributes["subnets"]
            subnets = subnets.append(subnetname)
            self.attributes["subnets"] = subnets
        else:
            self.attributes["subnets"] = [subnetname]
################################################################################ 
class Subnet(BaseObject):
    '''Defines the functionality for an OS Subnet Object. Handled via the Network 
    class'''
    def __init__(self,subnetname,attributes,properties):
        self.identifier = "OS::Neutron::Subnet"
        self.type = "Subnet"
        super(Subnet,self).__init__(subnetname,attributes,properties)
    def AttachToNetwork(self,net_name,CIDR):
        self.properties["network_id"] = "{ get_resource: %s }"%net_name 
        self.properties["cidr"] = CIDR 
################################################################################  
class Instance(BaseObject):
    '''The class that defines functionality of an OS Instance object. Inherits 
from BaseObject and has a Network Port and VolumeAttachment'''
    def __init__(self,resourcename,attributes,properties):
        self.identifier = "OS::Nova::Server"
        self.type = "Instance"
        super(Instance,self).__init__(resourcename,attributes,properties)
    def __repr__(self):
        base = """%s
    type: %s\n""" % (self.name,self.identifier)
        if self.properties:
            base += """    properties:"""
            for prop, val in self.properties.iteritems():
                if type(val) == list:
                    base += "\n        %s:"%prop
                    for tup in val:
                        subprop = tup[0]
                        subval = tup[1]
                        base += "\n            - %s: %s"%(subprop,subval)
                elif type(val) == dict:
                    base += "\n        %s:"%prop
                    for subprop,subval in val.iteritems():
                        base += "\n            - %s: %s"%(subprop,subval)
                else:    
                    base += "\n        %s: %s"%(prop,val)
        return base  
    # Add network port and volume attachment functionality here 
    def AttachToNetworkPort(self,port_object):
        '''Attach instance to network port. Note you must pass in the actual port
        object to prevent users from referring to a port that has not yet been created'''
        port_list = self.properties["networks"] 
        port_list.append(("port","{ get_resource: %s }"%port_object.name))
        self.properties["networks"] = port_list
    def AttachVolume():
        pass    
################################################################################  
class NetworkPort(BaseAttachmentObject):
    def __init__(self,portname,docking_network,attaching_subnet):
        self.identifier = "OS::Neutron::Port"
        self.type = "NetworkPort"
        super(NetworkPort,self).__init__(portname,docking_network,attaching_subnet)
        self.properties = {"network":docking_network,"fixed_ips":[("subnet_id",attaching_subnet)]}
################################################################################       
class Volume(BaseObject):
    '''The class that defines the functionality of an OS Volume object. Inherits from BaseObject and has a VolumeAttachment'''
    def __init__(self,resourcename,attributes,properties):
        self.identifier = "OS::Cinder::Volume"
        self.type = "Volume"
        super(Volume,self).__init__(resourcename,attributes,properties)
    def UpdateInstanceList():
        pass
        ### Add new instances to attributes dict here
    def UpdateAttachments():
        pass
################################################################################
class VolumeAttachment(BaseAttachmentObject):
    '''The class that defines the functionality for attaching an Instance and a Volume. Inherits from BaseAttachmentObject'''
    def __init__(self,attachmentname,docking_instance,attaching_volume):
        self.identifier = "OS::Cinder:VolumeAttachment"
        self.type = "VolumeAttachment"
        super(VolumeAttachment,self).__init__(attachmentname,docking_instance,attaching_volume)
        self.properties = {"instance_uuid":"{ get_resource: %s }"%self.docking_object_name, "volume_id":"{ get_resource: %s }"%self.attaching_object_name}
        #self.properties = {"instance_uuid":"{ get_resource: %s }"%self.docking_object_name, "volume_id":"{ get_resource: %s }"%self.attaching_object_name, "mountpoint":"{ str_replace: template: /dev/disk/by-id/virtio-ID params: ID: { get_resource: %s} }"%self.attaching_object_name}
        # The above properties intitialization needs to be properly tested, and is not even completely necessary
################################################################################   
class Router(BaseObject):
    '''The class that defines the functionality of an OS Router object. Inherits from BaseObject'''
    def __init__(self,routername,attributes,properties):
        self.identifier = "OS::Neutron::Router"
        self.type = "Router"
        super(Router,self).__init__(routername,attributes,properties)
################################################################################     
class RouterInterface(BaseAttachmentObject):
    '''The class that defines the functionality for connecting a subnet to a router. Inherits from BaseAttachmentObject'''
    def __init__(self,interfacename,docking_router,attaching_subnet):
        self.identifier = "OS::Neutron::RouterInterface"
        self.type = "RouterInterface"
        super(RouterInterface,self).__init__(interfacename,docking_router,attaching_subnet)
        self.properties = {"router_id":"{ get_resource: %s}"%docking_router.name,"subnet":"{ get_resource: %s }"%attaching_subnet.name}
################################################################################  
class Image(BaseObject):
    '''The class that defines the functionality for an Openstack Image object. Inherits from Base Object'''
    def __init__(self,imagename,attributes,properties):
        self.identifier = "OS::Glance::Image"
        self.type = "Image"
        super(Image,self).__init__(imagename,attributes,properties)  
    #!!!!!!!!!! This class is unique and needs additional functionality. There
    #!!!!!!!!!! are many different types of images, and work needs to be done on
    #!!!!!!!!!! them to make them bootable. Lots of post configuration also needs
    #!!!!!!!!!! to be done. For not we just need the list of available images in the
    #!!!!!!!!!! environment, and they will not be added as a resource in the YAML'
    #!!!!!!!!!! template file 
################################################################################                                                  
class Flavor(BaseObject):
    def __init__(self,flavorname,attributes,properties):
        self.identifier = "OS::Nova::Flavor"
        self.name = flavorname
        self.type = "Flavor"
        super(Flavor,self).__init__(flavorname,attributes,properties)
################################################################################        
