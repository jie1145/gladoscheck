# 配置说明

## 当前官网需要浏览器验证

2026-11-15 核查：当前签到请求需要一次性挑战和 Cloudflare 验证，Cookie 只能用于会话登录，不能替代该流程。GitHub Actions 的 requests 模式会提示 `browser-required` 并失败退出。

本地正常网页模式：

```bash
python -m pip install -r requirements-browser.txt
python browser_checkin.py --login --keep-open
```

本人在官网登录并按需完成验证；工具只点击原有签到按钮并检查接口结果。专用资料默认保存在已被 Git 忽略的 `.browser-profile/`，不需要复制 Cookie 到配置文件。真实账号是否成功仍需实测。

下面的 Cookie 配置用于旧版 API 模式及状态诊断。

---

## 核心配置三步法

### 1. 抓取 Cookie
1. 打开 [GLaDOS 控制台](https://glados.cloud/console/checkin) 并按 `F12`。
2. 切换到 **网络 (Network)** 标签页，刷新网页。
3. 点击任意请求，在右侧请求标头中找到并复制完整的 **`cookie:`** 字符串。

---

### 2. 填写位置（二选一）

| 使用方式 | 填写位置 | 说明 |
| :--- | :--- | :--- |
| **GitHub Actions**（云端免开机） | 仓库 `Settings` ➔ `Secrets and variables` ➔ `Actions` | 添加/修改变量名 **`GLADOS_COOKIES_JSON`**，将 JSON 贴入 |
| **本地运行** | 项目根目录下创建 **`accounts.local.json`** | 将 JSON 贴入，执行 `python checkin.py` |

---

### 3. 支持的 JSON 填写格式

无论在哪填写，内容均统一支持以下格式（支持 1 个或多个账号）：

#### 格式一：整行 Cookie（最推荐，简单省心）
```json
[
  {
    "name": "账号1",
    "cookie": "直接粘贴浏览器里复制的整行Cookie"
  },
  {
    "name": "账号2",
    "cookie": "直接粘贴小号整行Cookie"
  }
]
```

#### 格式二：拆分字段（下划线 / 冒号均支持）
```json
[
  {
    "name": "账号1",
    "gld_accts": "...",
    "gld_accts_sig": "...",
    "gld_sess": "...",
    "gld_sess_sig": "...",
    "koa_sess": "...",
    "koa_sess_sig": "..."
  }
]
```

---

## 选填通知变量

可在 GitHub Actions Secrets 中选填：
- `TG_BOT_TOKEN` / `TG_CHAT_ID`：Telegram 推送
- `SERVERCHAN_KEY`：Server酱 微信推送
