'''
Created on Feb 13, 2014

@author: sandy
'''
import api
import ConfigParser
from xapian import InvalidArgumentError

class LinodeCreater(object):
    config = ConfigParser.ConfigParser()
    config.read('/data/linode/linode.properties')
    linode = api.Api(config.get('DEFAULT','LINODE_API'))
    
    def __init__(self, linodeIdentifier):
        '''
        Constructor
        '''
        self.linodeIdentifier=linodeIdentifier
        self.distributionId=[d['DISTRIBUTIONID'] for d in self.linode.avail_distributions() if (self.config.get('DEFAULT','UBUNTU_DIST') in d['LABEL']) and (d['IS64BIT'])][0]
        print("Distribution id: %s"%(self.config.get('DEFAULT','UBUNTU_DIST')))
        self.kernelId=[_['KERNELID'] for _ in self.linode.avail_kernels() if (self.config.get('DEFAULT','KERNEL_LABEL') in _['LABEL']) ][0]
        self.dallasDataCenterId=[dc['DATACENTERID'] for dc in self.linode.avail_datacenters() if self.config.get('DEFAULT','DATACENTER_LABEL') in dc['LOCATION']][0]
        self.planId=[p['PLANID'] for p in self.linode.avail_linodeplans() if self.config.get('DEFAULT','PLAN_ID') in p['LABEL']][0]
        self.paymentTerm=1

    def _createLinode(self):
        try:
            self.saLinode=Linode(self.linodeIdentifier)
            print "Linode exists continuing forward"
        except InvalidArgumentError:
            print "Linode doesn't exists creating it" 
#            self.linodeNode=self.linode.linode_create(DatacenterID=self.dallasDataCenterId, PlanID=self.planId, PaymentTerm=self.paymentTerm)
#            self.linodeId=linodeNode['LinodeID']
#            self.linode.linode_update(LinodeID=self.linodeId, Label=self.linodeIdentifier,lpm_displayGroup=self.config.get('DEFAULT','LINODE_GROUP'))
            
            
        print self.saLinode.getId()
    
    def _createRootDiskIfNotExist(self):
        if not self.saLinode.getRootDisk():
            print "Root disk doesn't exists creating 20 GB of it"
            self.linode.linode_disk_createfromdistribution(LinodeID=self.saLinode.getId(), DistributionID=self.distributionId, Label='Root Partition', Size=(self.config.getint('DEFAULT', 'ROOT_DISK_SIZE')), rootPass=self.config.get('DEFAULT','ROOT_PWD'),rootSSHKey=open(self.config.get('DEFAULT','ROOT_SSH_KEY')).read())
            self.saLinode.refreshLinode()
        print self.saLinode.getRootDisk()['DISKID']
    
    def _createSwapDiskIfNotExist(self):
        if not self.saLinode.getSwapDisk():
            print "Swap disk doesn't exists creating 2 GB of it"
            self.linode.linode_disk_create(LinodeID=self.saLinode.getId(), Label='Swap Partition', Type='swap', Size=self.config.getint('DEFAULT', 'SWAP_DISK_SIZE'))
            self.saLinode.refreshLinode()
        print self.saLinode.getSwapDisk()['DISKID']
        
    def _createConfigIfNotExist(self):
        if not self.saLinode.getDefaultConfig():
            print "Configuration doesn't exists creating it"
            diskIdsList="{0},{1}".format(self.saLinode.getRootDisk()['DISKID'],self.saLinode.getSwapDisk()['DISKID'])
            self.linode.linode_config_create(LinodeID=self.saLinode.getId(), KernelID=self.kernelId, Label='Monimus Default Config', DiskList=diskIdsList)
            self.saLinode.refreshLinode()
        print self.saLinode.getDefaultConfig()['ConfigID']

    def _addPrivateIp(self):
        if not self.saLinode.getPrivateIp():
            print "This machine doesn't have a private IP address adding a private IP"
            self.pvtIpAddress=self.linode.linode_ip_addprivate(LinodeID=self.saLinode.getId())
            self.saLinode.refreshLinode()
        print self.saLinode.getPrivateIp()
            
    def _bootLinode(self):
        linodeNode=self.linode.linode_list(LinodeID=self.linodeId)[0]
        if not linodeNode['STATUS'] == 1:
            print ("Linode is not running, so booting it up!")
            self.linode.linode_boot(LinodeID=self.linodeId,ConfigID=self.configId)
        else:
            print ("Linode is already running")

    def create(self):
        self._createLinode()
        self._createRootDiskIfNotExist()
        self._createSwapDiskIfNotExist()
        self._createConfigIfNotExist()
        self._addPrivateIp()
        self._bootLinode()

class Linode(object):
    '''
    classdocs
    '''
    config = ConfigParser.ConfigParser()
    config.read('/data/linode/linode.properties')
    linode = api.Api(config.get('DEFAULT','LINODE_API'))

    def __init__(self, linodeIdentifier):
        '''
        Constructor
        '''
        self.linodeIdentifier=linodeIdentifier
        self._getLinode()


    def _getLinode(self):
        linodeNodes=[l for l in self.linode.linode_list() if (self.linodeIdentifier in l['LABEL'])]
        if not linodeNodes:
            print ("Linode doesn't exists for identifier %s"%(self.linodeIdentifier))
            raise InvalidArgumentError("Linode doesn't exists for identifier %s"%(self.linodeIdentifier))
        self.linodeNode=linodeNodes[0]
    
    def getId(self):
        return self.linodeNode['LINODEID']
    
    def getPublicIp(self):
        return [i['IPADDRESS'] for i in  self.linode.linode_ip_list(LinodeID=self.getId()) if (i['ISPUBLIC'])][0]
    
    def getPrivateIp(self):
        privateIp=None
        privateIpList=[i['IPADDRESS'] for i in  self.linode.linode_ip_list(LinodeID=self.getId()) if (not i['ISPUBLIC'])]
        if privateIpList:
            privateIp=privateIpList[0]
        return privateIp

    def getRootDisk(self):
        rootDisk=None
        rootDiskList=[d for d in  self.linode.linode_disk_list(LinodeID=self.getId()) if ('Root Partition' in d['LABEL'])]
        if rootDiskList:
            rootDisk=rootDiskList[0]
        return rootDisk
    
    def getDefaultConfig(self):
        defaultConfig=None
        defaultConfigsList=[c for c in  self.linode.linode_config_list(LinodeID=self.getId()) if ('Monimus Default Config' in c['Label'])]
        if defaultConfigsList:
            defaultConfig=defaultConfigsList[0]        
        return defaultConfig
    
    def getSwapDisk(self):
        swapDisk=None
        swapDiskList=[d for d in  self.linode.linode_disk_list(LinodeID=self.getId()) if ('Swap Partition' in d['LABEL'])]
        if swapDiskList:
            swapDisk=swapDiskList[0]
        return swapDisk
    
    def isRunning(self):
        running = (self.linodeNode['STATUS'] == 1)
        self.linode
        return running
    
    def refreshLinode(self):
        self._getLinode()
        
if __name__ == "__main__":
    #saLinode=Linode('bs2_monimus_org')
    #saLinode.create()
    saLinode=LinodeCreater('bs2_monimus_com')
    saLinode._createLinode()