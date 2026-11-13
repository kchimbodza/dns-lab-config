#!/usr/bin/env python3
"""Check that the forward and reverse zones agree, without running BIND.

Every A record must have a PTR pointing back to the same name, every PTR must have
a matching A record, and both zones must use the same SOA serial.
Usage: python3 scripts/check_zones.py   (Python 3 standard library only)
"""
import pathlib
import re
import sys

ZONES = pathlib.Path(__file__).resolve().parent.parent / "config" / "zones"
FORWARD, FWD_ORIGIN = ZONES / "lab.myviewsontech.local.zone", "lab.myviewsontech.local."
REVERSE, REV_ORIGIN = ZONES / "reverse.zone", "10.168.192.in-addr.arpa."


def records(path, rtype):
    out = {}
    for line in path.read_text().splitlines():
        parts = line.split(";")[0].split()
        if len(parts) >= 3 and parts[-2] == rtype:
            out[parts[0]] = parts[-1]
    return out


def serial(path):
    return re.search(r"(\d+)\s*;\s*Serial", path.read_text()).group(1)


def fqdn(name, origin):
    return name if name.endswith(".") else f"{name}.{origin}"


a = {fqdn(n, FWD_ORIGIN): ip for n, ip in records(FORWARD, "A").items()}
ptr = {f"192.168.10.{n}": target for n, target in records(REVERSE, "PTR").items()}
problems = []

for name, ip in sorted(a.items(), key=lambda x: x[1]):
    back = ptr.get(ip)
    ok = back == name
    print(f"{'OK  ' if ok else 'FAIL'} {name:<36} A {ip:<14} PTR -> {back}")
    if not ok:
        problems.append(f"{name} has no matching PTR")
for ip, target in ptr.items():
    if a.get(target) != ip:
        problems.append(f"PTR {ip} -> {target} has no matching A record")
if serial(FORWARD) != serial(REVERSE):
    problems.append("SOA serials differ")
else:
    print(f"OK   both zones use SOA serial {serial(FORWARD)}")

for p in problems:
    print("FAIL", p)
print(f"\n{len(a)} A records, {len(ptr)} PTR records, {len(problems)} problem(s)")
sys.exit(1 if problems or not a else 0)
