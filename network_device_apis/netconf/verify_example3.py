#!/usr/bin/env python3
"""
verify_example3.py
Verify the <edit-config> pushed by example3.py using NETCONF only.

Checks:
  1. <get-config> (running datastore)  -> did the config land?   (ietf-interfaces)
  2. <get> operational state           -> is the interface up?   (ietf-interfaces:interfaces-state)
Prints a PASS/FAIL table and exits 0 (all pass) or 1 (any fail).
"""

import sys
import xmltodict
from ncclient import manager
from device_info import ios_xe_sandbox

# --- Expected values: must match what example3.py pushed ---------------------
EXPECTED = {
    "name": "GigabitEthernet2",
    "description": "Configured by NETCONF",
    "enabled": "true",
    "ip": "10.255.255.1",
    "netmask": "255.255.255.0",
}

# --- Subtree filters (XML) -----------------------------------------------------
# Config view: only GigabitEthernet2 under the ietf-interfaces config tree
CONFIG_FILTER = f"""
<filter xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">
    <interface>
      <name>{EXPECTED["name"]}</name>
    </interface>
  </interfaces>
</filter>"""

# Operational view: same interface under interfaces-state (read-only data)
STATE_FILTER = f"""
<filter xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <interfaces-state xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">
    <interface>
      <name>{EXPECTED["name"]}</name>
      <admin-status/>
      <oper-status/>
    </interface>
  </interfaces-state>
</filter>"""


def as_list(x):
    """xmltodict returns a dict for one element, a list for many -> normalise."""
    if x is None:
        return []
    return x if isinstance(x, list) else [x]


def text(x):
    """Leaf values with attributes (e.g. xmlns) come back as {'#text': ...}."""
    if isinstance(x, dict):
        return x.get("#text")
    return x


def main():
    results = []  # rows of (check, expected, actual)

    with manager.connect(host=ios_xe_sandbox["address"],
                         port=ios_xe_sandbox["port"],
                         username=ios_xe_sandbox["username"],
                         password=ios_xe_sandbox["password"],
                         hostkey_verify=False,
                         allow_agent=False,
                         look_for_keys=False) as m:

        # 1) Running config ----------------------------------------------------
        cfg_reply = m.get_config(source="running", filter=CONFIG_FILTER)
        cfg = xmltodict.parse(cfg_reply.xml)["rpc-reply"]["data"]
        intf = (cfg or {}).get("interfaces", {}).get("interface") if cfg else None

        if not intf:
            print(f"FAIL: {EXPECTED['name']} not found in running config")
            sys.exit(1)

        addrs = as_list((intf.get("ipv4") or {}).get("address"))
        ips = {(text(a.get("ip")), text(a.get("netmask"))) for a in addrs}

        results.append(("description", EXPECTED["description"], text(intf.get("description"))))
        results.append(("enabled", EXPECTED["enabled"], text(intf.get("enabled"))))
        results.append(("ipv4 address",
                        f'{EXPECTED["ip"]}/{EXPECTED["netmask"]}',
                        ", ".join(f"{i}/{n}" for i, n in ips) or None))

        # 2) Operational state -------------------------------------------------
        st_reply = m.get(filter=STATE_FILTER)
        st = xmltodict.parse(st_reply.xml)["rpc-reply"]["data"]
        st_intf = (st or {}).get("interfaces-state", {}).get("interface", {}) if st else {}
        results.append(("admin-status", "up", text(st_intf.get("admin-status"))))
        results.append(("oper-status", "up", text(st_intf.get("oper-status"))))

    # --- Report -----------------------------------------------------------------
    print(f"\nVerification of example3.py on {ios_xe_sandbox['address']} ({EXPECTED['name']})")
    print("-" * 102)
    print(f"{'Check':<14}{'Expected':<30}{'Actual':<52}Result")
    print("-" * 102)
    failed = 0
    for check, exp, act in results:
        if check == "ipv4 address":
            ok = act is not None and exp in act
        else:
            ok = exp == act
        failed += not ok
        print(f"{check:<14}{exp:<30}{str(act):<52}{'PASS' if ok else 'FAIL'}")
    print("-" * 102)
    print("ALL CHECKS PASSED" if not failed else f"{failed} CHECK(S) FAILED")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
