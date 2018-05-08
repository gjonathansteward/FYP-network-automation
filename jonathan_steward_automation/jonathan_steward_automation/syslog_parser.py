from common_tasks import print_error, set_data_mysql, get_device_id, check_ip, get_data

import re

# Workflows
from int_down import interface_down_check


def parse_message(message):
    """
    Author - Jonathan Steward
    Function - Takes in a message and runs checks for each message
    Inputs - message - String
    returns -
        string - ip address of device sending message
        issue - the issue that was found (link down for example)
        acted - if the automation acted on the message.
    """
    ip = identify_ip(message)
    if not ip:
        return ("", "No valid ip detected in message", False)

    device_RID = identify_device_RID_from_int_ip(ip)

    state, issue, acted = interface_down_check(message, device_RID)
    if state:
        return (device_RID, issue, acted)

    # Add in extra checks here

    if not issue:
        issue = "Following message was recieved but didn't match any filters\n{}".format(message)

    return (device_RID, issue, acted)


def identify_device_RID_from_int_ip(ip):
    """
    Author - Jonathan Steward
    Function - finds the device_id based on interface ip
    Inputs - String - Ip address of interface
    returns - int - ID of related device
    """
    command = """
    SELECT device_id from `FYP Data`.interfaces
    WHERE ip_address = '{}';""".format(ip)

    result = get_data(command)
    print "device_id for {} ip is {}".format(ip, result)
    if not result:
        print_error("something wrong getting device information")
        return(False, "")

    if len(result) > 1:
        print_error("more than one device record, can't carry out automation")
        # email admin
        return (False, "")

    result = result[0][0]
    print "device id is {}".format(result)
    command = """
    SELECT ip from `FYP Data`.device_table
    WHERE device_id = '{}';""".format(result)

    result = get_data(command)

    print "device RID is {}".format(result[0][0])


    return result[0][0]


def identify_ip(message):
    """
    Author - Jonathan Steward
    Function - From a messagem parse for the ip address
    Inputs - message - string
    returns - ip - string - if failed returns a blank string
    """
    ip_regex = "(?P<host>\d+\.\d+\.\d+\.\d+).*"
    ip = re.match(ip_regex, message)
    if not ip:
        print_error("Syslog message not valid!: \n{}".format(message))
        return ""
    ip = ip.group("host")
    ip_state = check_ip(ip)
    if not ip_state:
        return ""
    return ip


def record_actions(host, message, issue, acted):
    """
    Author - Jonathan Steward
    Function - sends details to db about event and what happened
    Inputs -
        host - string
        message - string
        issue - string
        acted - bool
    """
    device_id = get_device_id(host)
    command = """
    INSERT INTO `FYP Data`.`syslog_events` (`syslog detail`, `device_id`, `acted_on`, `message`)
     VALUES ("{}", "{}", "{}", "{}");
    """.format(issue, device_id, acted, message)
    if "License" in message:
        pass
    elif "bgp" in message:
        pass
    else:
        print_error("sending following command to log event\n{}".format(command))

    set_data_mysql(command)


def parse(message):
    """
    Author - Jonathan Steward
    Function - Function called from the monitor calls all other functions.
    Inputs - message - string
    """
    print "recieved message:\n {}".format(message)
    device_RID, issue, acted = parse_message(message)
    print_error("{}, {}\n Was it acted on: {}".format(device_RID, issue, acted))
    record_actions(device_RID, message, issue, acted)
