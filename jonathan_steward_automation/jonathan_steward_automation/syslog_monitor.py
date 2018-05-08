# lines 7 - 20, 28 - 48 marcelom, (2012) PySyslog.py Available from gist.github.com/marcelom/421801
# Note there are some personal modifications, specifically the threading.


import syslog_parser
import re
import logging
import SocketServer
from threading import Thread


LOG_FILE = 'logfile.log'
HOST, PORT = "172.17.50.2", 50000  # local interface ip

logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    datefmt='',
    filename=LOG_FILE,
    filemode='a')


def parse(message):
    print "thread started"
    syslog_parser.parse(message)


class SyslogUDPHandler(SocketServer.BaseRequestHandler):

    def handle(self):
        data = bytes.decode(self.request[0].strip())
        socket = self.request[1]
        message = "{}:{}".format(self.client_address[0], data)
        regex = ".*(bgp|BGP|License|license).*"
        message_bgp = re.match(regex, message)
        if message_bgp:
            return
        else:
            #print message
            logging.info(message)
            t = Thread(target=parse, args=(message,))
            t.start()


if __name__ == "__main__":
    try:
        server = SocketServer.UDPServer((HOST, PORT), SyslogUDPHandler)
        server.serve_forever(poll_interval=0.000001)

    except (IOError, SystemExit):
        raise
    except KeyboardInterrupt:
        print ("\nCrtl+C Pressed. Shutting down.")
