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

pc.defineParameter(
    "nodeType1","Hardware Type 1",
    portal.ParameterType.NODETYPE,"",
    longDescription="A specific hardware type to use for each type 1 node.")

pc.defineParameter("numNode1", "Number of type 1 Nodes", portal.ParameterType.INTEGER, 0,
                   longDescription="set of nodes of the same type 1.")

pc.defineParameter(
    "nodeType2","Hardware Type 2",
    portal.ParameterType.NODETYPE,"",
    longDescription="A specific hardware type to use for each type 2 node.")

pc.defineParameter("numNode2", "Number of type 2 Nodes", portal.ParameterType.INTEGER, 0,
                   longDescription="set of nodes of the same type 2.")

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

# Parameter comprobation
if params.numNode1 > 0 and len(params.nodeType1) == 0:
    err = portal.ParameterError(
        "If you want to request nodes of type 1, you have to specify the hardware type of this set of nodes",
        ["numNode1", "nodeType1"])
    pc.reportError(err)

elif params.numNode2 > 0 and len(params.nodeType2) == 0:
    err = portal.ParameterError(
        "If you want to request nodes of type 2, you have to specify the hardware type of this set of nodes",
        ["numNode2", "nodeType2"])
    pc.reportError(err)

typeMaster = "c220g5"
numMaster = 1
TotalN = params.numNode1 + params.numNode2 + numMaster
CMD = "source /local/repository/setup_config/setup.sh -n {}".format(TotalN - 1)

# Script begins here

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
    node.disk_image = "urn:publicid:IDN+emulab.net+image+emulab-ops//UBUNTU24-64-STD"

    # Add to lan
    iface = node.addInterface("eth1")
    iface.addAddress(pg.IPv4Address("192.168.1.{}".format(i + 1), "255.255.255.0"))
    lan.addInterface(iface)

    # Hardware type.
    if numMaster - i > 0:
        node.hardware_type = typeMaster
        pass
    elif (params.numNode1 + numMaster) - i > 0:
        node.hardware_type = params.nodeType1
        pass
    else:
        node.hardware_type = params.nodeType2
        pass

    # Ejecucion de comando setup.sh
    node.addService(pg.Execute(shell="bash", command=CMD))

# Print the RSpec to the enclosing page.
pc.printRequestRSpec(request)