from SNMPPoll import SnmpPoll
from mysql import connector
from mysql.connector import DatabaseError
import getpass
import time
import re


def check_ip(ip):
    """
    Author - Jonathan Steward
    Function - Takes in an ip address and then returns the state of the ip to determine if its valid
    Inputs - ip - String
    returns - bool - state of if the ip is valid or not
    """

    ip_split = ip.split(".")
    if len(ip_split) != 4:
        print_error("ip isn't in correct format and doesn't have 4 sections, only takes ipv4\n e.g: 192.168.0.1")
        return
    octect_pos = 1
    for octect in ip_split:
        try:
            octect = int(octect)#change section to int, if a number this will work if any char's this won't work
        except ValueError:
            print_error("please ensure that each part of the ip address is a number and includes no characters\n e.g: 192.168.0.1")
            return
        if octect_pos == 4:
            if octect > 255:
                print_error("The Address provided is not a valid address as one or more octect is higher than 254")
                return
        else:
            if octect > 254:
                print_error("The Address provided is not a valid address as one or more octect is higher than 254")
                return
        octect_pos += 1
    return True


def print_error(error):
    """
    Author - Jonathan Steward
    Function - Nice print fuction highlight errors or certain messages
    Inputs - String - error message 
    """
    width = 60
    print '=' * width
    print error
    print '=' * width


def Grab_device_interfaces_snmp(ip, community):
    """
    Author - Jonathan Steward
    Function -
        Attempts to get all the devices interfaces
        Attempts 3 times before returning.
        Returns the list of SNMP results
    Inputs -
        ip - string - ip address of device
        community - string - community string, could be added to include authentication details
    returns - 
        list containing interface name and oid_index or empty string if failed
    """
    print "polling"
    device_interfaces = SnmpPoll('WALK', '.1.3.6.1.2.1.2.2.1.2', ip, community)
    # ifdesc standard
    if device_interfaces:
        # print "found device_interfaces"
        return device_interfaces
    else:
        print_error("Failed on the 3rd attempt trying to gather SNMP data, quitting")
        return ""
           


def get_data(query):
    """
    Author - Jonathan Steward
    Function - Used to get data from the Database based on a pre-defined SQL Query
    Inputs - string - query to use when getting data
    returns - list - resulting data
    """
    try:
        DBconnection = connector.connect(
            user="root",
            password="test",
            host="127.0.0.1",
            database="FYP Data")
        # This should be put off into some more secure method in the real world implementation
    except DatabaseError as error:
        print_error("Couldn't connect to DB because:{}".format(error))
        return ""
    # print_error("executing the following command:\n{}".format(query))
    DBcursor = DBconnection.cursor()
    DBcursor.execute(query)
    database_return = DBcursor
    result = []
    for line in database_return:
        result.append(line)
    return result


def set_data_mysql(command):
    """
    Author - Jonathan Steward
    Function - Used to set data, different from get data as it needs the commit command.
    Inputs - string - commandd to set data
    """
    try:
        DBconnection = connector.connect(
            user="root",
            password="test",
            host="127.0.0.1",
            database="FYP Data")
        # This should be put off into some more secure method in the real world implementation
    except DatabaseError as error:
        print_error("Couldn't connect to DB because:{}".format(error))
        return
    DBcursor = DBconnection.cursor()
    # print_error("executing the following command:\n{}".format(command))
    DBcursor.execute(command)
    # Need to commit otherwise the added/updated interface isn't actually added
    DBconnection.commit()


def get_config_lock(ip, script):
    """
    Author - Jonathan Steward
    Function -
        check the database for the config lock
        if no config lock it will get a config lock
        once attempted will re-check to verify it has a config lock
    Inputs -
        ip - String - ip address of device getting a config lock for
        script - String - script that needs the config lock
    returns -
        bool - Shows state of if its got the lock correctly
    """
    attemps = 0

    while attemps < 3:
        print "checking for config lock"

        config_lock = check_config_lock(ip)
        if not config_lock:
            print "setting config lock"
            set_config_lock(ip, True, script)
            break
        else:
            attemps += 1
            if attemps == 3:
                print_error("Failed on the 3rd attempt trying to get config lock because, quitting")
                return False
            print_error("issue getting a config lock, that was attempt {}".format(attemps))
            time.sleep(15)

    config_lock = check_config_lock(ip)
    if not config_lock:
        print_error("Tried to get a config lock as its not applied but failed??")
        return False
    else:
        return True


def check_config_lock(ip):
    """
    Author - Jonathan Steward
    Function - checks db for config lock on device
    Inputs - ip - string - ip address of device
    returns - Bool - State of config lock
    """
    query = """
    SELECT config_lock, config_lock_reason FROM `FYP Data`.device_table
    WHERE ip='{}';""".format(ip)
    result = get_data(query)
    if result[0][0] == 0:
        return False
    else:
        print_error("config_lock applied for {}".format(result[0][1]))
        return True


def set_config_lock(ip, state, script):
    """
    Author - Jonathan Steward
    Function -
        Used to set the config lock for a certain device. 
        When setting it gives details of why its being set
        Uses state to identify if we want to set a config lock or remove it.
    Inputs -
        ip - String - Device to set config lock to 
        state - Bool - state of config lock needed, false remove, True set config lock
        script - String - Script that needs config lock
    """
    query = """
    SELECT device_id FROM `FYP Data`.device_table
    WHERE ip='{}';
    """.format(ip)
    result = get_data(query)
    device_id = result[0][0]
    reason = "{} running {}".format(getpass.getuser(), script)
    if state:
        query = """
        UPDATE `FYP Data`.`device_table`
         SET `config_lock`='1', `config_lock_reason`='{}'
         WHERE `device_id`='{}';
        """.format(reason, device_id)
        set_data_mysql(query)

    else:
        query = """
        UPDATE `FYP Data`.`device_table`
         SET `config_lock`='0', `config_lock_reason`=''
         WHERE `device_id`='{}';
        """.format(device_id)
        set_data_mysql(query)


def get_device_id(ip):
    """
    Author - Jonathan Steward
    Function - Grab the device ID given the device ip
    Inputs - string - ip address
    returns - int - Device ID that relates to the database entry
    """
    query = """
    SELECT device_id FROM `FYP Data`.device_table
    WHERE ip='{}';""".format(ip)
    data = get_data(query)
    if not data:
        print_error("no device with that ip")
        return"0"
    return data[0][0]


def device_config_info_lookup(ip):
    from Classes import Device_object
    """
    Author - Jonathan Steward
    Function - Grab all the details about the device needed to configure/poll correctly.
    Inputs - ip address - String
    returns - 
        bool - State of if we have data to return
        device object - object with all the relevant details
    """
    query = """
    SELECT vendor,community,username,loginpassword,enpassword,asn FROM `FYP Data`.device_table
    WHERE ip='{}';""".format(ip)
    #print_error("sending following query to DB:\n{}".format(query))

    data = get_data(query)
    if not data:
        print_error("something wrong getting device information")
        return(False, "")

    if len(data) > 1:
        print_error("more than one device record, can't carry out automation")
        # email admin
        return (False, "")

    data = data[0]
    # data is a list of vendor,community,username,loginpassword,enpassword
    device = Device_object(ip, data[2], data[3], data[4], data[0])
    device.community = data[1]
    device.asn = data[5]

    return (True, device)


def grab_interface_ip(interface, device_id):
    """
    Author - Jonathan Steward
    Function - Take in interface name and find its ip
    Inputs - 
        interface - string - interface name
        device_id - int - device_id as found in the database
    returns -
        string - ip address of the interface
    """
    match_interface_name = "(Ethernet|FastEthernet|GigabitEthernet|TenGigE|fe-|ge-|xe-|et-|lo)"
    # Juniper doesn't have a standard ethernet but does have fast,gig,ten and 100 gig code prefix
    match_interface_number = "((\d+\/)+)*\d+"
    regex = match_interface_name + match_interface_number
    verify_interface = re.match(regex, interface)
    if not verify_interface:
        print_error("interface {} is not valid".format(interface))
        return False

    command = """
    SELECT ip_address FROM `FYP Data`.interfaces
    WHERE name = "{}" AND device_id = "{}"
    """.format(interface, device_id)
    results = get_data(command)
    print results
    if len(results) > 1:
        print_error("Too many results found for that interface")
        return False
    if len(results) == 0:
        print_error("No Results found for that interface")
        return False
    return results [0][0]
