# STARK INDUSTRIES DYNAMICALLY SYNTHESIZED SKILL
# Created: 2026-11-01 15:33:35
# Purpose: Lists all active network adapters with their IP addresses.

import sys, os
if hasattr(sys.stdout, 'reconfigure'):
    try: sys.stdout.reconfigure(encoding='utf-8')
    except Exception: pass

import psutil
import socket

def list_active_network_adapters():
    """Lists all active network adapters with their IP addresses."""
    print("Active Network Adapters:")
    found_active = False
    
    net_stats = psutil.net_if_stats()
    net_addrs = psutil.net_if_addrs()

    for interface_name, stats in net_stats.items():
        # Consider an adapter 'active' if it's up and has a non-zero speed (indicating connection/activity)
        if stats.isup and stats.speed > 0:
            addresses = net_addrs.get(interface_name, [])
            ip_addresses = []
            for addr in addresses:
                if addr.family == socket.AF_INET: # IPv4
                    ip_addresses.append(f"IPv4: {addr.address} (Netmask: {addr.netmask})")
                elif addr.family == socket.AF_INET6: # IPv6
                    ip_addresses.append(f"IPv6: {addr.address}")
            
            if ip_addresses: # Only print if there are actual IP addresses assigned
                print(f"  Interface: {interface_name}")
                for ip in ip_addresses:
                    print(f"    - {ip}")
                found_active = True
    
    if not found_active:
        print("  No active network adapters found with assigned IP addresses.")

list_active_network_adapters()