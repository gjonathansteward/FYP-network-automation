import unittest

from jonathan_steward_automation import int_down

from jonathan_steward_automation import syslog_parser


class TestingIpParsing(unittest.TestCase):

    def test_IP_Parse_normal_cisco(self):
        # Test a normal message being parsed
        message = "172.17.50.5:<187>539: *Mar  9 14:59:17.678: %LINK-3-UPDOWN: Interface FastEthernet0/18, changed state to down"
        expected_ip = "172.17.50.5"
        self.assertEqual(syslog_parser.identify_ip(message), expected_ip)

    def test_IP_Parse_normal_juniper(self):
        # Test a normal message being parsed
        message = "192.168.0.2:<28>Jan 10 20:37:24 mib2d[960]: SNMP_TRAP_LINK_DOWN: ifIndex 507, ifAdminStatus up(1), ifOperStatus down(2), ifName ge-0/0/11"
        expected_ip = "192.168.0.2"
        self.assertEqual(syslog_parser.identify_ip(message), expected_ip)

    def test_IP_Parse_only_ip(self):
        # Test Just the IP being parsed
        message = "192.168.0.1"
        expected_ip = "192.168.0.1"
        self.assertEqual(syslog_parser.identify_ip(message), expected_ip)

    def test_IP_Parse_no_ip(self):
        # Test for no ip in a valid message
        message = "Jan 10 20:37:24 mib2d[960]: SNMP_TRAP_LINK_DOWN: ifIndex 507, ifAdminStatus up(1), ifOperStatus down(2), ifName ge-0/0/11"
        expected_ip = ""
        self.assertEqual(syslog_parser.identify_ip(message), expected_ip)

    def test_IP_Parse_chars_in_ip(self):
        # This should never happen but still good to test to see if the ip address is replaced with a host name for example
        message = "hi mum:<28>Jan 10 20:37:24 mib2d[960]: SNMP_TRAP_LINK_DOWN: ifIndex 507, ifAdminStatus up(1), ifOperStatus down(2), ifName ge-0/0/11"
        expected_ip = ""
        self.assertEqual(syslog_parser.identify_ip(message), expected_ip)

    def test_IP_Parse_High_ip_values(self):
        # This should never happen but still good to test just in case something goes wrong with a syslog message and gets slightly corrupted or something similar
        message = "500.20.300.1:<28>Jan 10 20:37:24 mib2d[960]: SNMP_TRAP_LINK_DOWN: ifIndex 507, ifAdminStatus up(1), ifOperStatus down(2), ifName ge-0/0/11"
        expected_ip = ""
        self.assertEqual(syslog_parser.identify_ip(message), expected_ip)


class TestingMessageParsing(unittest.TestCase):

    # Cisco Tests

    def test_message_parsing_normal_cisco_ethernet_down(self):
        # Test to ensure the state and name is picked up from a normal down message
        message = "172.17.50.5:<187>539: *Mar  9 14:59:17.678: %LINK-3-UPDOWN: Interface Ethernet0/18, changed state to down"
        expected_int = "Ethernet0/18"
        state = True
        self.assertEqual(int_down.int_down_check(message), (state, expected_int))

    def test_message_parsing_normal_cisco_fa_down(self):
        # Test to ensure the state and name is picked up from a normal down message
        message = "172.17.50.5:<187>539: *Mar  9 14:59:17.678: %LINK-3-UPDOWN: Interface FastEthernet0/18, changed state to down"
        expected_int = "FastEthernet0/18"
        state = True
        self.assertEqual(int_down.int_down_check(message), (state, expected_int))

    def test_message_parsing_normal_cisco_gig_down(self):
        # Test to ensure the state and name is picked up from a normal down message
        message = "172.17.50.5:<187>539: *Mar  9 14:59:17.678: %LINK-3-UPDOWN: Interface GigabitEthernet0/18, changed state to down"
        expected_int = "GigabitEthernet0/18"
        state = True
        self.assertEqual(int_down.int_down_check(message), (state, expected_int))

    def test_message_parsing_normal_cisco_tengige_down(self):
        # Test to ensure the state and name is picked up from a normal down message
        message = "172.17.50.5:<187>539: *Mar  9 14:59:17.678: %LINK-3-UPDOWN: Interface TenGigE0/18, changed state to down"
        expected_int = "TenGigE0/18"
        state = True
        self.assertEqual(int_down.int_down_check(message), (state, expected_int))

    def test_message_parsing_normal_cisco_ethernet_up(self):
        # Test to ensure the state and name is picked up from a normal up message, this shouldn't trigger
        message = "172.17.50.5:<187>539: *Mar  9 14:59:17.678: %LINK-3-UPDOWN: Interface Ethernet0/18, changed state to up"
        expected_int = ""
        state = False
        self.assertEqual(int_down.int_down_check(message), (state, expected_int))

    def test_message_parsing_normal_cisco_fa_up(self):
        # Test to ensure the state and name is picked up from a normal up message, this shouldn't trigger
        message = "172.17.50.5:<187>539: *Mar  9 14:59:17.678: %LINK-3-UPDOWN: Interface FastEthernet0/18, changed state to up"
        expected_int = ""
        state = False
        self.assertEqual(int_down.int_down_check(message), (state, expected_int))

    def test_message_parsing_normal_cisco_gig_up(self):
        # Test to ensure the state and name is picked up from a normal up message, this shouldn't trigger
        message = "172.17.50.5:<187>539: *Mar  9 14:59:17.678: %LINK-3-UPDOWN: Interface GigabitEthernet0/18, changed state to up"
        expected_int = ""
        state = False
        self.assertEqual(int_down.int_down_check(message), (state, expected_int))

    def test_message_parsing_normal_cisco_tengige_up(self):
        # Test to ensure the state and name is picked up from a normal up message, this shouldn't trigger
        message = "172.17.50.5:<187>539: *Mar  9 14:59:17.678: %LINK-3-UPDOWN: Interface TenGigE0/18, changed state to up"
        expected_int = ""
        state = False
        self.assertEqual(int_down.int_down_check(message), (state, expected_int))

    # Juniper Tests

    def test_message_parsing_normal_juniper_fe_down(self):
        # Test to ensure the state and name is picked up from a normal down message
        message = "192.168.0.2:<28>Jan 10 20:37:24 mib2d[960]: SNMP_TRAP_LINK_DOWN: ifIndex 507, ifAdminStatus up(1), ifOperStatus down(2), ifName fe-0/0/11"
        expected_int = "fe-0/0/11"
        state = True
        self.assertEqual(int_down.int_down_check(message), (state, expected_int))

    def test_message_parsing_normal_juniper_ge_down(self):
        # Test to ensure the state and name is picked up from a normal down message
        message = "192.168.0.2:<28>Jan 10 20:37:24 mib2d[960]: SNMP_TRAP_LINK_DOWN: ifIndex 507, ifAdminStatus up(1), ifOperStatus down(2), ifName ge-0/0/11"
        expected_int = "ge-0/0/11"
        state = True
        self.assertEqual(int_down.int_down_check(message), (state, expected_int))

    def test_message_parsing_normal_juniper_xe_down(self):
        # Test to ensure the state and name is picked up from a normal down message
        message = "192.168.0.2:<28>Jan 10 20:37:24 mib2d[960]: SNMP_TRAP_LINK_DOWN: ifIndex 507, ifAdminStatus up(1), ifOperStatus down(2), ifName xe-0/0/11"
        expected_int = "xe-0/0/11"
        state = True
        self.assertEqual(int_down.int_down_check(message), (state, expected_int))

    def test_message_parsing_normal_juniper_et_down(self):
        # Test to ensure the state and name is picked up from a normal down message
        message = "192.168.0.2:<28>Jan 10 20:37:24 mib2d[960]: SNMP_TRAP_LINK_DOWN: ifIndex 507, ifAdminStatus up(1), ifOperStatus down(2), ifName et-0/0/11"
        expected_int = "et-0/0/11"
        state = True
        self.assertEqual(int_down.int_down_check(message), (state, expected_int))

    # No need to check for parsing on up status because juniper doesn't send messages when it goes up.
    # Checking now for the interface number specifically, no need to check both juniper and cisco as they search for the interface in the same way.

    def test_message_parsing_large_interface_numbers(self):
        # Test to ensure a rediculus amount of numbers in the interface is still valid.
        # This level is never going to exist but to future proof it, it is best to do this.
        message = "192.168.0.2:<28>Jan 10 20:37:24 mib2d[960]: SNMP_TRAP_LINK_DOWN: ifIndex 507, ifAdminStatus up(1), ifOperStatus down(2), ifName et-967365874563760/987435987398794387589/119873453548743954387539847598"
        expected_int = "et-967365874563760/987435987398794387589/119873453548743954387539847598"
        state = True
        self.assertEqual(int_down.int_down_check(message), (state, expected_int))

    def test_message_parsing_only_one_int_number(self):
        # Test only one interface number as some cisco devices can do this
        message = "192.168.0.2:<28>Jan 10 20:37:24 mib2d[960]: SNMP_TRAP_LINK_DOWN: ifIndex 507, ifAdminStatus up(1), ifOperStatus down(2), ifName et-0"
        expected_int = "et-0"
        state = True
        self.assertEqual(int_down.int_down_check(message), (state, expected_int))

    def test_message_parsing_only_two_int_numbers(self):
        # Testing for two interface numbers as some cisco devices do this.
        message = "192.168.0.2:<28>Jan 10 20:37:24 mib2d[960]: SNMP_TRAP_LINK_DOWN: ifIndex 507, ifAdminStatus up(1), ifOperStatus down(2), ifName et-0/0"
        expected_int = "et-0/0"
        state = True
        self.assertEqual(int_down.int_down_check(message), (state, expected_int))

    def test_message_parsing_only_four_int_numbers(self):
        # Testing for more than 3 interface numbers as this might one day be a possibility
        message = "192.168.0.2:<28>Jan 10 20:37:24 mib2d[960]: SNMP_TRAP_LINK_DOWN: ifIndex 507, ifAdminStatus up(1), ifOperStatus down(2), ifName et-0/0/0/0"
        expected_int = "et-0/0/0/0"
        state = True
        self.assertEqual(int_down.int_down_check(message), (state, expected_int))

    def test_message_parsing_ae_int(self):
        # Don't want to automate on anything other than physical
        message = "192.168.0.2:<28>Jan 10 20:37:24 mib2d[960]: SNMP_TRAP_LINK_DOWN: ifIndex 507, ifAdminStatus up(1), ifOperStatus down(2), ifName ae1"
        expected_int = ""
        state = False
        self.assertEqual(int_down.int_down_check(message), (state, expected_int))

    def test_message_parsing_vlan_int(self):
        # Don't want to automate on anything other than physical
        message = "192.168.0.2:<28>Jan 10 20:37:24 mib2d[960]: SNMP_TRAP_LINK_DOWN: ifIndex 507, ifAdminStatus up(1), ifOperStatus down(2), ifName vlan1"
        expected_int = ""
        state = False
        self.assertEqual(int_down.int_down_check(message), (state, expected_int))


if __name__ == '__main__':
    unittest.main()
