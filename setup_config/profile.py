"""Variable number of nodes in a lan. You have the option of picking from one
of several standard images we provide, or just use the default (typically a recent
version of Ubuntu). You may also optionally pick the specific hardware type for
all the nodes in the lan. 

Instructions:
Wait for the experiment to start, and then log into one or more of the nodes
by clicking on them in the toplogy, and choosing the `shell` menu option.
Use `sudo` to run root commands. 
"""

# Import the Portal object.
import geni.portal as portal
# Import the ProtoGENI library.
import geni.rspec.pg as pg
# Emulab specific extensions.
import geni.rspec.emulab as emulab

# Create a portal context, needed to defined parameters
pc = portal.Context()

# Create a Request object to start building the RSpec.
request = pc.makeRequestRSpec()

#Variable number of nodes.
pc.defineParameter("A30Nodes", "Number of Nodes A30", portal.ParameterType.INTEGER, 1,
                   longDescription="If you specify more then one node, " +
                   "we will create a lan for you.")

pc.defineParameter("P100Nodes", "Number of Nodes P100", portal.ParameterType.INTEGER, 0,
                   longDescription="If you specify more then one node, " +
                   "we will create a lan for you.")

# Pick your OS.
#  imageList = [
#      ('default', 'Default Image'),
#      ('urn:publicid:IDN+emulab.net+image+emulab-ops//UBUNTU24-64-STD', 'Ubuntu 24.04'),
#      ('urn:publicid:IDN+emulab.net+image+emulab-ops//UBUNTU22-64-STD', 'Ubuntu 22.04')]

# pc.defineParameter("osImage", "Select OS image",
#                    portal.ParameterType.IMAGE,
#                    imageList[0], imageList,
#                    longDescription="Most clusters have this set of images, " +
#                    "pick your favorite one.")

# Optional link speed, normally the resource mapper will choose for you based on node availability
pc.defineParameter("linkSpeed", "Link Speed",portal.ParameterType.INTEGER, 1000000,
                   [(0,"Any"),(100000,"100Mb/s"),(1000000,"1Gb/s"),(10000000,"10Gb/s"),(25000000,"25Gb/s"),(100000000,"100Gb/s")],
                   advanced=True,
                   longDescription="A specific link speed to use for your lan. Normally the resource " +
                   "mapper will choose for you based on node availability and the optional physical type.")
                   
# For very large lans you might to tell the resource mapper to override the bandwidth constraints
# and treat it a "best-effort"
pc.defineParameter("bestEffort",  "Best Effort", portal.ParameterType.BOOLEAN, False,
                    advanced=True,
                    longDescription="For very large lans, you might get an error saying 'not enough bandwidth.' " +
                    "This options tells the resource mapper to ignore bandwidth and assume you know what you " +
                    "are doing, just give me the lan I ask for (if enough nodes are available).")
                    
# Sometimes you want all of nodes on the same switch, Note that this option can make it impossible
# for your experiment to map.
pc.defineParameter("sameSwitch",  "No Interswitch Links", portal.ParameterType.BOOLEAN, False,
                    advanced=True,
                    longDescription="Sometimes you want all the nodes connected to the same switch. " +
                    "This option will ask the resource mapper to do that, although it might make " +
                    "it imppossible to find a solution. Do not use this unless you are sure you need it!")                

# Retrieve the values the user specifies during instantiation.
params = pc.bindParameters()

OSimage = {
    "CPU" : "urn:publicid:IDN+wisc.cloudlab.us+image+gpu4k8s-PG0//Image_config.node1",
    "A30" : "urn:publicid:IDN+wisc.cloudlab.us+image+gpu4k8s-PG0//Image_config.node2",
    "P100" : "urn:publicid:IDN+wisc.cloudlab.us+image+gpu4k8s-PG0//Image_config.node3"
}

nodetype = {
    "CPU" : "c220g5",
    "A30" : "d7525",
    "P100" : "c240g5"
}

Master = 1
TotalN = params.A30Nodes + params.P100Nodes + Master 

# Create link/lan.
if TotalN == 2:
    lan = request.Link()
else:
    lan = request.LAN()
    pass
if params.bestEffort:
    lan.best_effort = True
elif params.linkSpeed > 0:
    lan.bandwidth = params.linkSpeed
if params.sameSwitch:
    lan.setNoInterSwitchLinks()
pass

# Process nodes, adding to link or lan.
for i in range(TotalN):

    # Create a node and add it to the request
    name = "node{}".format(i + 1)
    node = request.RawPC(name)

    #OS Image
    # if params.osImage and params.osImage != "default":
    #     node.disk_image = params.osImage
    #     pass

    # Add to lan
    iface = node.addInterface("eth1")
    iface.addAddress(pg.IPv4Address("192.168.1.{}".format(i + 1), "255.255.255.0"))
    lan.addInterface(iface)

    # Hardware type.
    if Master - i > 0:
        node.hardware_type = nodetype["CPU"]
        node.disk_image = OSimage["CPU"]
        pass
    elif (params.A30Nodes + Master) - i > 0:
        node.hardware_type = nodetype["A30"]
        node.disk_image = OSimage["A30"]
        pass
    else:
        node.hardware_type = nodetype["P100"]
        node.disk_image = OSimage["P100"]
        pass

# Print the RSpec to the enclosing page.
pc.printRequestRSpec(request)