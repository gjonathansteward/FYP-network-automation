import paramiko
# import time
# from SNMPPoll import GrabIntToDesc
# import socket
from common_tasks import print_error
# from Classes import Device_object as Device


def ssh_connection(device):
    """
    Author - Jonathan Steward
    Function - create an SSH connection
    Inputs - device - device object - stores device details for connecting 
    returns - remote_con - paramiko shell object
    """
    remote_con_pre = paramiko.SSHClient()
    remote_con_pre.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        remote_con_pre.connect(
            device.ip,
            username=device.username,
            password=device.password,
            look_for_keys=False,
            allow_agent=False)
    except IOError as error:
        print_error("Can't connect to SSH for following reason:\n{}".format(error))
        return
    except paramiko.PasswordRequiredException as error:
        print_error("Username/Password incorrect")
        return
    except paramiko.AuthenticationException as error:
        print_error("Password/Username incorrect")
        return

    remote_con = remote_con_pre.invoke_shell()
    remote_con.settimeout(10)
    return remote_con


"""
Commented as this script was for phase 1

def set_description(device):

    remote_con = ssh_connection(device)
    if not remote_con:
        return

    print_error("connected to {}".format(device.ip))

    new_desc = "DESCRIPTION SET VIA SCRIPT AT {}".format(time.strftime('%Y-%m-%d %H:%M:%S'))

    if device.vendor == "cisco":
        command = ("\nen\n{}\nconfig t\ninterface s0/0/0\n wrongcommand {} on {}\n".format(
            device.enablePassword,
            new_desc,
            device.vendor))
        remote_con.send(command)
        time.sleep(1)
        output = remote_con.recv(8000)
        if "Invalid input detected" in output:
            print_error("A command used was wrong for {}, please update command given, see error below:".format(device.ip))
            print output
            # Some trigger to log to user that this went wrong
            return

    else:
        enter_configure = ('\nconfigure exclusive\n')
        remote_con.send(enter_configure)
        time.sleep(1)
        print "checking not locked"
        output = remote_con.recv(8000)
        if "configuration database locked" in output:
            print_error("configuration database is locked by someone else:")
            print output
            return
            # Exit because the database is locked and you can't do anything

        command = ('\nset interface fe-0/0/3 wrongcommand "{} on {}"\n').format(
            new_desc,
            device.vendor)
        remote_con.send(command)
        time.sleep(1)

        output = remote_con.recv(8000)
        if 'syntax error' in output:
            print_error("A command used was wrong for {}, please update command given, see error below:".format(device.ip))
            print output
            return

        command = ('\n commit comment "adding description via script"\n')
        remote_con.send(command)
        time.sleep(1)

        complete = False
        attempts = 0
        while not complete or attempts < 10:
            try:
                output = remote_con.recv(8000)
            except socket.timeout:
                print "waiting for commit to complete"
                attempts += 1
                continue

            print output

            if "commit complete" in output:
                complete = True
                device.configured = True
                return
            else:
                time.sleep(0.5)
                print "waiting for commit to complete"
                attempts += 1
        print_error("Something went wrong with committing")
        return
    device.configured = True


def main():
    devices = []
    # Creating array of device objects to store information nicely
    # devices.append(Device('192.168.0.1','admin', 'blah', 'blah', 'blah'))

    devices.append(Device('192.168.0.1', 'admin', 'cisco', 'cisco', 'cisco'))
    devices.append(Device('192.168.0.30', 'admin', 'cisco12345', '', 'juniper'))

    for device in devices:
        set_description(device)

    for device in devices:
        if device.configured:
            GrabIntToDesc(device.ip)


if __name__ == "__main__":
    main()
"""