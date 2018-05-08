from easysnmp import Session
from easysnmp import exceptions as SNMPexceptions


def SnmpPoll(type, OID, host, community):
    """
    Author - Jonathan Steward
    Function - Polls for Snmp Information based on the type and the OID provided.
    Inputs -
        type - string
        oid - string
        host - string
        community - string
    returns -
        list - results of the SNMP operation, if can't connect returns False
    """
    attemps = 0
    while attemps < 3:
        try:
            session = Session(hostname=host, community=community, version=2)
            if type == "GET":
                try:
                    result = session.get(OID)
                    return result
                except SNMPexceptions.EasySNMPTimeoutError as error:
                    print "couldn't connect to {} to poll for SNMP for some reason: {}".format(host, error)
                    attemps += 1

            if type == "WALK":
                try:
                    result = session.walk(OID)
                    return result
                except SNMPexceptions.EasySNMPTimeoutError as error:
                    print "couldn't connect to {} to poll for SNMP for some reason: {}".format(host, error)
                    attemps += 1
        except:
            print "something didn't work, re-trying"
            attemps += 1

"""
Commented because this script was for phase 1 and isn't used any more
def main():
    hosts = ["192.168.0.1"]
    community = "public"
    for host in hosts:
        GrabIntToDesc(host, community)


def GrabIntToDesc(host, community):
    InterfaceNameOID = '.1.3.6.1.2.1.2.2.1.2'  # OID for int names
    InterfaceDescOID = '.1.3.6.1.2.1.31.1.1.1.18'  # OID of int descriptions as configured
    # print ("searching for the value related to OID %s"%(OID))
    IntNames = SnmpPoll("WALK", InterfaceNameOID, host, community)
    if not IntNames:
        return
    IntDesc = SnmpPoll("WALK", InterfaceDescOID, host, community)
    if not IntDesc:
        return

    IntDetails = []

    descriptions = 0
    for index, interface in enumerate(IntNames):
        if not IntDesc[index].value:
            continue
        descriptions += 1
        intdetail = '{} {}'.format(interface.value, IntDesc[index].value)
        IntDetails.append(intdetail)

    if not descriptions:
        print "no interface descriptions set"
    else:
        print "\ninterfaces for {} host\nName\t|\tDescription".format(host)
        for int in IntDetails:
            print int


if __name__ == "__main__":
    main()

"""