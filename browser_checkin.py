#!/usr/bin/env python3
"""Run the site's own check-in page in a visible, dedicated browser profile.

Login and interactive human verification are completed by the user in the page.
This module does not generate, extract, store or replay challenge tokens.
"""
import argparse
from pathlib import Path
import re
import sys
from urllib.parse import urlparse

from checkin import checkin_outcome, redact_email, write_summary

CHECKIN_URL = "https://glados.cloud/console/checkin"
STATUS_URL = "https://glados.cloud/api/user/status"


def is_checkin_response(response):
    url = urlparse(response.url)
    return (url.scheme == "https" and url.netloc == "glados.cloud"
            and url.path == "/api/user/checkin" and response.request.method == "POST")


def checkin_in_page(page, timeout_ms):
    """Use only the ordinary first-party button; never interact with CAPTCHA frames."""
    button = page.get_by_role("button", name=re.compile(r"^(Checkin|Check in|签到|立即签到)$", re.I))
    button.wait_for(state="visible", timeout=timeout_ms)
    print("正在通过官网签到。若出现人机验证，请本人在浏览器中完成。")
    with page.expect_response(is_checkin_response, timeout=timeout_ms) as pending:
        button.click(timeout=timeout_ms)
    response = pending.value
    if response.status != 200:
        return {"code": -1, "message": f"签到接口返回 HTTP {response.status}"}
    try:
        result = response.json()
    except ValueError:
        return {"code": -1, "message": "签到接口返回非 JSON 响应"}
    if not isinstance(result, dict):
        return {"code": -1, "message": "签到接口返回了非预期的数据格式"}
    return {key: result.get(key) for key in ("code", "message", "repeated", "points", "reason")}


def main(argv=None):
    parser = argparse.ArgumentParser(description="通过官网正常页面签到；需要时由本人登录或完成验证")
    parser.add_argument("--profile", type=Path, default=Path(__file__).with_name(".browser-profile"),
                        help="专用浏览器资料目录；不要使用日常浏览器的资料目录")
    parser.add_argument("--channel", choices=("msedge", "chrome", "chromium"), default="msedge")
    parser.add_argument("--login", action="store_true", help="打开官网后等待本人登录，再开始签到")
    parser.add_argument("--keep-open", action="store_true", help="结束后等待按回车再关闭浏览器，便于检查页面")
    parser.add_argument("--timeout", type=int, default=180, help="等待页面及签到结果的最长秒数（默认 180）")
    args = parser.parse_args(argv)
    if args.timeout <= 0:
        parser.error("--timeout 必须大于 0")
    try:
        from playwright.sync_api import sync_playwright, Error, TimeoutError
    except ImportError:
        print("缺少浏览器依赖。请运行：python -m pip install -r requirements-browser.txt")
        return 2

    try:
        with sync_playwright() as playwright:
            options = {"headless": False}
            if args.channel != "chromium":
                options["channel"] = args.channel
            context = playwright.chromium.launch_persistent_context(str(args.profile.resolve()), **options)
            try:
                page = context.new_page()
                page.goto(CHECKIN_URL, wait_until="domcontentloaded", timeout=args.timeout * 1000)
                if args.login:
                    input("请在浏览器里亲自登录并完成账号引导，完成后在此按回车。密码、验证码无需输入终端：")
                    page.goto(CHECKIN_URL, wait_until="domcontentloaded", timeout=args.timeout * 1000)
                status = context.request.get(STATUS_URL, timeout=30000)
                try:
                    user_status = status.json() if status.status == 200 else None
                except ValueError:
                    user_status = None
                if not isinstance(user_status, dict) or type(user_status.get("code")) is not int or user_status["code"] != 0:
                    print("登录状态未就绪。请用 --login 重新运行，在官网亲自登录并完成账号引导。")
                    return 2

                try:
                    result = checkin_in_page(page, args.timeout * 1000)
                    outcome = checkin_outcome(result)
                    report = f"官网浏览器签到：{outcome}\n{redact_email(result.get('message') or '未返回说明')}"
                    if outcome in ("成功", "已签到"):
                        report += f"\n此次返回点数：{result.get('points')}"
                    elif result.get("reason") == "turnstile":
                        report += "\nCloudflare 验证未通过，请检查官网提示及验证资源连接；本次未确认签到。"
                    elif result.get("reason") == "device-mismatch":
                        report += "\n官网要求在当前设备重新登录，请本人操作后再试。"
                    print(report)
                    write_summary(report)
                    return 0 if outcome in ("成功", "已签到") else 1
                except TimeoutError:
                    print("等待官网签到超时，本次没有确认成功。请检查页面是否卡在登录、人机验证或网络错误。")
                    return 1
            finally:
                if args.keep_open:
                    input("可继续查看官网页面；按回车关闭这个专用浏览器：")
                context.close()
    except Error:
        print("无法启动或连接专用浏览器。请关闭使用同一资料目录的窗口，确认所选浏览器已安装，再重试。")
        return 2
    except (EOFError, KeyboardInterrupt):
        print("操作已结束，本次没有确认签到成功。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
