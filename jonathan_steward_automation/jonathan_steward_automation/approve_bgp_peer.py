from common_tasks import get_data, set_data_mysql, print_error
from Classes import ToolLog
import argparse
import getpass


def setup_steps():
    """
    Author - Jonathan Steward
    Function - Takes in command line arguments
    Inputs - n/a
    returns - argparse object - stores all arguments taken in
    """
    parser = argparse.ArgumentParser()
    peer_help = "Use this to define the peer_id to approve as shown in database"

    parser.add_argument("-p", "--peer_id", help=peer_help, dest="peer", required=True, type=int)

    arguments = parser.parse_args()
    return arguments


def check_peer(peer_id):
    """
    Author - Jonathan Steward
    Function - Check to ensure the peer_id specifed exists
    Inputs - int - peer_id user wants to approve
    returns - Bool - state of the configuration
    """
    command = """
    SELECT * FROM `FYP Data`.BGP_peers WHERE peer_id = {}
    """.format(peer_id)
    data = get_data(command)
    if not data:
        return False
    else:
        return True


def approve_peer(peer_id):
    """
    Author - Jonathan Steward
    Function - Sends MYSQL command to approve the peer requested
    Inputs - int - peer_id requested to be approved
    returns - n/a
    """
    command = """
    UPDATE `FYP Data`.BGP_peers
    SET approved = 1, approver = '{}'
    WHERE peer_id = {}
    """.format(getpass.getuser(), peer_id)
    # print command
    set_data_mysql(command)


def main():
    arguments = setup_steps()
    variables = "peer_id = {}".format(arguments.peer)
    tool_log = ToolLog("approve_bgp_peer", variables)
    state = check_peer(arguments.peer)
    if not state:
        print_error("Peer {} is not in the database".format(arguments.peer))
        tool_log.set_tool_log(False)
        return
    approve_peer(arguments.peer)
    tool_log.set_tool_log(True)
    print_error("Approved BGP Peer_id {}".format(arguments.peer))


if __name__ == "__main__":
    main()
