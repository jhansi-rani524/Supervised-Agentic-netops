# Network Automation Labs

Python scripts that automate the configuration, deployment, and verification of Cisco IOS network devices — built and tested against a multi-router BGP/OSPF lab topology using [Netmiko](https://github.com/ktbyers/netmiko).

Instead of manually console-ing into each router to configure interfaces, BGP neighbors, or OSPF areas, these scripts read a router's config from YAML and push it over SSH, then pull back verification output (`show ip bgp summary`, `show ip ospf neighbor`, etc.) to confirm it actually worked.

<br>

## Architecture

<!--
  Drop your architecture screenshot in a folder like `docs/images/architecture.png`,
  commit it, then point the line below at it. Relative paths work once the image
  is committed to the repo.
-->
![Architecture diagram](docs/images/architecture.png)

<br>

## Skills / Tech Stack

<!--
  Swap these for your own badges, or just paste a screenshot the same way as above:
  ![Skills](docs/images/skills.png)
-->
![Python](https://img.shields.io/badge/Python-3-3776AB?logo=python&logoColor=white)
![Netmiko](https://img.shields.io/badge/Netmiko-SSH%20Automation-informational)
![Cisco IOS](https://img.shields.io/badge/Cisco-IOS-1BA0D7?logo=cisco&logoColor=white)
![BGP](https://img.shields.io/badge/Protocol-BGP-orange)
![OSPF](https://img.shields.io/badge/Protocol-OSPF-orange)
![YAML](https://img.shields.io/badge/Config-YAML-CB171E)

<br>

## Why this exists

Manually configuring routing protocols across a multi-router lab is repetitive and error-prone — the same `interface` / `router bgp` / `neighbor` blocks, typed by hand, on every device. This project treats router configuration as data (YAML) instead of manual CLI steps, so a topology of 4+ routers can be brought up, verified, and torn down consistently and repeatably.

## What's in here

| Script | What it does |
|---|---|
| `bgp_multiple_int.py` | Reads `bgp_multiple_int.yaml`, configures interfaces + BGP (`router bgp`, neighbors) on every router in the file, then pulls `show ip bgp summary` to verify. |
| `bgp_full_log.py` | Same as above, plus structured logging (`bgp_full_log.log`) of every connection, config push, and verification step — with per-router error handling so one failed device doesn't kill the run. |
| `bgp_push.py` | Lighter-weight variant that pushes only BGP neighbor config (no interface config) from `bgp_push.yaml`. |
| `bgp_neighbor_down.py` | Connects to a router, parses `show ip bgp summary`, and reports which BGP neighbors are **not** in an Established state (Idle/Active/Connect) — a quick health check. |
| `ospf_mul.py` | Reads `ospf_mul.yaml`, configures interfaces + OSPF (including auto-calculating the wildcard mask from a subnet mask), then verifies via `show ip ospf neighbor`. |
| `vlan_config.py` | Creates a VLAN, assigns it to an access port, saves the running config, and verifies with `show vlan brief` — across multiple switches. |
| `interface.py` | Minimal example: connect to a device and pull `show ip int brief`. |

Each `*.yaml` file describes one lab topology as data: per-router device type, management IP, interfaces, IP addressing, and routing-protocol parameters (ASN/neighbors for BGP, process ID/router ID/area for OSPF).

## Example: bringing up BGP across 4 routers

```bash
python bgp_full_log.py
```

```
Connecting to the R1
...
--- BGP Summary for R1 ---
Neighbor        V    AS  MsgRcvd  MsgSent  ...  State/PfxRcd
192.168.12.2    4   100      12       14   ...  1

R1 Completed succesfully
```

Every run appends structured entries to `bgp_full_log.log`:

```
2026-06-09 21:03:49,981 - INFO - Authentication (password) successful!
2026-06-09 21:03:50,684 - INFO - R1 - Configuration Apllied Successfully
2026-06-09 21:03:50,792 - INFO - R1 - BGP verification succesfully completed
```

## Getting started

```bash
python -m venv venv
source venv/bin/activate
pip install netmiko pyyaml
```

Edit the relevant `*.yaml` file with your device details (the sample configs use placeholder credentials — do not commit real ones):

```yaml
routers:
  R1:
    device_type: cisco_ios
    host: 192.168.160.132
    username: your_username
    password: your_password_here
    secret: your_password_here
    asn: 100
    interfaces:
      - name: g2/0
        ip: 192.168.12.1
        mask: 255.255.255.0
    neighbors:
      - ip: 192.168.12.2
        remote_as: 100
```

Then run the script for the protocol you want:

```bash
python bgp_multiple_int.py    # BGP + interfaces
python ospf_mul.py            # OSPF + interfaces
python vlan_config.py         # VLAN provisioning
python bgp_neighbor_down.py   # BGP health check
```

> **Security note:** these scripts read credentials from YAML for lab simplicity. For anything beyond a local lab, swap the hardcoded YAML fields for environment variables or a secrets manager before running against real infrastructure.

## Lab environment

Built and tested against Cisco IOS routers/switches in a virtual lab (GNS3/EVE-NG style topology, RFC1918 addressing). Devices connect over SSH via Netmiko's `cisco_ios` driver.

## Stack

- **Python 3**
- **[Netmiko](https://github.com/ktbyers/netmiko)** — SSH connection handling to network devices
- **PyYAML** — topology/config-as-data
- **logging** — structured run logs for auditability

## Roadmap ideas

- Move credentials to environment variables / a `.env` file
- Add pre-checks (ping/reachability) before pushing config
- Extend `bgp_neighbor_down.py` into a standalone monitoring script with alerting
- Add unit tests around the wildcard-mask and BGP-state-parsing logic
