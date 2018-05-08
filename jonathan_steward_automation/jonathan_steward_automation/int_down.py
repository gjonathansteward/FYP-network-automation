from common_tasks import print_error, get_data, device_config_info_lookup
from lagchanger import process_lag_change
import re


def interface_down_check(message, ip):
    """
    Author - Jonathan Steward
    Function - workflow function for calling the relevent checks and then automation
    Inputs -
        message - string - syslog message 
        ip - string - ip address of sending device
    returns -
        bool - state of if it matched the regex
        string - the issue with the message, if matched this will detail the ip address of device
                 and the ip of the device with the interface down.
    """

    state, int_down = message_check(message)

    if not state:
        #print_error("The following message didn't match the regex needed  so no interface went physically down\n {}".format(message))
        return (False, "", False)

    print_error(message)

    issue = "{} interface on {} is down".format(int_down, ip)

    state, device = device_config_info_lookup(ip)

    if not state:
        # no data/too much data.
        return (True, issue, False)

    return_message, acted = process_down(int_down, device)
    issue = "{} {}".format(issue, return_message)
    return True, issue, acted


def message_check(message):
    """
    Author - Jonathan Steward
    Function - checks the message to see if it matches correctly against what we want to look for
    Inputs - 
        message - string - message input from the syslog monitor
    returns -
        Bool - State of if it matched the regex
        string - interface that went down
    """
    # used to match the corect regex and grab the interface that is down

    match_interface_name = "(Ethernet|FastEthernet|GigabitEthernet|TenGigE|fe-|ge-|xe-|et-)"
    # Juniper doesn't have a standard ethernet but does have fast,gig,ten and 100 gig code prefix
    match_interface_number = "((\d+\/)+)*\d+"

    # first cisco
    interface_downregex_cisco = ".*LINK-3-UPDOWN: Interface (?P<interface>{}{}).* down".format(match_interface_name, match_interface_number)
    int_down = re.match(interface_downregex_cisco, message)

    # second juniper
    if not int_down:
        interface_downregex_juniper = ".*SNMP_TRAP_LINK_DOWN.*ifName (?P<interface>{}{}).*".format(match_interface_name, match_interface_number)
        int_down = re.match(interface_downregex_juniper, message)

    if not int_down:
        return False, ""

    int_down = int_down.group("interface")
    return True, int_down


def process_down(int_down, device):
    """
    Author - Jonathan Steward
    Function - Call function and evaluate when trying to remove interface from lag
    Inputs -
        int_down - string - interface name that went down
        device - device object storing all details
    returns -
        string - the return message to state what happened
        bool - State of the automation working or not
    """

    print"taking {} out of lag on {}".format(int_down, device.ip)

    state = process_lag_change(
        False,
        device.ip,
        device.username,
        device.password,
        device.vendor,
        int_down,
        "",
        device.community,
        device.enablePassword)
    if not state:
        print_error("Didn't remove interface from lag see above for logs")
        # email admin
        return "Didn't remove interface from lag because of issue raised within automation script", False

    print "message was indicating that interface was down, automation triggered"
    return ("int {} down removed from lag".format(int_down)), True
