# Supervised Agentic NetOps

A Cisco lab that fixes itself — but only when you say so.

This project automates a 4-router / 3-switch GNS3 lab (OSPF, BGP, VLANs) over SSH, watches it continuously for problems, and can repair them automatically. On top of that sits an MCP server, so instead of running scripts by hand you can just ask Claude Desktop: "is everything up?", "why does R1 keep dropping OSPF?", "go fix it."

# Why "supervised"

An agent that can both see problems and change device config is powerful — and a little dangerous if it acts on its own. So the two are kept deliberately separate:

Looking is always allowed. Checking interfaces, OSPF, BGP, or VLAN status never touches a device's config, so the agent (or you) can check as often as it wants.
Fixing needs a yes. Every fix tool is wired up so the agent only re-applies config after you've actually asked it to — it won't quietly "fix" things in the background while it's just answering a status question.
Fixes are rate-limited. A device that's allow-listed can only be auto-remediated a few times before the script gives up and says "this needs a human," so a flapping link can't turn into an infinite retry loop.

The screenshots further down show this in practice — the agent noticing a repeat failure and stopping to ask instead of patching it again.

#Architecture
<img width="441" height="417" alt="image" src="https://github.com/user-attachments/assets/5f741a6e-44a4-4b14-9f46-8694f73adc34" />
Config lives as data in the *_inventory.yaml files. The push scripts read it and configure the lab. Status checks read the devices back — read-only, safe to run constantly — and every result lands in network_log.jsonl and feeds mcp_server.py. Claude Desktop can call any check_* tool freely, but a fix_* tool only runs through remediate.py, and only once you've actually said to go ahead. watcher.py runs the same status checks

# Lab Topology
<img width="957" height="491" alt="image" src="https://github.com/user-attachments/assets/a782cb25-61e3-4bfb-a7e3-a9642e66e4cf" />
How it works
Layer	Files	What it does
Push	ospf_push.py, bgp_push.py, vlan_push.py	Reads a *_inventory.yaml file and pushes interface + OSPF/BGP/VLAN config to every device in it. ospf_push.py works out the OSPF wildcard mask for you from the subnet mask. vlan_push.py asks for a yes/no before touching each switch.
Status	interface.py, ospf_status.py, bgp_status.py, vlan_status.py	Connects to one device, runs a show command, and reports back ok, down, no_neighbors, or error. Read-only — safe to call constantly. Every result gets logged.
Watch	watcher.py, check_all_devices.py	check_all_devices.py checks every device at once for a snapshot. watcher.py runs the same checks on a loop (interfaces every 15s, OSPF every 50s, BGP every 100s) and only raises a PROBLEM_CONFIRMED after two bad readings in a row — so one slow response doesn't trigger a false alarm.
Remediate	remediate.py	Re-pushes known-good config to a specific device, then re-checks to confirm it actually worked. Locked down to an allow-list of devices, capped at 3 attempts, and won't retry the same device+problem within 5 minutes.
Agent	mcp_server.py	Wraps all of the above as MCP tools — check_ospf, check_bgp, check_vlan, check_interface, check_all, read_recent_log are free to call anytime; fix_ospf, fix_bgp, fix_vlan are documented as "only call after the user has explicitly agreed" so the agent asks first.

logger.py is the thread running under everything — every check and every remediation attempt gets appended as one JSON line to network_log.jsonl, which the agent can also read back to answer "what's happened recently."

# Tested in Claude Desktop
<img width="1600" height="938" alt="image" src="https://github.com/user-attachments/assets/89b80a5a-80d1-4ff7-9819-d56a888c3620" />

Connected to the MCP server and asked it to check the lab. It calls check_all, and gives back a real status table:

A little later, I intentionally broke OSPF on R1 from the CLI and asked again. The agent doesn't just report "down" — it notices this is the third time R1's OSPF has dropped in the session, recognizes that's a pattern rather than a one-off, and stops to ask before doing anything:
<img width="896" height="399" alt="image" src="https://github.com/user-attachments/assets/5bced46e-47f7-4b3e-9bd8-36c54a78fc33" />

When I told it to go ahead and fix R1's OSPF, it calls fix_ospf, confirms neighbors are back to FULL, and repeats the same warning — patching the symptom again won't fix a link that keeps flapping:
<img width="900" height="356" alt="image" src="https://github.com/user-attachments/assets/a1bd621a-0cf7-407c-ba3d-8e6c81f3a8f5" />

# Getting started
bash
python -m venv venv
source venv/bin/activate
pip install netmiko pyyaml python-dotenv mcp

Create a .env file (git-ignored, never commit real credentials):

JHANSI_USERNAME=your_username
JHANSI_PASSWORD=your_password
JHANSI_SECRET=your_enable_secret

Point the *_inventory.yaml files at your own lab. Example (ospf_inventory.yaml):

yaml
routers:
  R1:
    device_type: cisco_ios
    host: 192.168.160.132
    process_id: 110
    router_id: 1.1.1.1
    interfaces:
      - name: g2/0
        ip: 192.168.12.1
        mask: 255.255.255.0
        area: 0
Usage
bash
# Push config
python ospf_push.py           # OSPF + interfaces
python bgp_push.py            # BGP + interfaces
python vlan_push.py           # VLANs, confirms per switch

# One-shot health check
python check_all_devices.py

# Continuous monitoring
python watcher.py

# Start the MCP server so Claude Desktop (or any MCP client) can use it
python mcp_server.py
Point Claude Desktop at mcp_server.py as a local MCP server, then just ask it things like "are all my devices up?" or "fix R1's OSPF.

# Security note

Credentials load from .env via python-dotenv and are never hardcoded in the YAML; .env is git-ignored. This is still built for an isolated lab, though — before running anything like it against real infrastructure, move device inventories out of plaintext YAML and into a proper secrets manager, and add a reachability check before any push.

# Roadmap ideas
Reachability pre-check before every config push
Slack/webhook alerting from watcher.py on PROBLEM_CONFIRMED
Root-cause diagnostics for repeat failures (the agent already flags them — teach remediate.py to investigate, not just re-push)
Unit tests around the OSPF wildcard-mask math and BGP-state parsing



on a loop in the background and only raises an alert once a problem shows up twice in a row.

