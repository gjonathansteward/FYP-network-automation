import argparse

from common_tasks import device_config_info_lookup, get_config_lock, set_config_lock, print_error, check_ip
from Classes import ToolLog
from sshconnection import ssh_connection
from JuniperConfig import Juniper_config
import time
import re
import sys


def setup_steps():
    """
    Author - Jonathan Steward
    Function - carry out arg parse setup taking in arguments and validating that some of them are valid
    returns - argparse object - stores all arguments input
    """
    parser = argparse.ArgumentParser()
    host_help = "Host you wish to target"
    interface_help = "interface you wish to target"
    cost_help = "cost you wish to apply, should be a whole number"


    # in a perfect world this would look up passwords username and vendor detail
    parser.add_argument("-d", "--host",
                        help=host_help, dest="host", required=True)
    parser.add_argument("-i", "--interface",
                        help=interface_help, dest="interface", required=True)
    parser.add_argument("-c", "--cost",
                        help=cost_help, dest="cost", required=True)

    # Note other community data would be needed if a more secure implementation was used.

    arguments = parser.parse_args()

    try:
        int(arguments.cost)
    except ValueError:
        print_error("cost provided isn't a whole number")
        sys.exit()

    # used to match the corect regex and grab the interface that is down

    match_interface_name = "(Ethernet|FastEthernet|GigabitEthernet|TenGigE|fe-|ge-|xe-|et-)"
    # Juniper doesn't have a standard ethernet but does have fast,gig,ten and 100 gig code prefix
    match_interface_number = "((\d+\/)+)*\d+"

    interface_regex = match_interface_name + match_interface_number
    interface_check = re.match(interface_regex, arguments.interface)
    if not interface_check:
        print_error("interface isn't valid")
        sys.exit()

    ip_state = check_ip(arguments.host)
    if not ip_state:
        sys.exit()

    return arguments


def add_cost_workflow(ip, interface, cost, called_from):
    """
    Author - Jonathan Steward
    Function - Workflow function calling relevant functions needed for configuration
    Inputs -
        ip - string - ip address of host on which cost needs to be applied
        interface - string - the interface name of the interface to apply cost to
        cost - int - Cost to apply to the interface
        called_from - string - what is callling this fuction for logging
    returns -
        bool - state of the workflow
    """
    arg_string = "host : {}, interface: {}, cost: {}, called from : {}".format(
        ip,
        interface,
        cost,
        called_from)
    tool = ToolLog("deprefer tool", arg_string)

    state, device = device_config_info_lookup(ip)
    if not state:
        print "didn't get device_config info"
        tool.set_tool_log(False)
        return False
    config_state = False

    print "starting add_cost_workflow"
    if device.vendor == "cisco":
        lock_state = get_config_lock(device.ip, "deprefer tool")
        if lock_state:
            config_state = add_cost_interface_cisco_ospf(device, interface, cost)
            print_error("attempted to configured cisco device")
    elif device.vendor == "juniper":
        lock_state = get_config_lock(device.ip, "deprefer tool")
        if lock_state:
            config_state = add_cost_interface_juniper_ospf(device, interface, cost)
            print_error("attempted to configured juniper device")
    else:
        print "unsupported vendor {}".format(device.vendor)
        tool.set_tool_log(False)
        return False

    set_config_lock(device.ip, False, "deprefer tool")
    print"config lock released"
    tool.set_tool_log(config_state)
    return True


def add_cost_interface_cisco_ospf(device, interface, cost):
    """
    Author - Jonathan Steward
    Function - Sends the relevant commmands to a cisco device to apply ospf cost to interface
    Inputs -
        device - device object - stores relevant details of device for configuration
        interface - string - interface that we are adding cost to
        cost - int - cost to be applied to interface
    returns -
        bool - state of the success of configuration
    """
    connection = ssh_connection(device)
    if not connection:
        return False

    # Attempt to log into config
    command = ("\nen\n{}\nconfig t\n".format(device.enablePassword))
    connection.send(command)
    time.sleep(0.5)
    output = connection.recv(8000)
    if "#" not in output:
        print_error("password was wrong!, see below for the issue:\n{}".format(output))
        return False
    print output

    # Attempt to get to interface prompt
    command = "\ninterface {interface}\n".format(interface=interface)
    connection.send(command)
    time.sleep(0.5)
    output = connection.recv(8000)
    if "(config-if)" not in output:
        print_error("interface {} was wrong, see below for output:\n{}".format(interface, output))
        return False
    print output

    # Attempt to apply to cost
    command = "\nip ospf cost {cost}\n".format(cost=cost)
    connection.send(command)
    time.sleep(0.5)
    output = connection.recv(8000)
    if "% Invalid" in output:
        print_error("something went wrong, might not be a L3 interface:{}".format(output))
        return False
    print output
    
    command = "\nend\ncopy run start\n"
    connection.send(command)
    time.sleep(1)

    print_error("configured cost correctly")
    return True


def add_cost_interface_juniper_ospf(device, interface, cost):
    """
    Author - Jonathan Steward
    Function - Creating configuration and calling the application of the configuration
    Inputs -
        device - device object - stores relevant details of device for configuration
        interface - string - interface that we are adding cost to
        cost - int - cost to be applied to interface
    returns -
        bool - State of if the configuration worked or not
    """
    configuration = """
    <configuration>
        <protocols>
            <ospf>
                <area>
                    <name>0.0.0.0</name>
                    <interface>
                        <name>{interface}</name>
                        <metric>{metric}</metric>
                    </interface>
                </area>
            </ospf>
        </protocols>
    </configuration>
    """.format(interface=interface, metric=cost)
    config_state = Juniper_config(configuration, device)
    if config_state:
        return True
    return False


def main():
    args = setup_steps()
    ip = args.host
    interface = args.interface
    cost = args.cost
    state = add_cost_workflow(ip, interface, cost, "CLI")
    print_error("finished add cost workflow")



if __name__ == "__main__":
    main()
