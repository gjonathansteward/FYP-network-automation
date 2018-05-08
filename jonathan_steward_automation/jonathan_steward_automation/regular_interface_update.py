from common_tasks import Grab_device_interfaces_snmp, get_data, set_data_mysql
from SNMPPoll import SnmpPoll as snmppoll
from Classes import ToolLog


def Device_interfaces_update():
    """
    Author - Jonathan Steward
    Function - Workflow function
    Inputs - n/a
    returns -
        int - updates - the number of interface records updated
        int - adds - The number of interface records added
    """
    command = "SELECT * FROM `FYP Data`.device_table;"
    devices = get_data(command)
    updates = 0
    adds = 0
    unreachable = 0
    for device in devices:
        updates, adds, unreachable = process_interfaces(device, updates, adds, unreachable)

    return updates, adds, unreachable
    """
    # uncomment below to enable threading
    for device in devices:
        t = Thread(target=Device_grab_interfaces, args=(device,))
        t.start()
    """


def process_interfaces(device, updates, adds, unreachable):
    """
    Author - Jonathan Steward
    Function - Function to carry out the logic to detect new or update interfaces and add to DB
    Inputs -
        Device - touple - one data record from the database containing device details
        updates - int - Number of updates so far
        adds - int - Number of added interfaces so far
    returns -
        int - updates - the number of interface records updated
        int - adds - The number of interface records added
    """
    print "grabbing details for:\n{}".format(device)
    (device_id, device_ip, vendor,
        community, username, passwd,
        enpass, config_lock, lock_reason, asn) = device
    device_interfaces = grab_device_interfaces(device_ip, community)
    if not device_interfaces:
        unreachable += 1
        return updates, adds, unreachable
    command = "SELECT * FROM `FYP Data`.interfaces where device_id = {}".format(device_id)
    db_interfaces = get_data(command)
    # db_interfaces will be ID/device_id/name/description/ip_address/state/lastupdate/traffic_counter/speed
    for ifindex, device_int in device_interfaces.items():
        # Checking new device interface
        state = "new"
        for interface in db_interfaces:
            # finding matching database interface
            if device_int["name"] == interface[2]:
                # Check state
                if device_int["description"] != interface[3]:
                    state = "update"
                    updates += 1
                    command = update_command(device_int, interface)
                    print "need to update record"
                    break
                if device_int["speed"] != interface[8]:
                    state = "update"
                    updates += 1
                    command = update_command(device_int, interface)
                    print "need to update record"
                    break
                if device_int["ip"] != interface[4]:
                    state = "update"
                    updates += 1
                    command = update_command(device_int, interface)
                    print "need to update record"
                    break
                if device_int["state"] != interface[5]:
                    state = "update"
                    updates += 1
                    command = update_command(device_int, interface)
                    print "need to update record"
                    break
                state = "good"
                # print "interface details the same as the database."
                break
            else:
                continue
        # itterated through all db interfaces
        if state == "new":
            adds += 1
            print "A new interface was detected: {}".format(device_int["name"])
            command = add_command(device_int, device_id)

    return updates, adds, unreachable


def grab_device_interfaces(device_ip, community):
    """
    Author - Jonathan Steward
    Function - Grab details for device interfaces along with stats and set all information into one dictionary
    Inputs -
        device_ip - string - ip address of device
        community - string - community details for snmp
    returns -
        dictionary - device_interfaces - keyed based on oid interface.
    """
    device_interfaces = {}

    interface_name_results = Grab_device_interfaces_snmp(device_ip, community)
    if not interface_name_results:
        return
    interface_descriptions = snmppoll("WALK", ".1.3.6.1.2.1.31.1.1.1.18", device_ip, community)
    if not interface_descriptions:
        return
    interface_ip = snmppoll("WALK", ".1.3.6.1.2.1.4.20.1.2", device_ip, community)
    if not interface_ip:
        return
    interface_state = snmppoll("WALK", ".1.3.6.1.2.1.2.2.1.8", device_ip, community)
    if not interface_state:
        return
    interface_speed = snmppoll("WALK", ".1.3.6.1.2.1.2.2.1.5", device_ip, community)
    if not interface_speed:
        return

    for inter in interface_name_results:
        device_interfaces[inter.oid_index] = {
            "name": inter.value,
            "description": "",
            "ip": "",
            "state": ""
        }
        for desc in interface_descriptions:
            if desc.oid_index == inter.oid_index:
                device_interfaces[inter.oid_index]["description"] = desc.value
                break
        for ip in interface_ip:
            if ip.value == inter.oid_index:
                device_interfaces[inter.oid_index]["ip"] = ip.oid_index
                break
        for speed in interface_speed:
            if speed.oid_index == inter.oid_index:
                device_interfaces[inter.oid_index]["speed"] = int(speed.value)
                break
        for state in interface_state:
            if state.oid_index == inter.oid_index:
                if state.value == "1":
                    state.value = "up"
                else:
                    state.value = "down"
                device_interfaces[inter.oid_index]["state"] = state.value
                break
    return device_interfaces


def update_command(device_int, db_int):
    """
    Author - Jonathan Steward
    Function - updating database with new interface state
    Inputs -
        device_int - dictionary - details of the interface for the state update
        db_int - list - details of the interface from the db, used for the id of the int record
    returns - n/a
    """
    command = """
        UPDATE `FYP Data`.`interfaces`
        SET `description`='{}', `ip_address`='{}', `state`='{}', `speed` ="{}"
        WHERE `interface_id`='{}';""".format(
        device_int["description"],
        device_int["ip"],
        device_int["state"],
        device_int["speed"],
        db_int[0])
    set_data_mysql(command)


def add_command(device_int, device_id):
    """
    Author - Jonathan Steward
    Function - Adds a new interface into the DB
    Inputs -
        device_int - dictionary - details of the interface for the state update
        device_id - int - device_id of the related device for linking in the DB
    returns - n/a
    """
    command = """
    INSERT INTO `FYP Data`.`interfaces`
    (`device_id`,`name`,`description`,`ip_address`,`state`, `speed`)
    VALUES('{}','{}','{}','{}','{}', '{}');""".format(
        device_id,
        device_int["name"],
        device_int["description"],
        device_int["ip"],
        device_int["state"],
        device_int["speed"])

    set_data_mysql(command)


def main():
    toollog = ToolLog("update global interfaces", "")
    updates, adds, unreachable = Device_interfaces_update()
    toollog.set_tool_log(True, "Updated: {} Added: {} Unreachable: {}".format(updates, adds, unreachable))


if __name__ == "__main__":
    main()
