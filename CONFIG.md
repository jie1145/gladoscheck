# 详细配置与疑难解答

---

## 📌 核心说明：为什么整个仓库只需 1 个 Secret？

很多新手在配置 GitHub Actions 时容易产生误解，以为有 3 个账号就要创建 3 个 Secret。

**特别澄清**：
- **不需要**创建多个环境变量，**只需要创建 1 个名为 `GLADOS_COOKIES_JSON` 的 Secret**。
- 所有的账号全部以 **JSON 数组**（`[ {账号1}, {账号2}, ... ]`）的形式统一保存在这个变量里。
- 脚本读取该变量后会自动遍历数组中的每一个账号，逐一执行签到和流量检查。

---

## 📌 命名疑问：Cookie 字段中的冒号（`:`）与下划线（`_`）

在浏览器 Application 的 Cookie 面板中，GLaDOS 使用了带冒号和点号的键名：
- `gld:accts`
- `gld:accts.sig`
- `gld:sess`
- `gld:sess.sig`
- `koa:sess`
- `koa:sess.sig`

### 为什么在文档中推荐使用下划线（如 `gld_sess`）？
因为 GitHub Actions Secret 和操作系统环境变量有命名规范，**严禁使用冒号 `:` 和点号 `.`**。

> 💡 **无需担心：脚本已做全兼容映射**
> 脚本内部已经实现了键名智能映射，你在 JSON 中写：
> - 规范写法：`"gld_sess"`, `"gld_sess_sig"`, `"gld_accts"`, `"koa_sess"`...
> - 原始写法：`"gld:sess"`, `"gld:sess.sig"`, `"gld:accts"`, `"koa:sess"`...
> 
> 脚本都会自动转换为 GLaDOS 所需的正确请求头发送给服务器。

---

## 1. Cookies 抓取方法详解

### 方式一：Network 网络面板（最推荐，一次性复制，绝不漏字段）
1. 打开浏览器登录 [GLaDOS 控制台](https://glados.cloud/console/checkin)。
2. 按 `F12` 打开开发者工具，点击 **网络 (Network)** 标签页。
3. 刷新页面，在列表中随意点击一个请求（如 `status` 或 `checkin`）。
4. 在右侧 **标头 (Headers)** -> **请求标头 (Request Headers)** 中找到 **`cookie:`**。
5. 复制整行内容。在配置中直接填入 `"cookie": "你复制的整行内容"` 即可！

### 方式二：Application 应用面板（逐个字段提取）
1. 在开发者工具中切换到 **应用 (Application)** 标签页。
2. 左侧展开 **存储 (Storage)** -> **Cookie** -> 点击 `https://glados.cloud`。
3. 找到并分别复制以下 **6 个字段** 的值：
   - `gld:accts`
   - `gld:accts.sig`
   - `gld:sess`
   - `gld:sess.sig`
   - `koa:sess`
   - `koa:sess.sig`

---

## 2. GitHub Secrets 具体配置路径

1. 进入你 Fork 的 GitHub 仓库。
2. 依次点击顶部菜单：`Settings` -> 左侧菜单 `Secrets and variables` -> `Actions`。
3. 点击 **New repository secret**（如果已经存在 `GLADOS_COOKIES_JSON` 则点击它右边的 ✏️ 编辑）：
   - **Name**：`GLADOS_COOKIES_JSON`
   - **Secret**：填入包含所有账号的 JSON 内容（格式见下文）。

### JSON 内容模板（二选一）：

#### 模板 A：6 字段标准版
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
  },
  {
    "name": "账号2",
    "gld_accts": "...",
    "gld_accts_sig": "...",
    "gld_sess": "...",
    "gld_sess_sig": "...",
    "koa_sess": "...",
    "koa_sess_sig": "..."
  }
]
```

#### 模板 B：整串 Cookie 版（最推荐）
```json
[
  {
    "name": "账号1",
    "cookie": "从 Network 面板复制的整行完整 Cookie"
  },
  {
    "name": "账号2",
    "cookie": "从 Network 面板复制的整行完整 Cookie"
  }
]
```

---

## 3. 推送通知配置（可选）

如果需要签到结果推送到微信或 Telegram，同样在 `Settings` -> `Secrets and variables` -> `Actions` 下添加对应变量：

- **Telegram 推送**：
  - `TG_BOT_TOKEN`：机器人 Token（通过 `@BotFather` 获取）
  - `TG_CHAT_ID`：你的用户 ID 或群组 ID（通过 `@userinfobot` 获取）
- **微信推送（Server酱）**：
  - `SERVERCHAN_KEY`：Server酱 SendKey（访问 [sct.ftqq.com](https://sct.ftqq.com/) 扫码获取）

---

## 4. 本地运行与调试

1. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```
2. 在项目根目录创建 `accounts.local.json`，把你的账号 JSON 数组粘贴进去（该文件已被 `.gitignore` 忽略，安全隔离）。
3. 启动签到：
   ```bash
   python checkin.py
   ```
