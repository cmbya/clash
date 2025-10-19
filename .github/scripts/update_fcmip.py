#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动从远程 hosts 文件中提取 IPv4 地址，
格式化为：IP-CIDR,xxx.xxx.xxx.xxx/32,no-resolve
并保存到仓库中的 fcmip.list。
"""

import os
import re
import requests
from datetime import datetime, timedelta
from ipaddress import IPv4Address

SOURCE_URL = os.environ.get(
    "SOURCE_URL",
    "https://raw.githubusercontent.com/yangFenTuoZi/fcm-hosts/refs/heads/master/hosts"
)
TARGET_PATH = os.environ.get("TARGET_PATH", "fcmip.list")

def fetch_raw(url):
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return resp.text

_ipv4_re = re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b')

def valid_ipv4(s):
    try:
        IPv4Address(s)
        return True
    except Exception:
        return False

def extract_ips(text):
    ips = set()
    for m in _ipv4_re.findall(text):
        if valid_ipv4(m):
            ips.add(m)
    return sorted(ips, key=lambda ip: tuple(map(int, ip.split('.'))))

def format_lines(ips):
    # 使用北京时间（UTC+8）
    now_beijing = datetime.utcnow() + timedelta(hours=8)
    time_str = now_beijing.strftime("%Y-%m-%d %H:%M:%S CST (Beijing Time)")
    lines = [
        f"# Auto generated: {time_str}",
        "# Source:",
        f"# {SOURCE_URL}",
        ""
    ]
    # 格式为：IP-CIDR,xxx.xxx.xxx.xxx/32,no-resolve（无短横线）
    lines += [f"IP-CIDR,{ip}/32,no-resolve" for ip in ips]
    return "\n".join(lines) + "\n"

def main():
    print(f"Fetching from {SOURCE_URL}")
    data = fetch_raw(SOURCE_URL)
    ips = extract_ips(data)
    print(f"Found {len(ips)} IPv4 addresses.")
    content = format_lines(ips)
    os.makedirs(os.path.dirname(TARGET_PATH) or ".", exist_ok=True)
    tmp = TARGET_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(content)
    os.replace(tmp, TARGET_PATH)
    print(f"Wrote {TARGET_PATH}")

if __name__ == "__main__":
    main()
