# 🌐 Cloudflare DDNS Updater

自动检测公网 IPv4 地址并更新至 Cloudflare DNS 记录的脚本工具。

---

## ✨ 功能特性

- ✅ 自动检测本机公网 IPv4 地址（多源取值，确保一致性）
- 📦 强制使用 IPv4（当系统同时拥有 IPv6 和 IPv4 出口时）
- ⚠️ 当 IP 未变化时，**自动跳过**更新，避免频繁请求
- 🕓 成功更新时：
  - 记录日志到 `cf_update.log`
  - 同步更新时间写入 DNS 记录的 `Comment` 字段

---

## 🔧 使用说明

### 1. 配置项修改

编辑脚本中的以下参数：

```python
CFUSER = "你的 Cloudflare 账户邮箱"
CFKEY = "你的 Cloudflare API Key"
CFZONE_NAME = "你的域名，例如：example.com"
CFRECORD_NAME = "需要更新的子域名，例如：nas.example.com"
