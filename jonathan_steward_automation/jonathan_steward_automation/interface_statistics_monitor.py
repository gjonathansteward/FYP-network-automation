from common_tasks import Grab_device_interfaces_snmp, get_data, set_data_mysql, device_config_info_lookup, print_error
from SNMPPoll import SnmpPoll as snmppoll
from datetime import datetime
from int_down import process_down
from threading import Thread
from deprefer_automation import add_cost_workflow
import time
import sys

percentage_threashold = 10
interval = 5
minuets = 5


def match_db_to_device(device_interfaces, device_id):
    """
    Author - Jonathan Steward
    Function - Take the list of interfaces and match up to the database interface and link the database
               information with the local interface
    Inputs - 
        device_interfaces - list - list of interfaceobjects from SNMP gets
        device_id - 
    returns - 
        device_interfaces - list - list of interface objects from snmp gets with database info
    """
    command = "SELECT * FROM `FYP Data`.interfaces where device_id = {}".format(device_id)
    # data will be ID/device_id/name/description/ip_address/state/lastupdate/traffic_counter/speed
    db_interfaces = get_data(command)
    for i in range(len(device_interfaces)):
        for db_int in db_interfaces:
            if device_interfaces[i].value == db_int[2]:
                name = str(device_interfaces[i].value)
                oid_index = int(device_interfaces[i].oid_index)
                device_interfaces[i] = {"name": name, "oid_index": oid_index}
                device_interfaces[i]["db_id"] = db_int[0]
                device_interfaces[i]["previous_update"] = db_int[6]
                device_interfaces[i]["previous_counter"] = db_int[7]
                device_interfaces[i]["speed"] = db_int[8]
                break
    return device_interfaces


def print_polling_traffic_stats(device_int):
    """
    Author - Jonathan Steward
    Function - print out traffic stats for the interval polling of the interface
    Inputs - 
        device_int - object - combined database and snmp gathered information
    returns - n/a
    """
    print "previous counter {}".format(device_int["previous_counter"])
    print "current_counter {}".format(device_int["current_counter"])
    print "bits_out {}".format(device_int["bits_out"])
    print "time_of poll {}".format(device_int["update_time"])
    print "previous_update {}".format(device_int["previous_update"])
    print "secounds since {}".format(device_int["seconds_since"])
    print "bits_per_sec {}".format(device_int["bits_per_sec"])
    print "speed {}".format(device_int["speed"])
    print "util_percentage {}".format(device_int["util_percentage"])
    print "util_percentage after round {}".format(device_int["util_percentage"])


def poll_traffic(device_interfaces, device_ip, community):
    """
    Author - Jonathan Steward
    Function - Polls Device for interface counter and then calls traffic automation for loops
    Inputs -
        device_interfaces - list - list of interface objects from snmp gets with database info
        device_ip - string - ip address of host with high utilization
        community - string - community string needed for SNMP
    returns - n/a
    """
    interfaces_traffic = snmppoll("WALK", ".1.3.6.1.2.1.31.1.1.1.10", device_ip, community)
    time_now = datetime.now()
    print "polled interface traffic on {}".format(device_ip)
    if not interfaces_traffic:
        print_error("no interface traffic stats reutrned!")
        return
    for int_traffic in interfaces_traffic:
        for i in range(len(device_interfaces)):
            if int(int_traffic.oid_index) != int(device_interfaces[i]["oid_index"]):
                # Not a matched interface
                continue

            if device_interfaces[i]["speed"] == 0:
                # Will always alarm no need for this
                break

            device_interfaces[i]["current_counter"] = int(int_traffic.value)

            state, device_interfaces[i] = calculate_interface_util(device_interfaces[i], time_now)
            if not state:
                break

            if device_interfaces[i]["util_percentage"] > 1:
                print_polling_traffic_stats(device_interfaces[i])

                print "threashold is {}% current usage is {}% on {} for {} device".format(
                    percentage_threashold,
                    device_interfaces[i]["util_percentage"],
                    device_interfaces[i]["name"],
                    device_ip)
            update_interface_and_history(device_interfaces[i])

            if device_interfaces[i]["util_percentage"] > percentage_threashold:
                print "interface {} on {} is at {}% which is above threashold".format(
                    device_interfaces[i]["name"],
                    device_ip,
                    device_interfaces[i]["util_percentage"])
                traffic_automation(device_interfaces[i], device_ip, community)
                #t = Thread(target=traffic_automation, args=(device_interfaces[i], device_ip, community,))
                #t.start()


def calculate_interface_util(device_int, time_now):
    """
    Author - Jonathan Steward
    Function - calculate the utilization on the interface
    Inputs - 
        device_int - object - combined database and snmp gathered information
        time_now - datetime object - Time of the poll for traffic counter
    returns - 
        bool - state of if there was an increase on the counter
        device_int - object - combined database and snmp gathered information
    """
    device_int["current_counter"] = int(device_int["current_counter"])
    device_int["previous_counter"] = int(device_int["previous_counter"])

    if device_int["current_counter"] == device_int["previous_counter"]:
        # print "no traffic on interface {} on {}".format(device_int["name"], device_ip)
        return False, device_int
    device_int["update_time"] = time_now
    device_int["seconds_since"] = (time_now - device_int["previous_update"]).seconds
    device_int["bits_out"] = (device_int["current_counter"] * 8) - (device_int["previous_counter"] * 8)
    max_int = 9223372036854775807
    if device_int["bits_out"] < 0:
        device_int["bits_out"] = (max_int - device_int["previous_counter"]) + device_int["current_counter"]
    device_int["bits_per_sec"] = device_int["bits_out"] / device_int["seconds_since"]
    device_int["util_percentage"] = float(device_int["bits_per_sec"]) * 100 / float(device_int["speed"])
    device_int["util_percentage"] = round(device_int["util_percentage"], 3)
    return True, device_int


def update_interface_and_history(device_int):
    """
    Author - Jonathan Steward
    Function - update the interface details on the database
    Inputs - 
        device_int - object - combined database and snmp gathered information
    returns - n/a
    """
    command = """
        UPDATE `FYP Data`.`interfaces`
        SET `traffic_out_counter`='{}', `last_updated` = '{}'
        WHERE `interface_id`='{}';""".format(
        int(device_int["current_counter"]),
        device_int["update_time"],
        device_int["db_id"])
    set_data_mysql(command)
    #print "updating interface with following mysql command:\n{}".format(command)

    # UPDATE HISTORY FEATURES OMMITTED AS IT WOULD NOT BE USED RIGHT NOW


def check_for_event(device_int, device_ip):
    """
    Author - Jonathan Steward
    Function - checks for an existing event and if one exists if its an old event or not
    Inputs - 
        Global - timeout_minuets - defined at the top to identify how many minuets old an event
                                   needs to be before closing it.
        device_int - object - combined database and snmp gathered information
        device_ip - string - ip address of the host for this event
    returns - 
    """
    command = """
    SELECT * FROM `FYP Data`.interface_events
    where `interface_id` = '{}'
    and `state` = 'active'
    and `issue` = 'out utilization'""".format(device_int["db_id"])
    events = get_data(command)
    if events:
        time_now = datetime.now()
        time_diff = (time_now - events[0][4]).seconds
        timeout_minuets = 5
        if time_diff / 60 > timeout_minuets:
            print_error("closing old event older than {} minuets".format(timeout_minuets))
            command = """
            UPDATE `FYP Data`.`interface_events`
            SET `state` = 'resolved'
            WHERE event_id = {} ;""".format(events[0][0])
            set_data_mysql(command)
        else:
            print "event for {} on {} already exists will not act".format(device_int["name"], device_ip)
            return False
    command = """
    INSERT INTO `FYP Data`.`interface_events` (`interface_id`, `state`, `issue`)
    VALUES ('{}', 'active', 'out utilization');""".format(device_int["db_id"])
    set_data_mysql(command)
    return True


def traffic_automation(device_int, device_ip, community):
    """
    Author - Jonathan Steward
    Function - Checks for event, if no event, will loop calling individual traffic check
               once the check has occured for the identified amount of times will trigger automation
    Inputs - 
        GLOBAL - minuets - Number of minuets/attempts/datapoints to wait till triggering automation
        device_int - object - combined database and snmp gathered information
        device_ip - string - ip address of host with high utilization
        community - string - community string needed for SNMP
    returns - n/a
    """
    state = check_for_event(device_int, device_ip)
    if not state:
        return

    re_tries = 0
    while re_tries < minuets:
        state, device_int = individual_traffic_check(device_int, device_ip, community, re_tries)
        update_interface_and_history(device_int)
        if not state:
            print "interface {} on {} didn't break the threashold on datapoint {} with {}%".format(
                device_int["name"],
                device_ip,
                re_tries,
                device_int["util_percentage"])
            close_event(device_int)
            return
        else:
            re_tries += 1
    #print_error("TRIGGER AUTOMATION")
    state = add_cost_workflow(device_ip, device_int["name"], 10, "automation")
    close_event(device_int)


def close_event(device_int):
    """
    Author - Jonathan Steward
    Function - closes event that was created once automation has been triggered
    Inputs - 
        device_int - object - combined database and snmp gathered information
    returns - n/a
    """
    command = """
    SELECT * FROM `FYP Data`.interface_events
    where interface_id = {} and state ='active' and issue = 'out utilization'""".format(device_int["db_id"])
    event = get_data(command)
    command = """
    UPDATE `FYP Data`.`interface_events`
    SET `state` = 'resolved'
    WHERE event_id = {} ;""".format(event[0][0])
    set_data_mysql(command)
    update_interface_and_history(device_int)


def individual_traffic_check(device_int, device_ip, community, re_tries):
    """
    Author - Jonathan Steward
    Function - checks for one interface the current utilization, calculation of util is in 
               another function however
    Inputs - 
        device_int - object - combined database and snmp gathered information
        device_ip - string - ip address of host with high utilization
        community - string - community string needed for SNMP
        re_tries - int - number of re-tries so far
    returns - 
        bool - state of if the util is above the threshold 
        object - device_int - combined database and snmp gathered information
    """
    print "sleeping for some time"
    time.sleep(interval)

    # Sleep for 60s to then poll for a new data point
    device_int["previous_counter"] = device_int["current_counter"]
    int_traffic = snmppoll(
        "GET",
        ".1.3.6.1.2.1.31.1.1.1.10.{}".format(device_int["oid_index"]),
        device_ip,
        community)
    time_now = datetime.now()
    device_int["previous_update"] = device_int["update_time"]
    device_int["update_time"] = time_now
    device_int["current_counter"] = int_traffic.value

    state, device_int = calculate_interface_util(device_int, time_now)
    if not state:
        return False, device_int
    print_polling_traffic_stats(device_int)

    if device_int["util_percentage"] > percentage_threashold:
        print "interface {} on {} is at {}% utilization this above the threashold attemp {}".format(
            device_int["name"],
            device_ip,
            device_int["util_percentage"],
            re_tries)
        return True, device_int

    # Flowed traffic but didn't break threashold
    return False, device_int


def main():
    command = "SELECT * FROM `FYP Data`.device_table;"
    devices = get_data(command)
    for device in devices:
        (device_id, device_ip, vendor,
            community, username, passwd,
            enpass, config_lock, lock_reason, asn) = device
        device_interfaces = Grab_device_interfaces_snmp(device_ip, community)
        if not device_interfaces:
            continue
        device_interfaces = match_db_to_device(device_interfaces, device_id)
        device_interfaces = poll_traffic(device_interfaces, device_ip, community)


if __name__ == "__main__":
    main()
