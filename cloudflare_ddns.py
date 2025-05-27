#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
╔══════════════════════════════════════════════╗
║     Cloudflare DDNS Updater - by Kele        ║
║  自动检测公网 IPv4 并更新至 Cloudflare 记录    ║
╚══════════════════════════════════════════════╝
"""

import requests
import json
import sys
import time
import socket
import os
from collections import Counter
from requests.adapters import HTTPAdapter
from urllib3.util import connection

# Cloudflare API 信息
CFUSER = "你的 Cloudflare 账户邮箱"
CFKEY = "你的 Cloudflare API Key"
CFZONE_NAME = "你的域名，例如：example.com"
CFRECORD_NAME = "需要更新的子域名，例如：nas.example.com"
CFTTL = 3600

# IP 获取服务
IP_SERVICES = [
    "https://ifconfig.co/ip",
    "https://api-ipv4.ip.sb/ip",
    "https://ipinfo.io/ip"
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.84 Safari/537.36",
    "Content-Type": "application/json"
}

CF_HEADERS = {
    "X-Auth-Email": CFUSER,
    "X-Auth-Key": CFKEY,
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.84 Safari/537.36",
    "Content-Type": "application/json"
}

# 日志和上次 IP 文件
LOG_FILE = "cf_update.log"
LAST_IP_FILE = "last_ip.txt"

# 强制使用 IPv4
def force_ipv4():
    def allowed_family():
        return socket.AF_INET
    connection.allowed_gai_family = allowed_family

class IPv4Adapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        kwargs["socket_options"] = [(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)]
        super().init_poolmanager(*args, **kwargs)

def log(msg):
    timestamp = time.strftime("[%Y-%m-%d %H:%M:%S]")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{timestamp} {msg}\n")
    print(f"{timestamp} {msg}")

def get_public_ip():
    force_ipv4()
    session = requests.Session()
    session.mount("http://", IPv4Adapter())
    session.mount("https://", IPv4Adapter())

    ip_list = []

    log("尝试从多个服务获取公网 IPv4...")
    for url in IP_SERVICES:
        try:
            resp = session.get(url, headers=HEADERS, timeout=5)
            resp.raise_for_status()
            ip = resp.text.strip()
            log(f"✓ {url} 返回 IP：{ip}")
            ip_list.append(ip)
        except Exception as e:
            log(f"✗ {url} 请求失败：{e}")

    if not ip_list:
        log("❌ 所有 IP 接口均失败")
        sys.exit(1)

    count = Counter(ip_list)
    most_common = count.most_common(1)
    ip, freq = most_common[0]

    if freq >= 2:
        log(f"✅ 确认公网 IP：{ip}（{freq} 个源一致）")
        return ip
    else:
        log(f"❌ 获取结果不一致：{ip_list}")
        sys.exit(1)

def ip_has_changed(new_ip):
    if os.path.exists(LAST_IP_FILE):
        with open(LAST_IP_FILE, "r") as f:
            old_ip = f.read().strip()
        if new_ip == old_ip:
            log("📌 公网 IP 未变化，无需更新 Cloudflare。")
            return False
    with open(LAST_IP_FILE, "w") as f:
        f.write(new_ip)
    return True

def get_zone_id(zone_name):
    url = f"https://api.cloudflare.com/client/v4/zones?name={zone_name}"
    try:
        resp = requests.get(url, headers=CF_HEADERS)
        data = resp.json()
        return data["result"][0]["id"]
    except Exception as e:
        log(f"❌ 获取 Zone ID 失败：{e}")
        sys.exit(1)


def get_record_id(zone_id, record_name):
    url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records?name={record_name}"
    try:
        resp = requests.get(url, headers=CF_HEADERS)
        data = resp.json()
        return data["result"][0]["id"], data["result"][0]["content"]
    except Exception as e:
        log(f"❌ 获取 Record ID 失败：{e}")
        sys.exit(1)

def update_cloudflare_dns(CFZONE_ID, CFRECORD_ID, ip):
    timestamp = time.strftime("[%Y-%m-%d %H:%M:%S]")
    url = f"https://api.cloudflare.com/client/v4/zones/{CFZONE_ID}/dns_records/{CFRECORD_ID}"
    payload = {
        "type": CFRECORD_TYPE,
        "name": CFRECORD_NAME,
        "content": ip,
        "ttl": CFTTL,
        "proxied": False,
        "comment": f"Updated via script @{timestamp}"
    }

    try:
        response = requests.patch(url, headers=CF_HEADERS, json=payload)
        response.raise_for_status()
        data = response.json()
        if data.get("success"):
            log(f"✅ Cloudflare DNS 更新成功！IP: {ip}")
        else:
            log("❌ Cloudflare 返回失败状态")
            log(json.dumps(data, indent=2))
            sys.exit(1)
    except Exception as e:
        log(f"❌ 请求发送失败: {e}")
        sys.exit(1)

def main():
    log("-------------------------------------------------------")
    log("🚀 启动 Cloudflare 更新脚本")
    ip = get_public_ip()
    zone_id = get_zone_id(CFZONE_NAME)
    record_id, current_ip = get_record_id(zone_id, CFRECORD_NAME)
    if ip_has_changed(ip):
        log(f"🔄 IP 发生变化，新IP：{ip}，准备更新 Cloudflare...")
        update_cloudflare_dns(zone_id, record_id, ip)

if __name__ == "__main__":
    main()
