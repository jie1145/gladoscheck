# GLaDOS 自动签到

GLaDOS 网络自动多账号签到脚本，支持 GitHub Actions 定时运行与本地运行，支持 Telegram 和微信推送通知。

> ⚠️ **重要更新提示**：GLaDOS 官方已升级鉴权机制，目前必须包含 Cookie 鉴权凭证（现在浏览器通常包含 **6 个字段**：`gld:accts`、`gld:accts.sig`、`gld:sess`、`gld:sess.sig`、`koa:sess`、`koa:sess.sig`）。若缺少核心 Cookie，接口将直接返回 `{"code": -2, "message": "没有权限"}`。

---

## 📌 常见疑问：为什么 Cookie 名字有冒号（`:`），但 JSON 键名用下划线（`_`）？

在浏览器 Cookie 中，字段名字通常带有冒号与点号，例如：`gld:sess`、`gld:sess.sig`、`gld:accts`。

- **为什么推荐下划线**：GitHub 环境变量和 Secret 命名**严禁使用冒号（`:`）和点号（`.`）**，只允许英文字母、数字和下划线（`_`）。
- **智能兼容**：脚本内部已经内置自动映射转换，无论你在 JSON 里写 `"gld_sess"` 还是 `"gld:sess"`，脚本**都能自动识别并正确发送**！

---

## 功能特性

- 🚀 **每日自动签到**：支持 GitHub Actions 定时任务（每天北京时间 08:30 自动执行），无需自备服务器
- 👥 **无限多账号支持**：账号数量无限制，都在同一个变量里以数组形式配置
- 🏷️ **智能账号备注**：`name` 字段完全可选，未填写时自动编号，报告中自动附带每个账号绑定的真实邮箱
- 🍪 **双模式支持**：支持填写 6 个拆分字段，也支持直接粘贴浏览器抓包整行原始 Cookie
- 📱 **多渠道通知推送**：支持 Telegram Bot 以及微信推送（Server酱）
- 🔒 **本地安全隔离**：本地调试使用 `accounts.local.json`，已被 `.gitignore` 忽略，绝不泄漏敏感凭据

---

## 快速上手使用教程（只需 3 步）

### 第 1 步：Fork 本仓库
点击仓库右上角的 `Fork` 按钮，将本仓库完整复制到你的 GitHub 个人账号下。

---

### 第 2 步：获取你的账号 Cookie

1. 打开浏览器并登录 [GLaDOS 控制台](https://glados.cloud/console/checkin)。
2. 按快捷键 `F12` 打开浏览器开发者工具。

这里提供两种获取方式（**强烈推荐方式 B，一键复制零出错**）：

#### 方式 A（在 Application 中获取 6 个字段）
1. 点击顶部的 **应用 (Application)** 标签页（如未显示，可点击 `>>` 展开）。
2. 在左侧面板展开 **存储 (Storage)** -> **Cookie** -> 点击 `https://glados.cloud`。
3. 依次找到并复制以下 **6 个字段** 的值：
   - `gld:accts`
   - `gld:accts.sig`
   - `gld:sess`
   - `gld:sess.sig`
   - `koa:sess`
   - `koa:sess.sig`

#### 方式 B（最推荐：在 Network 中直接复制整行 Cookie，速度最快、不会漏字段）
1. 点击顶部的 **网络 (Network)** 标签页。
2. 刷新页面，在请求列表中点击任意请求（例如 `status` 或 `checkin`）。
3. 在右侧 **标头 (Headers)** -> **请求标头 (Request Headers)** 中找到 **`cookie:`**。
4. 鼠标右键点击该行，直接**复制整行 Cookie 内容**。

---

### 第 3 步：配置 GitHub Actions Secret（只配置这 1 个变量！）

> ⚠️ **新手特别注意**：
> 不要为每个账号单独创建新的 Secret 变量！
> **整个仓库只需要添加 1 个名为 `GLADOS_COOKIES_JSON` 的 Secret**。所有的账号（账号1、账号2、账号N...）全部写进这同一个 JSON 数组里面。

#### 具体配置路径：
1. 打开你 Fork 后的仓库主页。
2. 依次点击顶部导航栏：**Settings**（设置） -> 左侧菜单栏 **Secrets and variables** -> **Actions**。
3. 如果列表里已有 `GLADOS_COOKIES_JSON`，点击它旁边的 ✏️ **铅笔图标（Edit）** 进行修改；若没有，点击绿色按钮 **New repository secret**：
   - **Name（变量名）**：必须填 `GLADOS_COOKIES_JSON`
   - **Secret（内容）**：将你的多账号 JSON 数组粘贴进去（参考下方格式），然后点击 **Add secret / Update secret** 保存。

---

### 📝 `GLADOS_COOKIES_JSON` 的填写示例

#### 示例 1：使用拆分字段格式（6 字段标准版，支持下划线或冒号）
```json
[
  {
    "name": "账号1",
    "gld_accts": "你的 gld:accts 值",
    "gld_accts_sig": "你的 gld:accts.sig 值",
    "gld_sess": "你的 gld:sess 值",
    "gld_sess_sig": "你的 gld:sess.sig 值",
    "koa_sess": "你的 koa:sess 值",
    "koa_sess_sig": "你的 koa:sess.sig 值"
  },
  {
    "name": "账号2",
    "gld_accts": "账号2的 gld:accts 值",
    "gld_accts_sig": "账号2的 gld:accts.sig 值",
    "gld_sess": "账号2的 gld:sess 值",
    "gld_sess_sig": "账号2的 gld:sess.sig 值",
    "koa_sess": "账号2的 koa:sess 值",
    "koa_sess_sig": "账号2的 koa:sess.sig 值"
  }
]
```

#### 示例 2：使用整串 Cookie 格式（最省事，推荐）
```json
[
  {
    "name": "账号1",
    "cookie": "gld:accts=...; gld:accts.sig=...; gld:sess=...; gld:sess.sig=...; koa:sess=...; koa:sess.sig=..."
  },
  {
    "name": "账号2",
    "cookie": "直接粘贴账号2在浏览器 Network 中复制的整串 Cookie"
  }
]
```

> 💡 **小贴士**：
> - 无论你有 2 个、5 个还是更多账号，只需在方括号 `[ ... ]` 内部按英文逗号 `,` 分隔继续追加 `{ ... }` 对象即可。
> - `"name"` 字段选填，如果不写脚本会自动显示为 `账号 1`，并在签到汇报中自动附带对应的邮箱地址。

---

### 第 4 步：立即手动运行测试

1. 点击仓库顶部的 **Actions** 标签页。
2. 如果页面提示工作流已被禁用，点击绿色按钮 **I understand my workflows, go ahead and enable them**。
3. 在左侧工作流列表中点击 **GLaDOS Checkin**。
4. 在右侧找到 **Run workflow** 下拉按钮 -> 点击绿色的 **Run workflow** 按钮。
5. 等待几十秒后点击查看运行日志，即可看到多账号详细签到与剩余天数报告！

---

## 选填配置：消息推送

同样在 `Settings` -> `Secrets and variables` -> `Actions` 下添加对应 Secret：

- **Telegram 消息推送**：
  - `TG_BOT_TOKEN`：Telegram 机器人的 Bot Token（向 `@BotFather` 申请）
  - `TG_CHAT_ID`：接收通知的用户 ID 或群组 ID（向 `@userinfobot` 获取）
- **微信消息推送（Server酱）**：
  - `SERVERCHAN_KEY`：访问 [Server酱官网](https://sct.ftqq.com/) 扫码登录获取的 SendKey

---

## 本地运行说明（可选）

1. 克隆项目并安装依赖：
   ```bash
   pip install -r requirements.txt
   ```
2. 在项目根目录下新建一个名为 `accounts.local.json` 的文件，把上面的多账号 JSON 数组粘贴进去（该文件已被 `.gitignore` 忽略，安全不会被提交）。
3. 执行运行：
   ```bash
   python checkin.py
   ```

---

## 自动运行时间

工作流配置在 `.github/workflows/checkin.yml`，默认每天北京时间 **08:30 (UTC 00:30)** 自动触发。如需修改，可调整文件中的 cron 表达式：
```yaml
schedule:
  - cron: '30 0 * * *'  # UTC 00:30 = 北京时间 08:30
```

---

## 免责声明

本项目仅供学习交流与自动化脚本参考，请遵守服务提供商的相关使用条款。使用者需对自身账号安全及脚本使用行为负责。

## License

MIT License
