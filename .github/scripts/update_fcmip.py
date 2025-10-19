#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
合并两个来源的 FCM IP/DOMAIN 列表：
1. fcm-hosts 链接，IPv4 转换成 IP-CIDR,<ip>/32,no-resolve
2. GoogleFCM.list 链接，内容原样保留
生成文件 fcmip.list，带北京时间注释
"""

import os
import re
import requests
from datetime import datetime, timedelta
from ipaddress import IPv4Address

# 来源链接
FCM_HOSTS_URL = os.environ.get(
    "FCM_HOSTS_URL",
    "https://raw.githubusercontent.com/yangFenTuoZi/fcm-hosts/refs/heads/master/hosts"
)
GOOGLE_FCM_URL = os.environ.get(
    "GOOGLE_FCM_URL",
    "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/refs/heads/master/rule/Clash/GoogleFCM/GoogleFCM.list"
)
TARGET_PATH = os.environ.get("TARGET_PATH", "fcmip.list")

_ipv4_re = re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b')

def fetch_raw(url):
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return resp.text

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

def format_fcm_hosts(text):
    """从 fcm-hosts 提取 IP 并格式化"""
    ips = extract_ips(text)
    return [f"IP-CIDR,{ip}/32,no-resolve" for ip in ips]

def format_google_fcm(text):
    """GoogleFCM.list 内容原样保留"""
    lines = []
    for line in text.splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            lines.append(line)
    return lines

def main():
    # 获取 fcm-hosts
    print(f"Fetching from FCM_HOSTS_URL: {FCM_HOSTS_URL}")
    fcm_text = fetch_raw(FCM_HOSTS_URL)
    fcm_lines = format_fcm_hosts(fcm_text)
    print(f"FCM hosts extracted: {len(fcm_lines)} IPs")

    # 获取 GoogleFCM.list
    print(f"Fetching from GOOGLE_FCM_URL: {GOOGLE_FCM_URL}")
    google_text = fetch_raw(GOOGLE_FCM_URL)
    google_lines = format_google_fcm(google_text)
    print(f"Google FCM entries: {len(google_lines)} lines")

    # 时间戳
    now_beijing = datetime.utcnow() + timedelta(hours=8)
    time_str = now_beijing.strftime("%Y-%m-%d %H:%M:%S CST (Beijing Time)")

    content = [
        f"# Auto generated: {time_str}",
        "# Sources:",
        f"# {FCM_HOSTS_URL}",
        f"# {GOOGLE_FCM_URL}",
        ""
    ] + fcm_lines + google_lines

    # 写入文件
    os.makedirs(os.path.dirname(TARGET_PATH) or ".", exist_ok=True)
    tmp = TARGET_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write("\n".join(content) + "\n")
    os.replace(tmp, TARGET_PATH)
    print(f"Wrote {TARGET_PATH}")

if __name__ == "__main__":
    main()
