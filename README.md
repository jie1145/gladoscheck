# GLaDOS 自动签到

极简高效的 GLaDOS 网络自动签到脚本。支持 **GitHub Actions（每日云端定时免服务器）** 与 **本地运行**，支持无限多账号与微信/Telegram 推送。

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

#### 方式 A：GitHub Actions 云端定时运行（推荐，免电脑开机）
1. Fork 本仓库到你的 GitHub。
2. 进入仓库设置：`Settings` ➔ 左侧 `Secrets and variables` ➔ `Actions`。
3. 点击 **New repository secret**（已有则点铅笔编辑）：
   - **名称（Name）**：`GLADOS_COOKIES_JSON`
   - **内容（Secret）**：直接把你的账号 JSON 填进去（参考下文【支持的填写格式】）。
4. 去仓库顶部的 **Actions** 页面启用并手动测试一次。以后每天北京时间 **08:30** 自动签到！

#### 方式 B：本地电脑运行
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
