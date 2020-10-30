from scapy.all import *
from netmiko import ConnectHandler
import textfsm
from ntc_templates.parse import parse_output
import re
import sys
import getpass

hostname = input("\nEnter IP address: ")
username = input("Enter device username: ")
password = getpass.getpass("Enter device password: ")

def run_trace(hostname):
    for i in range(1, 28):
        pkt = IP(dst=hostname, ttl=i) / UDP(dport=33434)

        # Send the packet and get a reply
        reply = sr1(pkt, verbose=0, timeout=3)
        if reply is None:
            # No reply
            print("\nNext hop did not reply..")    
            break
        elif reply.type == 3:
            # We've reached our destination
            print("Done! Reached", reply.src)
            break
        else:
            # We're in the middle somewhere
            print("Hop %d: " % i , reply.src)
            last_hop = reply.src
        
    return last_hop



def get_lasthop_info(net_connect):

    info = {}
    info["hostname"] = net_connect.find_prompt()[:-1]
    return info



def get_arp(net_connect, hostname):

    command = f"show ip arp {hostname}"
    output = net_connect.send_command(command)

    with open("show_ip_arp_host.textfsm") as f:
        template = textfsm.TextFSM(f)
    fsm_results = template.ParseText(output)

    try:
        interface = fsm_results[0][4]
        mac_address = fsm_results[0][2]
    except:
        print("\nLooks like this host is a network device. Please SSH to it directly")
        sys.exit()

    return interface, mac_address



def get_mac_interface(net_connect, mac_address):

    command = f"show mac address-table address {mac_address}"
    output = net_connect.send_command(command)

    with open("show_mac_address_host.textfsm") as f:
        template = textfsm.TextFSM(f)
    fsm_results = template.ParseText(output)

    mac_interface = fsm_results[0][3]

    return mac_interface



def init_cdp_check(net_connect):

    command = f"sho cdp neighbors {mac_interface} detail "
    output = net_connect.send_command(command)

    with open("show_cdp_detail.textfsm") as f:
        template = textfsm.TextFSM(f)
    cdp_results = template.ParseText(output)

    if "Switch" in cdp_results[0][2]:
        return True, cdp_results[0][1]
    else:
        return False, cdp_results[0][1]


def get_sw_info(cdp_nbr_ip):

    device2 = {
        "device_type": "cisco_ios",
        "host": cdp_nbr_ip,
        "username": username,
        "password": password,
    }

    net_connect2 = ConnectHandler(**device2)

    sw_results = {}
    sw_results["hostname"] = net_connect2.find_prompt()[:-1]

    command = f"show mac address-table address {mac_address}"
    output = net_connect2.send_command(command)

    with open("show_mac_address_host.textfsm") as f:
        template = textfsm.TextFSM(f)
    mac_results = template.ParseText(output)

    mac_interface = mac_results[0][3]

    command = f"sho cdp neighbors {mac_interface} detail "
    output = net_connect2.send_command(command)

    with open("show_cdp_detail.textfsm") as f:
        template = textfsm.TextFSM(f)
    cdp_results = template.ParseText(output)
    return(sw_results, mac_results, cdp_results)



if __name__ == "__main__":

    # get lasthop ip address using traceroute
    last_hop = run_trace(hostname)

    # populate last hop device details
    device = {
        "device_type": "cisco_ios",
        "host": last_hop,
        "username": username,
        "password": password,
    }

    print(f"Logging in to last hop {last_hop}...\n")

    # connect to last_hop device
    net_connect = ConnectHandler(**device)

    # get details of last hop router
    lasthop_info = get_lasthop_info(net_connect)

    # get arp entry from last hop device
    interface, mac_address = get_arp(net_connect, hostname)

    # if endpoint mac is learned on VLAN interface, we need to look it up in MAC Table
    vlan_match = re.search("^Vlan", interface)
    if vlan_match:
        mac_interface = get_mac_interface(net_connect, mac_address)

    # perform initial cdp check to see if downstream neighbor is a switch
    is_switch, cdp_nbr_ip = init_cdp_check(net_connect)

    # set this to true when final switch is reached
    if is_switch:
        print("Lasthop router is connected to switch.")
        print(f"Interrogating {cdp_nbr_ip}...")
        reached_last_switch = False
    else:
        reached_last_switch = True

    # we will populate this list with switch details using cdp
    switch_path = []

    # initialize the cdp neighbor up, this is the last hop to begin
    # cdp_nbr_ip = cdp_nbr_ip

    while reached_last_switch is False:

        # grab cdp details
        try:
            sw_results, mac_results, cdp_results = get_sw_info(cdp_nbr_ip)
        except:
            print("Unable to gather more CDP info.")
            reached_last_switch = True
            # remove last item since its erroneous now
            # switch_path = switch_path[:-1]
            break

        switch = {}
        switch["hostname"] = sw_results['hostname']
        switch["interface"] = mac_results[0][3]
        switch_path.append(switch)

        if "Switch" in cdp_results[0][2]:
            cdp_nbr_ip = cdp_results[0][1]
            print (f"Neighbor is a switch, interrogating {cdp_nbr_ip}...")
        else:
            reached_last_switch = True


    print(f"""
    MAC ADDRESS:                {mac_address}
    LASTHOP ROUTER:             {lasthop_info['hostname']}
    LASTHOP LAYER 3 INTERFACE:  {interface}
    LASTHOP LAYER 2 INTERFACE:  {mac_interface}
    DOWNSTREAM SWITCHES: """)

    for switch in switch_path:
        print(f"\t - {switch['hostname']}\t{switch['interface']}")
    print("\n")
        