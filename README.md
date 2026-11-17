# GLaDOS 自动签到

GLaDOS 签到工具，包含旧版 API 模式和本地官网浏览器模式。

## 当前网站验证要求（2026-11-15 核查）

官网现在先调用 `/api/user/checkin/challenge`，再通过页面完成一次性 nonce、浏览器 proof 和 Cloudflare Turnstile 验证。只发送 Cookie 和 `{"token":"glados.cloud"}` 的旧请求不再足够。

- **GitHub Actions 的 requests 模式无法完成当前网页验证**。本版本会识别这一要求、在摘要显示原因并返回失败，避免任务绿色却没有签到。
- 本地浏览器模式会打开可见的专用浏览器，通过官网原有按钮签到。需要时由本人登录或完成人机验证。它没有绕过验证的实现，也不保证无人值守成功。
- 只有签到接口明确返回 `code: 0` 才算成功；其中 `repeated: true` 表示已签到。读取账号状态成功不等于签到成功。

### 使用本地官网浏览器模式

```bash
python -m pip install -r requirements-browser.txt
python browser_checkin.py --login --keep-open
```

默认使用已安装的 Microsoft Edge，在本项目 `.browser-profile/` 里保存专用登录状态。请本人在新窗口登录并完成账号引导，然后回到终端按回车；若出现 Cloudflare 交互验证，也由本人在官网完成。浏览器模式不读取 GitHub Secret，也不把 Cookie 上传到其他地方。

以后可以运行 `python browser_checkin.py`，使用同一个本地登录状态。电脑需要开机且有图形桌面，验证可能仍需本人操作。可用 `--profile 路径` 指定专用资料目录，请勿使用日常浏览器正在占用的目录；自定义目录也应放在仓库之外。

没有 Edge 时，可选择已安装的 Chrome：`python browser_checkin.py --channel chrome --login`。使用 bundled Chromium 时，先执行 `python -m playwright install chromium`，再选择 `--channel chromium`。

浏览器模式已完成离线回归测试，**尚未在真实账号上确认签到成功**。最终以官网返回成功或已签到为准，超时和验证失败均返回非零退出码。

### 检查结果

| 退出码 | 含义 |
| --- | --- |
| 0 | 所有账号成功／已签到，或浏览器模式收到明确成功结果 |
| 1 | 签到失败、需要浏览器验证或未确认成功 |
| 2 | 配置错误、缺少依赖或浏览器未就绪 |

回归测试：`python -m unittest discover -s tests -v`。测试使用模拟响应，不需要真实账号，不访问签到服务。

---

## 核心使用流程（极简 3 步）

整个配置非常简单，本质就是：**抓取 Cookie ➔ 填入配置（GitHub Action 或 本地）➔ 运行**。

---

### 第一步：获取你的 Cookie

1. 打开浏览器登录 [GLaDOS 控制台](https://glados.cloud/console/checkin)。
2. 按 `F12` 打开开发者工具，点击 **网络 (Network)** 标签页。
3. 刷新页面，在左侧任意点击一个请求（如 `status` 或 `checkin`）。
4. 在右侧 **标头 (Headers)** 找到 **`cookie:`**，直接**复制整行 Cookie 内容**。

> 💡 *小号同样操作：登录小号后按上述步骤复制小号的整行 Cookie 即可。*

---

### 第二步：填写 Cookie（按你的使用方式二选一）

#### 方式 A：GitHub Actions 云端定时运行（仅兼容无网页挑战的旧接口）
1. Fork 本仓库到你的 GitHub。
2. 进入仓库设置：`Settings` ➔ 左侧 `Secrets and variables` ➔ `Actions`。
3. 点击 **New repository secret**（已有则点铅笔编辑）：
   - **名称（Name）**：`GLADOS_COOKIES_JSON`
   - **内容（Secret）**：直接把你的账号 JSON 填进去（参考下文【支持的填写格式】）。
4. 去仓库顶部的 **Actions** 页面启用并手动测试一次。定时配置为每天北京时间 **08:30**；当前官网需要浏览器验证时，这个模式会失败并显示说明，不能视为可用的每日自动签到。

#### 方式 B：本地运行旧 API（同样受网页验证限制）

当前官网需要浏览器验证时，请使用本文开头的 `browser_checkin.py`。下列命令只适用于不要求网页挑战的旧接口，不能通过换成本机执行来解决当前验证失败。

1. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```
2. 在项目根目录下新建 `accounts.local.json` 文件（该文件已被 `.gitignore` 保护，绝不会被 Git 提交上传）。
3. 把你的账号 JSON 内容保存进去，终端运行即可：
   ```bash
   python checkin.py
   ```

---

### 第三步：填写格式说明（支持以下 2 种格式）

不管是在 GitHub Secret 还是本地 `accounts.local.json`，内容都是一个 JSON 数组，**支持任意多个账号**：

#### 格式 1：直接贴整行 Cookie（最推荐，简单零出错）
把刚才抓包复制的完整字符串贴进 `"cookie"` 字段即可：
```json
[
  {
    "name": "账号1",
    "cookie": "gld:accts=...; gld:sess=...; koa:sess=..."
  },
  {
    "name": "账号2",
    "cookie": "粘贴小号整行Cookie"
  }
]
```

#### 格式 2：拆分字段格式（支持冒号或下划线）
如果你习惯在 Application 面板里单项复制字段，也可以这样写：
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
*(注：字段名用 `gld_sess` 或带冒号的 `gld:sess` 脚本均可自动识别)*

---

## 选填：消息推送

如需签到结果发送到手机，可在 GitHub Secrets 中添加对应变量：
- **Telegram**：`TG_BOT_TOKEN`（机器人Token）、`TG_CHAT_ID`（用户ID）
- **微信（Server酱）**：`SERVERCHAN_KEY`（SendKey）

---

## 免责声明

本项目仅供个人学习交流使用，请遵守服务商条款。
