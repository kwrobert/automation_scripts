#****** THE CLASS STRUCTURE BELOW IS VERY REPETITIVE. CAN ACHIEVE THE SAME PURPOSE
#****** SERVED BY THE MANY CLASSES BELOW SIMPLY BY PASSING A TYPE ARGUMENT INTO 
#****** THE BASE CLASS
#****** THIS MIGHT BE A GOOD PLACE TO APPLY THE PRINCIPLES OF POLYMORPHIC 
#****** CODE DESIGN, WHERE EACH CHILD CLASS/OBJECT INHERITS FROM THE PARENT/BASE
#****** CLASS/OBJECT AND ONLY OVERWRITES THE FUNCTIONALITY OF THE BASE CLASS
#****** WHEN NECESSARY 
################################################################################ 
class OpenStack_Virtual_Infrastructure(object):
    def __init__(self,template_version):
        self.networks = {}
        self.instances = {}
        self.volumes = {}
        self.images = {}
        self.flavors  = {}
        self.template_version = template_version
        self.resources = []
    def AddNetwork(self,network_object):
        key = network_object.type+"_"+network_object.name
        self.networks[key] = network_object
        self.resources.append(network_object)
    def AddInstance(self,instance_object):
        key = instance_object.type+"_"+instance_object.name
        self.instances[key] = instance_object
        self.resources.append(instance_object)
    def AddVolume(self,volume_object):
        key = volume_object.type+"_"+volume_object.name
        self.volumes[key] = volume_object
        self.resources.append(volume_object)
    def AddImage(self,image_object):
        key = image_object.type+"_"+image_object.name
        self.images[key] = image_object
        #self.resources.append(image_object)
    def AddFlavor(self,flavor_object):
        key = flavor_object.type+"_"+flavor_object.name
        self.images[key] = flavor_object
        self.resources.append(flavor_object)
    def __repr__(self):
        base = "heat_template_version: %s\n\nresources:\n"%self.template_version
        for resource in self.resources:
            resource_section = resource.__repr__()
            print resource_section
            for line in resource_section.splitlines():
                base += "    "+line+"\n"
        return base
################################################################################ 
class BaseObject(object):
    '''The class that defines the basic functionality of an Openstack Resource object'''
    def __init__(self,resourcename,attributes,properties): ## attributes and properties should be a dictionary
        self.name = resourcename 
        self.attributes = attributes
        self.properties = properties
    def __repr__(self):
        base = """%s:
    type: %s
    properties:""" % (self.name,self.identifier)
        for prop, val in self.properties.iteritems():
            base += "\n        %s: %s"%(prop,val)
        return base
    def AddProperty(self, key, value):
        self.properties[key] = value
################################################################################
class BaseAttachmentObject(object):
    '''The class that defines the basic functionality of an Openstack Resource Attachment object'''
    def __init__(self,docking_object,attaching_object,attributes,properties):
        self.docking_object = docking_object.name
        self.attaching_object = attaching_object.name
        self.properties = properties
    def AddProperty(self, key, value):
        self.properties[key] = value            
################################################################################        
class Instance(BaseObject):
    '''The class that defines functionality of an OS Instance object. Inherits 
from BasicObject and has a Network Port and VolumeAttachment'''
    def __init__(self,resourcename,attributes,properties):
        self.identifier = "OS::Nova::Server"
        self.type = "Instance"
        super(Instance,self).__init__(resourcename,attributes,properties)
        # Add network port and volume attachment functionality here
    def __repr__(self):
        base = """%s
    type: %s
    properties:""" % (self.name,self.identifier)
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
################################################################################        
class Volume:
    '''The class that defines the functionality of an OS Volume object. Inherits from BasicObject and has a VolumeAttachment'''
    def __init__(self,resourcename,attributes,properties):
        self.identifier = "OS::Cinder::Volume"
        self.type = "Volume"
        super(Volume,self).__init__(resourcename,attributes,properties)
        ### Add Volume Creation and Attachment functionality in here
    def __repr__(self):
        base = """%s
    type: %s
    properties:""" % (self.name,self.identifier)
        for prop, val in self.properties.iteritems():
            base += "\n        %s: %s"%(prop,val)
        return base
################################################################################
class Network:
    def __init__(self,resourcename, **properties):
        self.identifier = "OS::Neutron::Net"
        ### Add subnet creation and functionality in here
        self.name = resourcename
        self.properties = properties
    def __repr__(self):
        base = """%s
    type: %s
    properties:""" % (self.name,self.identifier)
        for prop, val in self.properties.iteritems():
            base += "\n        %s: %s"%(prop,val)
        return base
################################################################################                
class SecurityGroup:
    def __init__(self,resourcename, **properties):
        self.identifier = "OS::Neutron::SecurityGroup"
        self.name = resourcename
        self.properties = properties
    def __repr__(self):
        base = """%s
    type: %s
    properties:""" % (self.name,self.identifier)
        for prop, val in self.properties.iteritems():
            base += "\n        %s: %s"%(prop,val)
        return base
################################################################################       
class InstanceFlavor:
    def __init__(self,resourcename, **properties):
        self.identifier = "OS::Nova::Flavor"
        self.name = resourcename
        self.properties = properties
    def __repr__(self):
        base = """%s
    type: %s
    properties:""" % (self.name,self.identifier)
        for prop, val in self.properties.iteritems():
            base += "\n        %s: %s"%(prop,val)
        return base 
################################################################################        
class User:
    def __init__(self,resourcename, **properties):
        self.identifier = "OS::Keystone::User"
        self.name = resourcename
        self.properties = properties
    def __repr__(self):
        base = """%s
    type: %s
    properties:""" % (self.name,self.identifier)
        for prop, val in self.properties.iteritems():
            base += "\n        %s: %s"%(prop,val)
        return base
################################################################################ 