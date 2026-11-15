#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import os
import re
import sys
import time
import requests
from datetime import datetime, timezone, timedelta
from pathlib import Path
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# 解决 Windows 控制台输出 Emoji 时报 UnicodeEncodeError (GBK) 的问题
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

DEBUG = False
ACCOUNTS_LOCAL = Path(__file__).with_name("accounts.local.json")
ACCOUNTS_FILE = Path(__file__).with_name("accounts.json")


def redact_email(value):
    return re.sub(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "[邮箱已隐藏]", str(value))


def checkin_outcome(response):
    """Only an explicit server success counts; 'not logged in' is not a repeat."""
    if not isinstance(response, dict) or type(response.get("code")) is not int or response["code"] != 0:
        return "失败"
    return "已签到" if response.get("repeated") is True else "成功"


def write_summary(report):
    summary_path = os.getenv("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as summary:
            summary.write("## GLaDOS 签到结果\n\n```text\n" + redact_email(report).replace("```", "'''") + "\n```\n")

def load_accounts():
    """
    优先从环境变量 GLaDOS_COOKIES_JSON / GLADOS_COOKIES_JSON 读取（Actions/CI）
    本地运行优先读取 accounts.local.json（防泄露），其次 accounts.json
    """
    raw = (os.getenv("GLaDOS_COOKIES_JSON") or os.getenv("GLADOS_COOKIES_JSON") or "").strip()
    if raw:
        try:
            accounts = json.loads(raw)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"GLaDOS_COOKIES_JSON is not valid JSON: {e}") from e
        source = "env:GLaDOS_COOKIES_JSON"
    else:
        target_file = ACCOUNTS_LOCAL if ACCOUNTS_LOCAL.exists() else ACCOUNTS_FILE
        if not target_file.exists():
            raise RuntimeError(
                "Missing accounts source.\n"
                f"- For local: create {ACCOUNTS_LOCAL} or {ACCOUNTS_FILE}\n"
                "- For CI: set env GLaDOS_COOKIES_JSON / GLADOS_COOKIES_JSON"
            )
        try:
            raw = target_file.read_text(encoding="utf-8").strip()
            accounts = json.loads(raw)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"{target_file} is not valid JSON: {e}") from e
        source = f"file:{target_file.name}"

    if not isinstance(accounts, list) or not accounts:
        raise RuntimeError(f"Accounts from {source} must be a non-empty JSON array")

    for idx, a in enumerate(accounts, 1):
        if not isinstance(a, dict):
            raise RuntimeError(f"Account #{idx} must be an object")
        # name 字段可选，未提供时自动命名为 "账号 {idx}"
        if not a.get("name"):
            a["name"] = f"账号 {idx}"
        # 支持整段 cookie 或分开的字段（兼容下划线和冒号）
        has_full_cookie = bool(a.get("cookie"))
        has_koa = bool((a.get("koa_sess") or a.get("koa:sess")) and (a.get("koa_sess_sig") or a.get("koa:sess.sig")))
        has_gld = bool(a.get("gld_sess") or a.get("gld:sess") or a.get("gld_accts") or a.get("gld:accts"))
        if not (has_full_cookie or has_koa or has_gld):
            raise RuntimeError(
                f"Account #{idx} ({a.get('name')}) 缺少 Cookie。\n"
                "可直接提供完整的 'cookie' 字符串，或分别提供 'gld_sess' (或 'gld:sess') 等字段。"
            )

    return accounts, source

def format_traffic(traffic):
    if traffic is None:
        return "未知"
    # 按照从大到小的顺序判断
    if traffic >= 1024 ** 3:
        return f"{traffic / (1024 ** 3):.2f} GB"
    elif traffic >= 1024 ** 2:
        return f"{traffic / (1024 ** 2):.2f} MB"
    elif traffic >= 1024:
        return f"{traffic / 1024:.2f} KB"
    else:
        return f"{traffic} B"

def notify_telegram(title: str, text: str) -> bool:
    token = os.getenv("TG_BOT_TOKEN")
    chat_id = os.getenv("TG_CHAT_ID")
    if not token or not chat_id:
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": f"{title}\n\n{text}",
        "disable_web_page_preview": True,
    }
    try:
        r = requests.post(url, json=payload, timeout=30)
        return r.status_code == 200
    except requests.RequestException:
        return False

def notify_serverchan(title: str, markdown: str) -> bool:
    key = os.getenv("SERVERCHAN_KEY")
    if not key:
        return False
    url = f"https://sctapi.ftqq.com/{key}.send"
    try:
        r = requests.post(url, data={"title": title, "desp": markdown}, timeout=30)
        return r.status_code == 200
    except requests.RequestException:
        return False

def notify(title: str, text: str):
    if notify_telegram(title, text):
        return
    notify_serverchan(title, text)

class GLaDOS:
    def __init__(self):
        self.s = requests.Session()
        self.s.trust_env = True

        retry = Retry(
            total=5,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"],
        )
        adapter = HTTPAdapter(max_retries=retry)
        self.s.mount("https://", adapter)
        self.s.mount("http://", adapter)

        # 对齐浏览器关键头
        self.s.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            "X-Requested-With": "XMLHttpRequest",
            "Origin": "https://glados.cloud",
            "Referer": "https://glados.cloud/console/checkin",
        })

    def set_cookies_from_account(self, acc: dict):
        # 1. 优先使用整段 cookie 字符串
        if acc.get("cookie"):
            raw_cookie = acc["cookie"].strip()
            for part in raw_cookie.split(";"):
                if "=" in part:
                    k, v = part.strip().split("=", 1)
                    self.s.cookies.set(k.strip(), v.strip())
            return

        # 2. 字段式注入（同时兼容带冒号和下划线的字段名）
        mapping = {
            "gld:accts": ["gld:accts", "gld_accts"],
            "gld:accts.sig": ["gld:accts.sig", "gld_accts_sig", "gld:accts_sig"],
            "gld:sess": ["gld:sess", "gld_sess"],
            "gld:sess.sig": ["gld:sess.sig", "gld_sess_sig", "gld:sess_sig"],
            "koa:sess": ["koa:sess", "koa_sess"],
            "koa:sess.sig": ["koa:sess.sig", "koa_sess_sig", "koa:sess_sig"],
        }
        cookies = {}
        for cookie_name, keys in mapping.items():
            for k in keys:
                if acc.get(k):
                    cookies[cookie_name] = acc[k]
                    break

        self.s.cookies.update(cookies)

    def get_status(self):
        url = "https://glados.cloud/api/user/status"
        try:
            r = self.s.get(url, timeout=30)
        except requests.RequestException as e:
            return None, f"网络请求失败: {e}"

        if r.status_code != 200:
            return None, f"HTTP {r.status_code}"

        try:
            data = r.json()
        except Exception:
            return None, "状态接口返回非 JSON 响应"

        if not isinstance(data, dict):
            return None, "状态接口返回了非预期的数据格式"

        if data.get("code") != 0:
            msg = str(data.get("message") or "status error")
            if "没有权限" in msg or data.get("code") == -2:
                msg = f"{msg} (Cookie 已过期或无效，请重新抓取填入 accounts.json)"
            return None, msg

        u = data.get("data")
        if not isinstance(u, dict):
            return None, "状态接口缺少账号数据，请在官网登录检查账号"
        try:
            left_days = int(float(u.get("leftDays", 0)))
        except (TypeError, ValueError, OverflowError):
            return None, "状态接口的剩余天数格式无法识别"
        if DEBUG:
            safe_keys = ["vip", "days", "leftDays", "traffic", "cakeCount", "site", "expired", "system_date"]
            print("调试返回(脱敏)：", json.dumps({k: u.get(k) for k in safe_keys}, ensure_ascii=False, indent=2))

        return {
            "email": u.get("email"),
            "vip": u.get("vip"),
            "leftDays": left_days,
            "days": u.get("days"),
            "traffic": u.get("traffic"),
            "cakeCount": u.get("cakeCount"),
        }, None

    def checkin(self):
        try:
            # 当前官网先获取 nonce，再由浏览器完成 proof 和 Turnstile。
            # requests 不能完成这个流程；不能把缺失验证的 POST 当作可重试错误。
            challenge_response = self.s.get("https://glados.cloud/api/user/checkin/challenge", timeout=30)
            if challenge_response.status_code != 404:
                if challenge_response.status_code != 200:
                    return {"code": -1, "message": f"获取签到验证要求失败：HTTP {challenge_response.status_code}"}
                try:
                    challenge = challenge_response.json()
                except ValueError:
                    return {"code": -1, "message": "签到验证接口返回非 JSON 响应，请使用官网检查登录状态"}
                if not isinstance(challenge, dict) or type(challenge.get("code")) is not int:
                    return {"code": -1, "message": "签到验证接口返回了非预期的数据格式"}
                if challenge["code"] != 0:
                    return {"code": challenge["code"], "message": challenge.get("message") or "无法获取签到验证，请在官网登录检查账号"}
                if challenge.get("nonce") or challenge.get("turnstile"):
                    return {
                        "code": -3,
                        "reason": "browser-required",
                        "message": "网站要求浏览器挑战验证，纯 requests 云端签到不支持。请在本机运行 python browser_checkin.py，或在官网完成签到；刷新 Cookie 不能替代此次验证。",
                    }
                return {"code": -1, "message": "签到验证要求无法识别，请通过官网签到"}

            # 仅兼容没有挑战接口的旧版服务，不尝试伪造或重放验证结果。
            url = "https://glados.cloud/api/user/checkin"
            r = self.s.post(url, json={"token": "glados.cloud"}, timeout=30)
        except requests.RequestException as e:
            return {"code": -1, "message": f"网络请求失败: {e}"}

        if r.status_code != 200:
            return {"code": -1, "message": f"HTTP {r.status_code}"}
        try:
            result = r.json()
            if not isinstance(result, dict):
                return {"code": -1, "message": "签到接口返回了非预期的数据格式"}
            return result
        except Exception:
            return {"code": -1, "message": "签到接口返回非 JSON 响应"}

def main():
    try:
        accounts, source = load_accounts()
    except RuntimeError as error:
        report = "配置错误：" + redact_email(error)
        print(report)
        write_summary(report)
        return 2
    print(f"Loaded {len(accounts)} account(s) from {source}")

    results = []
    for i, acc in enumerate(accounts, 1):
        name = redact_email(acc["name"])
        print(f"\n===== 账号 {i}: {name} =====")

        g = GLaDOS()
        g.set_cookies_from_account(acc)

        st, err = g.get_status()
        if err:
            err = redact_email(err)
            print("❌ 获取状态失败：", err)
            results.append((name, "失败", err, None, None, None))
            continue

        print("账号状态详情：")
        print("  登录状态: 有效（邮箱不写入日志）")
        print(f"  VIP等级: {st['vip']}")
        print(f"  剩余天数: {st['leftDays']}")
        print(f"  已用流量: {format_traffic(st.get('traffic'))}")
        print(f"  Cake数: {st.get('cakeCount', 0)}")

        res = g.checkin()
        msg = redact_email(res.get("message", "Unknown"))
        points_today = res.get("points")

        outcome = checkin_outcome(res)
        display_name = name

        if outcome == "成功":
            print(f"✅ 签到成功：{msg}，获得点数：{points_today}")
            results.append((display_name, "成功", msg, points_today, st["leftDays"], st.get("traffic")))
        elif outcome == "已签到":
            print("ℹ️ 今日已签到：", msg)
            results.append((display_name, "已签到", msg, points_today, st["leftDays"], st.get("traffic")))
        else:
            print("❌ 签到失败：", msg)
            results.append((display_name, "失败", msg, points_today, st["leftDays"], st.get("traffic")))

        time.sleep(2)

    ok = sum(1 for _, st, *_ in results if st in ("成功", "已签到"))
    total = len(results)

    # CI 用 SGT，本地也不影响
    now_sgt = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S (SGT)")
    report = f"时间：{now_sgt}\n结果：{ok}/{total}\n\n"
    for name, st, msg, points_today, leftDays, traffic in results:
        icon = "✅" if st == "成功" else ("ℹ️" if st == "已签到" else "❌")
        report += f"{icon} {name}：{st} - {msg}"
        if points_today is not None:
            report += f" (今日点数: {points_today})"
        report += f" (剩余天数: {leftDays})"
        if traffic is not None:
            report += f" (已用流量: {format_traffic(traffic)})"
        report += "\n"

    print("\n--- 汇总 ---\n" + report)
    write_summary(report)
    notify("GLaDOS 签到报告", report)
    return 0 if ok == total else 1

if __name__ == "__main__":
    sys.exit(main())
