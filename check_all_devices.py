import os
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor

from ospf_status import check_ospf_neighbors
from bgp_status import check_bgp_neighbors
from interface import get_interface_status
from vlan_status import check_vlan_status

load_dotenv()

USERNAME = os.getenv("JHANSI_USERNAME")
PASSWORD = os.getenv("JHANSI_PASSWORD")
SECRET = os.getenv("JHANSI_SECRET")

routers = ["192.168.160.132", "192.168.160.133", "192.168.160.134", "192.168.160.135"]
switches = ["192.168.160.136", "192.168.160.137", "192.168.160.139"]


def check_router(host):
    return {
        "host": host,
        "interface": get_interface_status(host, USERNAME, PASSWORD, SECRET),
        "ospf": check_ospf_neighbors(host, USERNAME, PASSWORD, SECRET),
        "bgp": check_bgp_neighbors(host, USERNAME, PASSWORD, SECRET),
    }


def check_switch(host):
    return {
        "host": host,
        "interface": get_interface_status(host, USERNAME, PASSWORD, SECRET),
        "vlan": check_vlan_status(host, USERNAME, PASSWORD, SECRET),
    }


if __name__ == "__main__":
    with ThreadPoolExecutor() as executor:
        router_results = list(executor.map(check_router, routers))
        switch_results = list(executor.map(check_switch, switches))

    print("\n===== ROUTERS =====")
    for r in router_results:
        print(f"\nHost: {r['host']}")
        print(f"  Interface status: {r['interface']['status']}")
        print(f"  OSPF status: {r['ospf']['status']}")
        print(f"  BGP status: {r['bgp']['status']}")

    print("\n===== SWITCHES =====")
    for s in switch_results:
        print(f"\nHost: {s['host']}")
        print(f"  Interface status: {s['interface']['status']}")
        print(f"  VLAN status: {s['vlan']['status']}")