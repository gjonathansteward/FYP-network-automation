from JuniperConfig import Juniper_config
from Classes import Device_object, ToolLog
from sshconnection import ssh_connection
from SNMPPoll import SnmpPoll
from common_tasks import print_error, Grab_device_interfaces_snmp, get_config_lock, set_config_lock, check_ip, device_config_info_lookup
import time
import argparse
import getpass
import re


def setup_steps():
    """
    Author - Jonathan Steward
    Function - carry out arg parse setup taking in arguments and validating that some of them are valid
    returns - argparse object - Stores all arguments given to the code
    """
    parser = argparse.ArgumentParser()
    activate_help = "use this to activate the lag, default is to deactivate"
    host_help = "use this to enter the host details"
    # NOTE a company would possibly have their own password/auth system with creds for automation
    # this isn't being emulated as its just proof of concept
    interface_help = "enter the full interface name as shown under show interface CASE SENSITIVE"
    aggport_help = "enter the number of the AE or Port-channel group, scrip will complete based on vendor"

    # in a perfect world this would look up passwords username and vendor detail
    parser.add_argument("-a", "--activate",
                        help=activate_help, dest='activate', default=False, action='store_true')
    parser.add_argument("-d", "--host",
                        help=host_help, dest="ip", required=True)
    parser.add_argument("-i", "--interface",
                        help=interface_help, dest="interface", required=True)
    parser.add_argument("-g", "--aggport",
                        help=aggport_help, dest="ae_int", default="")

    arguments = parser.parse_args()
    activate = arguments.activate
    if not arguments.ae_int:
        if activate:
            print_error("Trying to add interface but no AE port provided this isn't possible")
            return
        print_error("No AE given will attmept to find the AE to remove")
    else:
        try:
            arguments.ae_int = int(arguments.ae_int)
        except ValueError:
            print_error("Please input agg port as a number not full AE or Port-channel \nUsing -g --aggport you inputted {}". format(arguments.ae_int))
            return

    ip_state = check_ip(arguments.ip)
    if not ip_state:
        return

    match_interface_name = "(Ethernet|FastEthernet|GigabitEthernet|TenGigE|fe-|ge-|xe-|et-)"
    int_state = re.match(match_interface_name, arguments.interface)
    if not int_state:
        print_error("Interface {} is not valid, please enter the full name. Cisco is case SENSITIVE".format(arguments.interface))
        return

    return arguments


def verify_arguments(arguments):
    """
    Author - Jonathan Steward
    Function - asks user for verification before carrying out any external calls
    Inputs - argparse object 
    returns - bool - determines the state of if the arguments
    """
    confirm_statement = """
    Please confirm the following settings:
    Adding to lag?: {addremove}
    Device: {ip}
    Interface: {int}
    Agg port: {ae}
    If you are adding an interface to a group, please ensure the group port exists
    """
    print confirm_statement.format(
        addremove=arguments.activate,
        ip=arguments.ip,
        int=arguments.interface,
        ae=arguments.ae_int)

    confirmed = ""
    while confirmed != "y":
        confirmed = raw_input("y/n:")
        confirmed = confirmed.lower()
        if confirmed == "n":
            print_error("quitting due to user inputs")
            return False
        elif confirmed == "y":
            user = getpass.getuser()
            print "user {} confirmed".format(user)
        else:
            print_error("please a single y or n")
    return True


def process_lag_change(
    activate, ip,
    username, password,
    vendor, interface,
    ae_int, community,
    enpassword="cisco",
):
    """
    Author - Jonathan Steward
    Function - main workflow of the process to remove interface from lag on device
    Inputs - 
        activate - bool - identifies if the interface should be added or removed
        ip - string - ip address of the host 
        username - string - username needed to log into the device
        password - string - password needed to log into the device
        vendor - string - the vendor of the device
        interface - string - interface you want to add or remove
        ae_int - int - lag you want to remove interface from
        community - string - snmp community used for polling information from device
        enpassword - string - default to "cisco", needed to configure cisco devices
    returns - bool - determines if the automation worked correctly
    """
    variables = [
        "activate = {}".format(activate),
        "ip = {}".format(ip),
        "username = {}".format(username),
        "password = {}".format(password),
        "vendor = {}".format(vendor),
        "interface = {}".format(interface),
        "ae_int = {}".format(ae_int),
        "community = {}".format(community),
        "enpassword = {}".format(enpassword)
    ]
    print variables

    tool_log = ToolLog("lagchanger", variables)

    state = get_config_lock(ip, "lagchanger")
    if not state:
        tool_log.set_tool_log()
        return False

    device_details = Device_object(
        ip,
        username,
        password,
        enpassword,
        vendor.lower())

    int_state, original_ae_int = int_in_ae(device_details.ip, ae_int, interface, community, activate, 1)
    if not int_state and original_ae_int == "bad":
        print_error("intended ae not found")
        set_config_lock(ip, False, "lagchanger")
        tool_log.set_tool_log(True)
        return False

    if activate:
        if int_state:
            # trying to add and also in lag
            # pointless
            print_error("interface is already in a lag, can't configure")
            set_config_lock(ip, False, "lagchanger")
            tool_log.set_tool_log(True)
            return False
        else:
            # trying to add but not in lag
            print "trying to add as not in lag"
            if device_details.vendor == "cisco":
                state = change_int_lag_state_cisco(True, interface, device_details, ae_int)
            elif device_details.vendor == "juniper":
                state = change_int_lag_state_juniper(True, interface, device_details, ae_int)
    else:
        if int_state:
            # Trying to remove and in lag
            print "trying to remove as in lag"
            if device_details.vendor == "cisco":
                state = change_int_lag_state_cisco(False, interface, device_details, ae_int)
            elif device_details.vendor == "juniper":
                state = change_int_lag_state_juniper(False, interface, device_details, ae_int)
        else:
            # Trying to remove and not in lag
            # pointless
            if device_details.vendor == "cisco":
                print_error("interface not showing as in lag but cisco devices do this when they are phy down")
                state = change_int_lag_state_cisco(False, interface, device_details, ae_int)
            else:
                print_error("interface is already out of lag, no need to remove further")
                set_config_lock(ip, False, "lagchanger")
                tool_log.set_tool_log(True)
                return False

    if not state:
        print_error("something failed while configuring, quitting")
        set_config_lock(ip, False, "lagchanger")
        tool_log.set_tool_log()
        return False

    print_error("config should have been applied, waiting some time to ensure connection is stable")
    time.sleep(30)
    int_state, ae_int = int_in_ae(device_details.ip, ae_int, interface, community, activate, 2)

    check_success(activate, int_state, interface, ae_int)

    set_config_lock(ip, False, "lagchanger")
    tool_log.set_tool_log(True)
    return True


def int_in_ae(ip, ae_int, interface, community, activate, stage):
    """
    Author - Jonathan Steward
    Function - identifies if the interface is in the lag and if so what lag.
    Inputs - 
        ip - string
        ae_int - string
        interface - string
        community - string
    returns - 
        bool - state of if the interface is in lag
        int - ae_int the interface is in.
    """
    state, ae_index, interface_index, device_interfaces = find_ae_int_ref(ip, ae_int, interface, community, activate)
    # print interface_index
    # print ae_index
    if ae_index == "bad":
        return False, "bad"
    if not state:
        # Error messages in find_ae_int
        return False, ""
    if not activate and stage == 1:
        if ae_int:
            return True, ae_int
        else:
            return True, ""
    result = SnmpPoll('GET', '.1.2.840.10006.300.43.1.2.1.1.13.{}'.format(interface_index), ip, community)
    print result

    if not ae_index:
        if not result.oid_index:
            print_error("no AE interface found assigned to interface")
            if activate:
                return False, ""
        for inter in device_interfaces:
            if inter.oid_index == result.value:
                ae_int = inter.value
                print_error("Found AE port {}".format(ae_int))
                return True, ae_int
    elif result.value == ae_index:
        return True, ae_int

    return False, ae_int


def find_ae_int_ref(ip, ae_int, interface, community, activate):
    """
    Author - Jonathan Steward
    Function - identify the lag and interface ifindex and all interfaces
    Inputs - 
        ip - string
        ae_int - string
        interface - string
        community - string
    returns - 
        bool - state of if interface and lag found
        int - ae_index
        int - interface_index
        list - device_interfaces
    """
    interface_unit = interface + ".0"

    device_interfaces = Grab_device_interfaces_snmp(ip, community)

    ae_index = ""
    interface_index_unit = ""
    interface_index = ""
    print "checking for ae {}".format(ae_int)

    for inter in device_interfaces:
        if ae_int:
            if str(inter.value) == str(ae_int):
                ae_index = inter.oid_index
                print "found matching AE index from list of interfaces"
                print ae_index
                continue

        if str(inter.value) == str(interface_unit):
            interface_index_unit = inter.oid_index
            print "found interface_unit index"
            print interface_index_unit
            continue
        if str(inter.value) == str(interface):
            interface_index = inter.oid_index
            print "found interface index"
            print interface_index
            continue

    if not interface_index:
        print_error("requested interface {} not found at all, please re-check".format(interface))
        return False, "", "", ""
    if interface_index_unit:
        interface_index = interface_index_unit

    if not ae_index:
        print_error("{} not found on device".format(ae_int))
        if activate:
            return False, "bad", "", ""

    return True, ae_index, interface_index, device_interfaces


def change_int_lag_state_cisco(addornot, interface, device_details, ae_int):
    """
    Author - Jonathan Steward
    Function - Configure cisco device to either add or remove interface from group
    Inputs - 
        addornot - bool
        interface - string
        device_details - object
        ae_int - int 
    returns - bool - state of if the config was applied or not.
    """
    if not ae_int:
        pass
    else:
        ae_int_number = ae_int.split("Port-channel")[1]

    connection = ssh_connection(device_details)
    if not connection:
        return False

    command = ("\nen\n{}\nconfig t\n\n\n\n\n".format(device_details.enablePassword))
    connection.send(command)
    time.sleep(0.5)
    output = connection.recv(8000)
    if "#" not in output:
        print_error("password was wrong!, see below for the issue:\n{}".format(output))
        return False
    print output

    if addornot:
        lagcommand = "\ninterface {}\n channel-group {} mode active\n".format(interface, ae_int_number)
    else:
        lagcommand = "\ninterface {}\nno channel-group\n".format(interface)

    connection.send(lagcommand)
    time.sleep(1)

    output = connection.recv(8000)

    if "% Invalid arguments detected" in output:
        print_error("something went wrong, see below:{}".format(output))

    print "applied config as seen below:\n{}".format(output)
    
    command = "\nend\ncopy run start\n"
    connection.send(command)
    time.sleep(1)
    
    return True


def change_int_lag_state_juniper(addornot, interface, device_details, ae_int):
    """
    Author - Jonathan Steward
    Function - apply configuration to remove/add interface to a lag on juniper device
    Inputs - 
        addornot - bool
        interface - string
        device_details - object
        ae_int - int 
    returns -  bool - state of if the config was applied or not.
    """

    if addornot:
        state = 'active="active"'.format(ae_int)
        configuration = """
            <configuration>
                <interfaces>
                    <interface>
                        <name>{interface}</name>
                        <ether-options {state}>
                            <ieee-802.3ad>
                                <bundle>{ae}</bundle>
                            </ieee-802.3ad>
                        </ether-options>
                    </interface>
                </interfaces>
            </configuration>
            """.format(interface=interface, state=state, ae=ae_int)
    else:
        state = 'inactive="inactive"'.format(ae_int)
        configuration = """
            <configuration>
                <interfaces>
                    <interface>
                        <name>{interface}</name>
                        <ether-options {state}>
                        </ether-options>
                    </interface>
                </interfaces>
            </configuration>
            """.format(interface=interface, state=state)

    
    print "attempting to apply the following config:/n {}".format(configuration)
    state = Juniper_config(configuration, device_details)
    return state


def check_success(activate, int_state, interface, ae_int):
    """
    Author - Jonathan Steward
    Function - Simple function to check if an interface was added into lag and output to user/logs
    Inputs - 
        activate - bool
        int_state - bool
        interface - string
        ae_int - int 
    """

    if activate:
        if int_state:
            # trying to add and also in lag
            # success
            print_error("{} was added to {}".format(interface, ae_int))
        else:
            # trying to add but not in lag
            # fail
            print_error("{} was not added to {} for some reason, might be down other end".format(interface, ae_int))
    else:
        if int_state:
            # Trying to remove and in lag
            # fail
            print_error("{} was not removed from {} for some reason".format(interface, ae_int))
        else:
            print_error("{} was removed from lag {}".format(interface, ae_int))


def main():

    arguments = setup_steps()
    if not arguments:
        print_error("Invalid arguments")
        return

    state, device = device_config_info_lookup(arguments.ip)
    # device vendor,community,username,loginpassword,enpassword
    if not state:
        return

    if device.vendor == "cisco":
        arguments.ae_int = "{}{}".format("Port-channel", arguments.ae_int)
    elif device.vendor == "juniper":
        arguments.ae_int = "{}{}".format("ae", arguments.ae_int)
    else:
        print_error("The vendor '{}' isn't valid please re-try".format(arguments.vendor))
        return
    state = verify_arguments(arguments)
    if state:
        process_lag_change(
            arguments.activate,
            arguments.ip,
            device.username,
            device.password,
            device.vendor,
            arguments.interface,
            arguments.ae_int,
            device.community,
            device.enablePassword)


if __name__ == "__main__":
    main()
