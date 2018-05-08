import socket
import sys
import time
from threading import Thread 
import threading
import argparse
from common_tasks import set_data_mysql, get_data, SnmpPoll
import logging


LOG_FILE = 'logfile_stress.log'
logging.basicConfig(level=logging.INFO, format='%(message)s', datefmt='', filename=LOG_FILE, filemode='a')


sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
"""
server_address=("172.17.50.2",50000)
message = "blah"
number_of_messages =100
number_of_connections = 50
for _ in range(number_of_messages):
    sock.sendto(message, server_address)


t = Thread(target=function, args=(message,))
t.start()

"""


def setup_steps():
    parser = argparse.ArgumentParser()
    attempts_help = "the amount of attempts to stress test with"
    test_help = "What we are going to test"
    ip_help = "IP used for SNMP stress test"
    parser.add_argument("-a", "--attempts", help=attempts_help, dest="attempts", required=True)
    parser.add_argument("-t", "--test", help=test_help, dest="test", required=True)
    parser.add_argument("-i", "--ip", help=ip_help, dest="ip")
    arguments = parser.parse_args()
    return arguments


def send_syslog_message(message):
    server_address = ("172.17.50.2", 50000)
    print ("=" * 64 + "Sent message {}" + "=" * 64).format(message)
    sock.sendto(message, server_address)


def stress_parsing_syslog(attempts):
    start_time = time.time()

    message = "STRESS TEST MESSAGE NUMBER {}  192.168.0.2:<28>Jan 10 20:37:24 mib2d[960]: SNMP_TRAP_LINK_DOWN: ifIndex 507, ifAdminStatus up(1), ifOperStatus down(2), ifName kjhgvnajieuijfkjdjjkjkdukjhkjhjhjhjvjhkbhajzsdvmbc hjmnadhbfj,ksvcfkvmfxbcnlkdshcbm xnvb ./ljkc kjmnzdsbxc vhkz.xncbv kjz,cbv kz.shmjdnv kjsm"

    messages_sent = 0
    for _ in range(int(attempts)):
        message_to_send = message.format(messages_sent)
        t = Thread(target=send_syslog_message, args=(message_to_send,))
        t.start()
        messages_sent += 1
        time.sleep(0.005)

    end_time = time.time()
    diff = end_time - start_time
    print "Execution took %s seconds" % (diff)


def db_read(attempt):
    get_data("SELECT * FROM `FYP Data`.device_table;")
    logging.info("done read number: {}".format(attempt))
    print "done read number: {}".format(attempt)


def db_write(attempt):
    add_command = """
    INSERT INTO `FYP Data`.`event` (`device_id`, `syslog detail`, `message`, `acted_on`) 
    VALUES ('{}', '192.168.0.2:<28>Jan 10 20:37:24 mib2d[960]: SNMP_TRAP_LINK_DOWN: ifIndex 507, ifAdminStatus up(1), ifOperStatus down(2), ifName kjhgvnajieuijfkjdjjkjkdukjhkjhjhjhjvjhkbhajzsdvmbc hjmnadhbfj,ksvcfkvmfxbcnlkdshcbm xnvb ./ljkc kjmnzdsbxc vhkz.xncbv kjz,cbv kz.shmjdnv kjsm',
    '192.168.0.2:<28>Jan 10 20:37:24 mib2d[960]: SNMP_TRAP_LINK_DOWN: ifIndex 507, ifAdminStatus up(1), ifOperStatus down(2), ifName kjhgvnajieuijfkjdjjkjkdukjhkjhjhjhjvjhkbhajzsdvmbc hjmnadhbfj,ksvcfkvmfxbcnlkdshcbm xnvb ./ljkc kjmnzdsbxc vhkz.xncbv kjz,cbv kz.shmjdnv kjsm',
    '192.168.0.2:<28>Jan 10 20:37:24 mib2d[960]: 2');
    """.format(attempt)
    set_data_mysql(add_command)
    print "done, write number: {}".format(attempt)


def stress_test_db_read(attempts):
    for i in range(int(attempts)):
        """
        threads_number = threading.active_count()
        print threads_number
        if threads_number>120:
            while threads_number>120:
                threads_number = threading.active_count()
                time.sleep(1)
        """
        t = Thread(target=db_read, args=(i,))
        t.start()


def stress_test_db_write(attempts):
    for i in range(int(attempts)):
        t = Thread(target=db_write, args=(i,))
        t.start()


def poll_interfaces(attempt, ip):
    result = SnmpPoll('WALK', '.1.3.6.1.2.1.2.2.1.2', ip, 'public')
    if not result:
        logging.info("attempt {} failed".format(attempt))
    print "done poll number {}".format(attempt)


def stress_test_SNMP(attempts, ip):
    start_time = time.time()
    for i in range(int(attempts)):
        t = Thread(target=poll_interfaces, args=(i, ip,))
        t.start()
        time.sleep(0.002)
    end_time = time.time()
    diff = end_time - start_time
    logging.info("Execution took %s seconds" % (diff))


def main():
    args = setup_steps()
    if args.test == "syslog":
        stress_parsing_syslog(args.attempts)
    if args.test == "dbRead":
        stress_test_db_read(args.attempts)
    if args.test == "dbWrite":
        stress_test_db_write(args.attempts)
    if args.test == "snmp":
        stress_test_SNMP(args.attempts, args.ip)
    print "done test, sleeping for a short time"
    time.sleep(15)


if __name__ == "__main__":
    main()
