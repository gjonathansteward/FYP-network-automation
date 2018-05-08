from jnpr.junos import Device
from jnpr.junos.utils.config import Config
from jnpr.junos.exception import ConnectError
from jnpr.junos.exception import ConfigLoadError
from jnpr.junos.exception import CommitError
from lxml.etree import XMLSyntaxError
import time
from common_tasks import print_error


def Juniper_connect(device_object):
    """
    Author - Jonathan Steward
    Function - Create a connnection to a juniper device
    Inputs - device_object - Device object
    returns - device connection object
    """
    print "{}: connecting".format(time.strftime('%Y-%m-%d %H:%M:%S'))
    try:
        device_con = Device(
            host=device_object.ip,
            user=device_object.username,
            passwd=device_object.password).open()
    except ConnectError as error:
        print_error("{}: there was an issue connecting: {}".format(time.strftime('%Y-%m-%d %H:%M:%S'), error))
        return
    return device_con


def Juniper_config(configuration, device_object, config_format='xml'):
    """
    Author - Jonathan Steward
    Function - use device connection object and connect to load configuration
    Inputs -
        configuration - string of what configuration you want to apply
        device_object - device object containing all the device
        config_format - the format of the configuration, default is xml but can also be set commands
    returns - bool - state of if the config operation worked or not.
    """
    device_con = Juniper_connect(device_object)
    if not device_con:
        return False
    try:
        with Config(device_con, mode='private') as connection:
            print "{}: connected, loading".format(time.strftime('%Y-%m-%d %H:%M:%S'))
            try:
                connection.load(configuration, format=config_format, overwrite=True)
            except ConfigLoadError as error:
                print_error("there was an issue loading configuration:\n{}".format(error))
                return False
            except XMLSyntaxError as error:
                print_error("there was a syntax error:\n{}".format(error))
                return False
            except:
                print_error("Something went wrong".format(error))
                return False

            print "{}: loaded, commiting the following change:".format(time.strftime('%Y-%m-%d %H:%M:%S'))
            diff = connection.pdiff()
            print diff

            try:
                connection.commit(comment='Adding description via api with xml file')
            except CommitError as error:
                print_error("There was an issue with the commit!{}".format(error))
                return False
            print "{}: commit complete".format(time.strftime('%Y-%m-%d %H:%M:%S'))
        device_con.close()
    except:
        print_error("Something went wrong applying config")
    return True

"""
Commented out as used within phase 1
def main():
    device_details = Device_object('192.168.0.2', 'admin', 'cisco12345', '', 'juniper')
    configuration = """
"""
    extra comment block
    <configuration>
        <interfaces>
            <interface>
                <name>ge-0/0/4</name>
                <description>DESCRIPTION SET VIA XML FILE AND SCRIPT at {}</description>
            </interface>
        </interfaces>
    </configuration>
"""
""".format(time.strftime('%Y-%m-%d %H:%M:%S'))
    # configuration = "This shouldn't work"
    state = Juniper_config(configuration, device_details)
    if not state:
        print_error("Issue with Configuring quitting")
        sys.exit()
    print "checking Descriptions VIA SNMP"
    GrabIntToDesc(device_details.ip)


if __name__ == "__main__":
    main()
"""