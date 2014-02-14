'''
Created on Feb 13, 2014

@author: sandy
'''
import api
import ConfigParser

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
        self.distributionId=[d['DISTRIBUTIONID'] for d in self.linode.avail_distributions() if (self.config.get('DEFAULT','UBUNTU_DIST') in d['LABEL']) and (d['IS64BIT'])]
        print("Distribution id: %s"%(self.config.get('DEFAULT','UBUNTU_DIST')))
        self.kernelId=[_['KERNELID'] for _ in self.linode.avail_kernels() if (self.config.get('DEFAULT','KERNEL_LABEL') in _['LABEL']) ]
        self.dallasDataCenterId=[dc['DATACENTERID'] for dc in self.linode.avail_datacenters() if self.config.get('DEFAULT','DATACENTER_LABEL') in dc['LOCATION']]
        self.planId=[p['PLANID'] for p in self.linode.avail_linodeplans() if self.config.get('DEFAULT','PLAN_ID') in p['LABEL']]
        self.paymentTerm=1

    def _createLinode(self):
        self.linodeId=[l['LINODEID'] for l in  self.linode.linode_list() if (self.linodeIdentifier in l['LABEL'])]
        if not self.linodeId:
            print "Lindoe doesn't exists. Creating it"
            self.linodeNode=self.linode.linode_create(DatacenterID=self.dallasDataCenterId, PlanID=self.planId, PaymentTerm=self.paymentTerm)
            
            
        print self.linodeId
    
    def _createRootDiskIfNotExist(self):
        self.rootDiskId=[d['DISKID'] for d in  self.linode.linode_disk_list(LinodeID=self.linodeId) if ('Root Partition' in d['LABEL'])]
        if not self.rootDiskId:
            print "Root disk doesn't exists creating 20 GB of it"
            self.disk=self.linode.linode_disk_createfromdistribution(LinodeID=self.linodeId, DistributionID=self.distributionId, Label='Root Partition', Size=(self.config.getint('DEFAULT', 'ROOT_DISK_SIZE')), rootPass=self.config.get('DEFAULT','ROOT_PWD'),rootSSHKey=open(self.config.get('DEFAULT','ROOT_SSH_KEY')).read())
            self.rootDiskId=self.disk['DiskID']
        print self.rootDiskId
    
    def _createSwapDiskIfNotExist(self):
        self.swapDiskId=[d['DISKID'] for d in  self.linode.linode_disk_list(LinodeID=self.linodeId) if ('Swap Partition' in d['LABEL'])]
        if not self.swapDiskId:
            print "Swap disk doesn't exists creating 2 GB of it"
            self.disk=self.linode.linode_disk_create(LinodeID=self.linodeId, Label='Swap Partition', Type='swap', Size=self.config.getint('DEFAULT', 'SWAP_DISK_SIZE'))
            self.swapDiskId=self.disk['DiskID']
        print self.swapDiskId
        
    def _createConfigIfNotExist(self):
        self.configId=[c['ConfigID'] for c in  self.linode.linode_config_list(LinodeID=self.linodeId) if ('Monimus Default Config' in c['Label'])]
        if not self.configId:
            print "Configuration doesn't exists creating it"
            self.config=self.linode.linode_config_create(LinodeID=self.linodeId, KernelID=self.kernelId, Label='Monimus Default Config', DiskList=[self.rootDiskId,self.swapDiskId])
            self.configId=self.config['ConfigID']
        print self.configId
    
    def _addPrivateIp(self):
        self.pvtIpAddress=[i['IPADDRESS'] for i in  self.linode.linode_ip_list(LinodeID=self.linodeId) if (not i['ISPUBLIC'])]
        if not self.pvtIpAddress:
            print "This machine doesn't have a private IP address adding a private IP"
            self.pvtIpAddress=self.linode.linode_ip_addprivate(LinodeID=self.linodeId)
        print self.pvtIpAddress
            
    def _bootLinode(self):
        self.linode.linode_boot(self.linodeId)

    def create(self):
        self._createLinode()
        self._createRootDiskIfNotExist()
        self._createSwapDiskIfNotExist()
        self._createConfigIfNotExist()
        self._addPrivateIp()
        #self._bootLinode()
    
if __name__ == "__main__":
    saLinode=Linode('bs1_monimus_org')
    saLinode.create()