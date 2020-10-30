# FIND AN ENDPOINT

## Description

This script attempts to find the last L2 switch and port where a MAC address is located. Along the way it displays L3 hops via traceroute and L2 hops via CDP.

## Usage:
```
python find_endpoint.py

Enter IP address: 
Enter device username: 
Enter device password: 
```

## Example:
```
$ sudo .venv/bin/python find_endpoint.py 

Enter IP address: 172.28.128.121
Enter device username: admin
Enter device password: 
Hop 1:  172.28.87.2
Hop 2:  172.28.6.9
Done! Reached 172.28.128.121
Logging in to last hop 172.28.6.9...

Lasthop router is connected to switch.
Interrogating 172.28.254.10...
Neighbor is a switch, interrogating 172.28.254.32...
Neighbor is a switch, interrogating 172.28.128.121...
Unable to gather more CDP info.

    MAC ADDRESS:                7cad.4f07.7980
    LASTHOP ROUTER:             PDX-3850-CORE
    LASTHOP LAYER 3 INTERFACE:  Vlan428
    LASTHOP LAYER 2 INTERFACE:  Gi2/0/24
    DOWNSTREAM SWITCHES: 
         - PDX-3650-STAGING     Gi0/2
         - PDX-3850-02  Gi1/0/13
```