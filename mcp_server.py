import os
import json
from dotenv import load_dotenv
from mcp.server.mcpserver import MCPServer

from ospf_status import check_ospf_neighbors
from bgp_status import check_bgp_neighbors
from vlan_status import check_vlan_status
from interface import get_interface_status
from remediate import remediate_ospf, remediate_bgp, remediate_vlan

load_dotenv()

USERNAME = os.getenv("JHANSI_USERNAME")
PASSWORD = os.getenv("JHANSI_PASSWORD")
SECRET = os.getenv("JHANSI_SECRET")

ROUTERS = ["192.168.160.132", "192.168.160.133", "192.168.160.134", "192.168.160.135"]
SWITCHES = {
    "192.168.160.136": (10, "Ethernet0/0"),
    "192.168.160.137": (20, "Ethernet0/0"),
    "192.168.160.138": (30, "Ethernet0/0"),
}

LOG_FILE = "network_log.jsonl"
mcp = MCPServer("network-lab")
# The name here is what Claude Desktop will show as the source of these tools.



@mcp.tool()
def check_ospf(host: str) -> dict:
    """Check OSPF neighbor status on one router. Read-only, safe to call anytime.
    host must be one of: 192.168.160.132, .133, .134, .135 (R1-R4)."""
    return check_ospf_neighbors(host, USERNAME, PASSWORD, SECRET)


@mcp.tool()
def check_bgp(host: str) -> dict:
    """Check BGP neighbor status on one router. Read-only, safe to call anytime.
    host must be one of: 192.168.160.132, .133, .134, .135 (R1-R4)."""
    return check_bgp_neighbors(host, USERNAME, PASSWORD, SECRET)


@mcp.tool()
def check_interface(host: str) -> dict:
    """Check interface status on one router or switch. Read-only, safe to call anytime."""
    return get_interface_status(host, USERNAME, PASSWORD, SECRET)


@mcp.tool()
def check_vlan(host: str) -> dict:
    """Check VLAN status on one IOU switch. Read-only, safe to call anytime.
    host must be one of: 192.168.160.136, .137, .138 (the 3 IOU switches)."""
    if host in SWITCHES:
        vlan_id, interface = SWITCHES[host]
        return check_vlan_status(host, USERNAME, PASSWORD, SECRET,
                                  expected_vlan_id=vlan_id, expected_interface=interface)
    return check_vlan_status(host, USERNAME, PASSWORD, SECRET)


@mcp.tool()
def check_all() -> dict:
    """Check interface, OSPF, and BGP status on all 4 routers, and interface and VLAN
    status on all 3 IOU switches. Read-only. Use this for a full health check of the lab."""
    results = {"routers": [], "switches": []}

    for host in ROUTERS:
        results["routers"].append({
            "host": host,
            "interface": check_interface(host)["status"],
            "ospf": check_ospf(host)["status"],
            "bgp": check_bgp(host)["status"],
        })

    for host in SWITCHES:
        results["switches"].append({
            "host": host,
            "interface": check_interface(host)["status"],
            "vlan": check_vlan(host)["status"],
        })

    return results


@mcp.tool()
def read_recent_log(count: int = 20) -> list:
    """Read the most recent entries from the network activity log
    (network_log.jsonl). Use this to answer questions like 'what happened
    yesterday' or 'what has watcher.py detected recently'. count is how many
    of the most recent log lines to return (default 20)."""
    if not os.path.exists(LOG_FILE):
        return []

    with open(LOG_FILE) as f:
        lines = f.readlines()

    recent = lines[-count:] if len(lines) > count else lines
    entries = []
    for line in recent:
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return entries


@mcp.tool()
def fix_ospf(host: str) -> dict:
    """Re-applies OSPF configuration to a router and confirms whether it fixed
    the problem. This makes a REAL change to the router. Only call this after
    the user has explicitly agreed to the fix in the conversation.
    host must be one of: 192.168.160.132, .133, .134, .135 (R1-R4)."""
    return remediate_ospf(host)


@mcp.tool()
def fix_bgp(host: str) -> dict:
    """Re-applies BGP configuration to a router and confirms whether it fixed
    the problem. This makes a REAL change to the router. Only call this after
    the user has explicitly agreed to the fix in the conversation.
    host must be one of: 192.168.160.132, .133, .134, .135 (R1-R4)."""
    return remediate_bgp(host)


@mcp.tool()
def fix_vlan(host: str) -> dict:
    """Re-applies VLAN configuration to an IOU switch and confirms whether it
    fixed the problem. This makes a REAL change to the switch. Only call this
    after the user has explicitly agreed to the fix in the conversation.
    host must be one of: 192.168.160.136, .137, .138 (the 3 IOU switches)."""
    return remediate_vlan(host)


if __name__ == "__main__":
    mcp.run()