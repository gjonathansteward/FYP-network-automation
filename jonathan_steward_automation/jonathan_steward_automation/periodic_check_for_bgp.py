from common_tasks import get_data, set_data_mysql, print_error, check_ip, device_config_info_lookup, grab_interface_ip
from Classes import ToolLog
from sshconnection import ssh_connection
from JuniperConfig import Juniper_config
from SNMPPoll import SnmpPoll
import time


def check_for_peers():
    """
    Author - Jonathan Steward
    Function - Gets data from the database about the different peers 
               checks the state of the peers and calls the relevant functions
    Inputs - n/a 
    returns - 
        int - configures - Number of peers configured used for logging
        int - checks - Number of peers checked used for logging
        int - fails - Number of peer actions that failed used for logging 
    """
    command = "SELECT * FROM `FYP Data`.BGP_peers"
    data = get_data(command)
    # data = peerId/device_id/remote_asn/loopback_source/remote_ip/source_interface/approved/approver/configured
    non_approved = []
    configures = []
    checks = []
    fails = []
    for peer in data:
        if peer[6] == 0:  # Need to approve
            print_error("peer id {} for device {} and remote ip {} needs to be approved".format(
                peer[0], peer[1], peer[4]))
            non_approved.append(peer[0])
        elif peer[8] == 0:  # Need to configure
            set_peer_status(peer[0], 1)
            configures.append(peer[0])
            state, peer_object, device = configure_peer_workflow(peer)
            if state:
                set_peer_status(peer[0], 2)
                state = check_peer_status(
                    peer_object["device_ip"],
                    peer_object["remote_ip"],
                    device)
                if state:
                    print_error("Peer is established")
                    set_peer_status(peer[0], 3)
            else:
                fails.append(peer[0])

        elif peer[8] == 1:  # Started to configured but didn't work
            print_error("Peer id {} was attempted to be configured previously but there was a problem".format(peer[0]))
            # EMAIL NETWORK ENGINEER OR SOMETHING SIMILAR

        elif peer[8] == 2:  # Configured but wasn't in established state
            checks.append(peer[0])
            print_error("Checking peer: {}".format(peer))
            state = check_peer_workflow(peer)
            if state:
                print_error("Peer is established")
                set_peer_status(peer[0], 3)
            else:
                print_error("Peer still not established")
                fails.append(peer[0])

        else:  # Peer fully configured
            pass
    # Setting peer status to in progress
    return configures, checks, fails, non_approved


def set_peer_status(peer_id, status):
    """
    Author - Jonathan Steward
    Function - send MYSQL command to set the configured state of peer
    Inputs - 
        int - peer_id - peer_id of the peer acting on
        int - status - the state of the peer
    returns - n/a
    """
    command = """
    UPDATE `FYP Data`.BGP_peers
    SET configured = {}
    WHERE peer_id = {}
    """.format(status, peer_id)
    set_data_mysql(command)


def configure_peer_workflow(data):
    """
    Author - Jonathan Steward
    Function - Workflow function to call configuration functions
    Inputs - list - data - list of details about peer
    returns - 
        bool - state - state of configuration
        dict - peer - stores all peer relevant information
        object - device - stores all device relevant information
    """
    peer = gather_peer_data(data)
    if not peer:
        return False, "", ""
    state, device = device_config_info_lookup(peer["device_ip"])
    if not state:
        return False
    print "have peer and device config info"
    if peer["vendor"] == "cisco":
        state = configure_peer_cisco(peer, device)
    elif peer["vendor"] == "juniper":
        state = configure_peer_juniper(peer, device)
    return state, peer, device


def check_peer_workflow(data):
    """
    Author - Jonathan Steward
    Function - Workflow function to check a peer with existing config
    Inputs - list - data - list of details about peer 
    returns - bool - state - state of peer
    """
    peer = gather_peer_data(data)
    if not peer:
        return False
    state, device = device_config_info_lookup(peer["device_ip"])
    if not state:
        return False
    state = check_peer_status(peer["device_ip"], peer["remote_ip"], device)
    return state


def gather_peer_data(data):
    """
    Author - Jonathan Steward
    Function - converts the list of data into a peer dictionary for easier referencing
    Inputs - list - data - list of details about peer 
    returns - dict - peer - peer details 
    """
    peer = {}
    peer["device_id"] = data[1]
    peer["remote_asn"] = data[2]
    if data[3] == 1:
        peer["loopback_source"] = True
        peer["source_interface"] = data[5]
    else:
        peer["loopback_source"] = False
    peer["remote_ip"] = data[4]
    peer["source_interface"] = data[5]
    state = check_ip(peer["remote_ip"])
    if not state:
        return False
    peer["device_ip"], peer["vendor"], peer["local_asn"] = find_device_ip(peer["device_id"])
    if peer["device_ip"] == "":
        return False

    print "need to configure/check {} to remote_ip {} asn {} a {} device".format(
        peer["device_ip"], peer["remote_ip"], peer["remote_asn"], peer["vendor"])
    return peer


def find_device_ip(device_id):
    """
    Author - Jonathan Steward
    Function - find the RID of the device required along with some other details 
    Inputs - int - device_id - device_id of the request device
    returns -
        string - RID of device
        string - Vendor of device
        int - ASN of device
    """
    command = """
    SELECT ip, vendor, asn from `FYP Data`.device_table
    WHERE device_id = {}
    """.format(device_id)
    data = get_data(command)
    if len(data) > 1:
        print_error("There multipul devices listed under device_id {} somehow".format(device_id))
        return "", "", ""
    if len(data) == 0:
        print_error("No Data was found for device_id {}".format(device_id))
        return "", "", ""
    print data[0]
    return data[0][0], data[0][1], data[0][2]


def configure_peer_cisco(peer, device):
    """
    Author - Jonathan Steward
    Function - Steps through the different configuration commands to configure a peer on cisco
    Inputs - 
        dict - peer - details of peer
        object - device - details of device
    returns -
        bool - state of configuration
    """
    connection = ssh_connection(device)
    if not connection:
        return False

    # Attempt to log into config
    command = ("\nen\n{}\nconfig t\n\n\n\n\n".format(device.enablePassword))
    connection.send(command)
    time.sleep(0.5)
    output = connection.recv(8000)
    if "#" not in output:
        print_error("password was wrong!, see below for the issue:\n{}".format(output))
        return False
    print output

    command = "\nrouter bgp {}\n".format(peer["local_asn"])
    connection.send(command)
    time.sleep(0.5)
    output = connection.recv(8000)
    if "(config-router)" not in output:
        print_error("Local BGP ASN defined in database is incorrect:\n{}".format(output))
        return False
    print output

    command = "\nneighbor {} remote-as {}\n".format(peer["remote_ip"], peer["remote_asn"])
    connection.send(command)
    time.sleep(0.5)
    output = connection.recv(8000)
    if "% Invalid" in output:
        print_error("Something went wrong with configuration:\n{}".format(output))
        return False
    print output

    if peer["loopback_source"]:
        command = "\nneighbor {} update-source {}\n".format(peer["remote_ip"], peer["source_interface"])
        connection.send(command)
        time.sleep(0.5)
        output = connection.recv(8000)
        if "% Invalid" in output:
            print_error("Something went wrong with configuration:\n{}".format(output))
            return False
        print output

        if peer["remote_asn"] != device.asn:  # Need to configure for ebgp multi hop
            command = "\nneighbor {} ebgp-multihop 5\n".format(peer["remote_ip"])
            connection.send(command)
            time.sleep(0.5)
            output = connection.recv(8000)
            if "% Invalid" in output:
                print_error("Something went wrong with configuration:\n{}".format(output))
                return False
            print output

    print_error("configured BGP neighbour")
    
    command = "\nend\ncopy run start\n"
    connection.send(command)
    time.sleep(1)
    
    return True


def configure_peer_juniper(peer, device):
    """
    Author - Jonathan Steward
    Function - Identifies the XML configuration to push to the juniper device
    Inputs -
        dict - peer - details of peer
        object - device - details of device
    returns -
        bool - state of configuration
    """
    print ("remote_asn {} device asn {}".format(peer["remote_asn"], device.asn))
    if int(peer["remote_asn"]) == int(device.asn):  # Need to configure for ebgp
        group = "auto-configured-internal"
    else:
        group = "auto-configured-external"

    if peer["loopback_source"]:
        unit_interface = peer["source_interface"]+".0"
        peer["interface_ip"] = grab_interface_ip(
            unit_interface,
            peer["device_id"])
        if peer["interface_ip"] is False:
            print "failed to get interface_ip"
            return False
        local_address = "\n<local-address>{}</local-address>".format(peer["interface_ip"])
        multihop = "\n<multihop>\n</multihop>"
    else:
        multihop = ""
        local_address = ""

    configuration = """
    <configuration>
            <protocols>
                <bgp>
                    <group>
                        <name>{group}</name>
                        <neighbor>
                            <name>{peer_address}</name>
                            {multihop}
                            {local_address}
                            <peer-as>{peer_as}</peer-as>
                        </neighbor>
                    </group>
                </bgp>
            </protocols>
    </configuration>
    """.format(
        group=group,
        peer_address=peer["remote_ip"],
        multihop=multihop,
        local_address=local_address,
        peer_as=peer["remote_asn"])
    state = Juniper_config(configuration, device)
    return state


def check_peer_status(device_ip, remote_ip, device):
    """
    Author - Jonathan Steward
    Function - polls SNMP for the state of the Peer configured and returns details
    Inputs - 
        string - device_ip - ip address of the device with the target peer
        string - remote_ip - ip address of neighbour
        object - device - Device object storing all details 
    returns -
        bool - state of peer, if established true 
    """
    print"waiting for BGP to connect after configuration"
    time.sleep(30)

    result = SnmpPoll(
        "GET",
        ".1.3.6.1.2.1.15.3.1.2.{}".format(remote_ip),
        device_ip,
        device.community)
    print result.value
    if result.value == "1":
        print_error("neighbour is idle")
    elif result.value == "2":
        print_error("neighbour is in connect state")
    elif result.value == "3":
        print_error("neighbour is active")
    elif result.value == "4":
        print_error("neighbour is in open sent state")
    elif result.value == "5":
        print_error("neighbour is openconfirm")
    elif result.value == "6":
        print_error("neighbour is established")
    else:
        print_error("neighbour wasn't at all configured")

    if result.value == "6":
        return True
    return False


def main():
    tool_log = ToolLog("configure bgp peers", "")
    configures, checks, fails, non_approved = check_for_peers()
    variables = """Following peer_id's configured: {} Following peer_id's where checked as they where not up previously: {} Following peer_id's where checked or configured but failed {} Following peer_id's are yet to be approved {}""".format(
        configures, checks, fails, non_approved)
    # Variables line can't have new line chars as mysql doesn't like it!
    tool_log.set_tool_log(True, variables=variables)


if __name__ == "__main__":
    main()
