# GLaDOS 自动签到

GLaDOS 网络自动多账号签到脚本，支持 GitHub Actions 定时运行与本地运行，支持 Telegram 和微信推送通知。

> ⚠️ **重要更新提示**：GLaDOS 官方已升级鉴权机制，目前必须包含 Cookie 鉴权字段（如 `gld:sess`、`gld:sess.sig`、`koa:sess`、`koa:sess.sig`，部分环境还含有 `gld:accts`、`gld:accts.sig`）。若缺少核心 Cookie，接口将直接返回 `{"code": -2, "message": "没有权限"}`。

---

## 📌 常见疑问：为什么 Cookie 名字有冒号（`:`），但 JSON 键名用下划线（`_`）？

在浏览器 Cookie 中，名字通常带有冒号与点号，例如：
- `gld:sess`
- `gld:sess.sig`
- `gld:accts`
- `koa:sess`

### 为什么推荐用下划线？
1. **GitHub Secret 命名限制**：GitHub 的 Secret 名称**只允许使用英文字母、数字和下划线（`_`）**，不允许包含冒号（`:`）或点号（`.`）。
2. **规范习惯**：在编写配置和环境变量映射时，下划线命名（如 `gld_sess`、`koa_sess`）在各种系统和工具中兼容性最好。

> 💡 **无需担心！脚本已做双向智能兼容：**
> 脚本内部已经完全兼容带冒号和下划线两种写法。也就是说，你在 JSON 里写 `"gld_sess"` 或者 `"gld:sess"`，脚本**都能自动识别并正确发送**给 GLaDOS 服务器！

---

## 功能特性

- 🚀 **每日自动签到**：支持 GitHub Actions 定时任务（每天北京时间 08:30 自动执行），无需服务器
- 👥 **无限多账号支持**：账号数量无限制，可在数组中自由追加
- 🏷️ **智能账号备注**：`name` 字段完全可选，未填写时自动编号，报告中自动附带每个账号绑定的真实邮箱
- 🍪 **支持两种 Cookie 格式**：支持拆分字段格式（下划线/冒号均可），也支持直接粘贴整串浏览器 Cookie 字符串
- 📱 **多渠道通知推送**：支持 Telegram Bot 以及微信推送（Server酱）
- 🔒 **本地安全隔离**：本地支持 `accounts.local.json`，已被 `.gitignore` 忽略，绝不泄漏敏感凭据

---

## 使用方法

### 1. Fork 本仓库

点击右上角的 `Fork` 按钮，将本仓库 fork 到你的 GitHub 账号下。

---

### 2. 获取账号 Cookie

1. 浏览器打开并登录 [GLaDOS 控制台](https://glados.cloud/console/checkin)。
2. 按 `F12` 打开浏览器开发者工具。
3. **方法 A（在 Application 中查看字段）**：
   - 切换到 **应用 (Application)** 标签页 -> 左侧展开 **Cookie** -> 点击 `https://glados.cloud`。
   - 分别找到并复制以下字段的值：
     - `gld:sess`
     - `gld:sess.sig`
     - `koa:sess`
     - `koa:sess.sig`
     - *(如有 `gld:accts` 和 `gld:accts.sig` 也可一同复制)*
4. **方法 B（直接复制整串 Cookie，最便捷，零出错率）**：
   - 切换到 **网络 (Network)** 标签页，刷新页面或点击任意请求。
   - 在右侧 **标头 (Headers)** -> **请求标头 (Request Headers)** 找到 `Cookie`，直接鼠标右键复制整行字符串。

---

### 3. 配置 GitHub Actions Secrets

进入你 Fork 的仓库，点击 **Settings** -> **Secrets and variables** -> **Actions**，点击 **New repository secret**：

#### 必选配置：`GLADOS_COOKIES_JSON`

将多个账号的 JSON 填入 Secret，支持以下任意格式：

##### 格式一：字段式格式（推荐，下划线或冒号均支持）
```json
[
  {
    "name": "账号1",
    "gld_sess": "你的 gld:sess 值",
    "gld_sess_sig": "你的 gld:sess.sig 值",
    "koa_sess": "你的 koa:sess 值",
    "koa_sess_sig": "你的 koa:sess.sig 值",
    "gld_accts": "可选，如有则填",
    "gld_accts_sig": "可选，如有则填"
  },
  {
    "name": "账号2",
    "gld_sess": "账号2的 gld:sess 值",
    "gld_sess_sig": "账号2的 gld:sess.sig 值",
    "koa_sess": "账号2的 koa:sess 值",
    "koa_sess_sig": "账号2的 koa:sess.sig 值"
  }
]
```

##### 格式二：整串 Cookie 格式（最方便）
直接复制浏览器抓包里的整条 Cookie，粘贴到 `"cookie"` 字段即可：
```json
[
  {
    "name": "账号1",
    "cookie": "gld:sess=gld_xxx; gld:sess.sig=xxx; koa:sess=xxx; koa:sess.sig=xxx; gld:accts=xxx; gld:accts.sig=xxx"
  },
  {
    "name": "账号2",
    "cookie": "直接粘贴账号2在浏览器里的整串 Cookie"
  }
]
```

> 💡 **说明**：
> 1. 支持任意多个账号，按数组格式继续追加 `{ ... }` 即可。
> 2. `"name"` 字段为可选参数，若不写则脚本自动命名为 `账号 1`、`账号 2`，并在签到结果中自动追加邮箱以便区分。

#### 可选通知配置

- `TG_BOT_TOKEN`：Telegram 机器人的 Bot Token
- `TG_CHAT_ID`：接收通知的 Telegram Chat ID / 用户 ID
- `SERVERCHAN_KEY`：Server酱 SendKey（用于微信通知）

---

### 4. 启用与测试 GitHub Actions

1. 进入仓库顶部的 **Actions** 标签页。
2. 若提示工作流未启用，点击启用。
3. 在左侧选择 **GLaDOS Checkin** 工作流，点击右侧的 **Run workflow** -> 绿色按钮 **Run workflow** 进行手动触发测试。
4. 点进运行记录查看日志，即可看到所有账号的签到详情和流量统计。

---

### 5. 本地运行（可选）

1. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```
2. 在项目根目录下创建 `accounts.local.json`，把你的账号 JSON 内容粘贴进去（该文件已被 git 忽略，不会误提交）。
3. 运行签到：
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
