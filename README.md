# 大乐透选号工具 · 部署指南

参照双色球 app 做的大乐透独立版 PWA：前区 1-35 选 5、后区 1-12 选 2，含四个模块（今期开奖 / 往期开奖 / 预测走势 / 随机预测）。
仓库：`https://github.com/Jansen889527/dlt-platform`（Public），线上页面：`https://jansen889527.github.io/dlt-platform/`。

安卓 APK 的 `server.url` 即指向该 Pages 地址 —— **网页更新推送到 GitHub 后，用户在 App 内点「检查更新」即可生效，无需重装 APK**。本仓库是大乐透代码的唯一管理目录，网页源文件在仓库根目录（`dlt-platform-web/` 为废弃的旧发布目录，勿再修改）。

> 注：本机 Mac 终端的 git 通道连不上 github.com，但可通过 GitHub REST API 推送；若终端 `git push` 失败，让 WorkBuddy 代推即可，不影响日常更新。

## 目录结构

```
dlt-platform/
├── index.html              # 主页面（四个模块），打开即用
├── data.json               # 最近 120 期真实开奖（兜底数据，最新 26125 / 2026-11-02）
├── manifest.webmanifest    # PWA 配置（可"添加到主屏幕"当 App）
├── sw.js                   # 离线缓存
├── version.json            # 版本号（改内容时 bump，App 端会提示更新）
├── icon-192.png / icon-512.png / icon-maskable-512.png / apple-touch-icon.png
├── scripts/gen_icons.py    # 重新生成图标用
├── dlt_live.py             # 腾讯云函数源码（启用实时开奖用，见下文"二"）
└── android-app/            # Capacitor 安卓壳（打包 APK 用，见下文"三"）
    ├── build-apk.sh        # 安卓 APK 一键构建脚本（Mac 上运行）
    ├── capacitor.config.json
    ├── www/                # 离线兜底网页快照
    └── android/            # 原生安卓工程
```

---

## 零、最省事：一键部署（deploy.sh，推荐先看）

如果你嫌下面的手动步骤麻烦，仓库里已经放好了一个一键脚本 `deploy.sh`，在 Mac 终端跑一条命令就能自动建仓库并推送：

```bash
cd ~/WorkBuddy/dlt-platform
chmod +x deploy.sh
./deploy.sh
```

脚本会：自动推断你的 GitHub 用户名 → 若已装 GitHub CLI（`gh`）则直接建仓库并推送；若没装 `gh`，则改用 https 地址推送（终端会提示输入用户名，密码处填 Personal Access Token）。
跑完后，按脚本末尾提示去 `Settings → Pages` 把 Source 设为 `main` / `/root` 即可。

> 手动 5 步见下文「一」，适合想完全自己掌控、或脚本出错时兜底。

---

## 一、网页上线（GitHub Pages）—— 必做，约 5 分钟

目标：让大乐透网页有一个公网地址，手机/电脑浏览器直接打开。

### 第 1 步：打开 Mac 终端
- 在「访达」→「应用程序」→「实用工具」里打开「终端」（或按 `Command + 空格`，输入 `终端` 回车）。
- 把下面第 3 步的命令一条条复制粘贴进去，每条回车执行。

### 第 2 步：在 GitHub 网页新建一个空仓库
1. 浏览器打开 https://github.com 并登录你的账号（用户名 `Jansen889527`）。
2. 右上角点 `+` → `New repository`（新建仓库）。
3. 仓库名（Repository name）填：`dlt-platform`
4. 说明（Description）可填可不填，例如：大乐透选号工具 PWA
5. 仓库类型选 **Public**（公开，这样 GitHub Pages 免费可用）
6. **不要**勾选 "Add a README file" / "Add .gitignore" 等任何初始化选项（仓库要保持为空，方便一会直接推送）
7. 点 `Create repository`（创建仓库）。

### 第 3 步：在终端推送代码
逐条执行（直接复制粘贴，每条回车）：

```bash
cd ~/WorkBuddy/dlt-platform
git push -u origin main
```

- 如果终端提示输入用户名/密码：用户名填 `Jansen889527`；密码处**不是 GitHub 登录密码**，而是要填「个人访问令牌（Token）」。
  - 令牌获取：GitHub 网页右上角头像 → `Settings` → 左侧 `Developer settings` → `Personal access tokens` → `Tokens (classic)` → `Generate new token` → 勾选 `repo` 权限 → 生成后**复制保存**（只显示一次）。
- 如果提示 `permission denied (publickey)`：说明你电脑没配 SSH 钥匙，改用 https 地址再推：
  ```bash
  git remote set-url origin https://github.com/Jansen889527/dlt-platform.git
  git push -u origin main
  ```

看到 `main -> main` 或 `Writing objects: 100%` 就成功了。

### 第 4 步：开启 GitHub Pages
1. 回到刚建的仓库页面 `https://github.com/Jansen889527/dlt-platform`。
2. 点上方 `Settings`（设置）→ 左侧 `Pages`（页面）。
3. `Build and deployment` 下，`Source`（源）选 `Deploy from a branch`（从分支部署）。
4. `Branch`（分支）选 `main`，目录选 `/ (root)`，点 `Save`（保存）。
5. 等 1 分钟左右刷新页面，顶部会出现一行绿字：`Your site is published at https://jansen889527.github.io/dlt-platform/`

### 第 5 步：验证
浏览器打开 `https://jansen889527.github.io/dlt-platform/`，能看到大乐透四个标签页、最新一期 26125 即成功。

> 此时页面顶部数据源会显示「本地静态数据（与云端同步）」——这是正常的，说明还没部署实时云函数，数据停在 26125。要实时更新见"二"。

---

## 二、启用实时开奖数据（可选）—— 腾讯云函数

部署后，网页打开即自动拉到最新一期（无需本机常驻服务）。不部署也能用，只是数据停在 26125。

1. 浏览器打开 https://console.cloud.tencent.com/scf （腾讯云函数控制台），登录。
2. 左侧「函数服务」→ `新建` → 创建方式选「空白函数」。
   - 函数名称：`dlt-live`
   - 运行环境：`Python 3.10`
   - 地域：广州（或离你近的）
3. 创建后在「函数代码」里，把本仓库 `dlt_live.py` 的**全部内容**粘贴进去（或上传该文件），**入口函数**填 `main_handler`。
4. 点「部署」。
5. 左侧「触发管理」→ `创建触发器`：
   - 触发方式：`函数 URL`
   - 认证方式：**不认证**
   - 创建后复制「函数 URL」（形如 `https://xxxx.ap-guangzhou.tencentscf.com`）。
6. 打开本仓库 `index.html`，找到第 434 行：
   ```js
   const DLT_SCF_URL = '';
   ```
   把空串改成刚才复制的函数 URL，保存。
7. 终端重新推送：
   ```bash
   cd ~/WorkBuddy/dlt-platform
   git add index.html
   git commit -m "feat: 接入大乐透实时云函数"
   git push
   ```
8. 再打开网页，数据源会显示「实时（中体彩云端直连）」，且为最新一期。

---

## 三、打包安卓 APK —— Capacitor（你要的"安装包"就在这）

> ✅ 线上源为 GitHub Pages：`https://jansen889527.github.io/dlt-platform/`
> 安卓壳的 `server.url`（根目录 `capacitor.config.json` 与 `android/app/src/main/assets/capacitor.config.json` **两处**）均指向它。App 联网即加载线上最新版，离线回退壳内 `assets/public` 快照。**日常改网页只需推送 GitHub，不用重打包 APK。**
>
> 包名 `com.lottery.dlt`、App 名「大乐透选号工具」。正式 release 包用 `~/.android/release.keystore` 签名；签名配置写在 `android/gradle.properties`（**含明文密码，已加入 .gitignore，绝不入库**），模板见 `gradle.properties.example`。
> 构建 release：`cd android && ./gradlew assembleRelease`（需 Android Studio 自带 JBR 21，系统默认 JDK 26 不兼容 AGP 8.13 的 jlink）。

### 环境准备（一次性，在 Mac 上）
- 安装 Node.js（https://nodejs.org，LTS 版）。
- 安装 Android Studio（https://developer.android.com/studio），首次打开会自动下载 Android SDK（需联网，约 1GB+）。

### 一键打包（推荐）
```bash
cd ~/WorkBuddy/dlt-platform/android-app
bash build-apk.sh
```
脚本会自动：① 探测 Android SDK → ② `npm install` → ③ `npx cap sync android` → ④ gradle 构建 debug APK。
成功后终端会打印 APK 路径：`android-app/android/app/build/outputs/apk/debug/app-debug.apk`。

### 手动打包（脚本出错时兜底）
```bash
cd ~/WorkBuddy/dlt-platform/android-app
npm install
npx cap sync android
```
然后用 Android Studio 打开 `android-app/android` 目录：`Build` → `Build Bundle(s) / APK(s)` → `Build APK(s)`。
生成的 APK 在 `android-app/android/app/build/outputs/apk/debug/`。

### 把 APK 装到手机
把 `app-debug.apk` 通过数据线 / 微信 / 聊天工具传到安卓手机，点击安装即可（debug 包可直接安装，无需上架商店）。

### ⚠️ 网络坑（你 Mac 之前 git 连 github 超时，说明终端没走代理）
- `npm install` 和首次 `gradle` 构建都要联网下载依赖。如果 Mac 终端下不动（超时），是因为你电脑上的代理/翻墙软件没给终端开本地端口。
- 解决：打开你电脑的代理软件，开启「允许局域网连接 / 混合模式 / 设置 HTTP 代理端口」，记下端口（常见 7890 / 7897），终端先执行：
  ```bash
  export https_proxy=http://127.0.0.1:端口
  export http_proxy=http://127.0.0.1:端口
  ```
  再跑上面的打包命令即可。

### 重新打包的触发条件
- **日常改网页**：不用重打包！改完重新发布/推送在线版，App 联网自动生效（App 内「检查更新」或下次打开即更新）。
- **只有**换图标 / 包名 / 权限 / 新增原生插件 / 升级 Capacitor 时才需重新跑打包。

---

## 四、日常更新

1. **改文件**：只改仓库根目录的 `index.html` / `data.json` / `sw.js` / `version.json` 等网页文件。
2. **同步副本**：把改动同步到 `android-app/www/` 与 `android-app/android/app/src/main/assets/public/`（离线快照，保持三处一致）。
3. **bump 版本号（必须）**：`version.json` 的 `version` + `index.html` 里的 `APP_VERSION` 同步 +1；若改了静态资源，`sw.js` 的 `CACHE` 名也要变（如 `dlt-v2` → `dlt-v3`）。否则老用户不会收到「发现新版本」提示或读到旧缓存。
4. **推送**：`git add . && git commit -m "说明" && git push`（终端不通就让 WorkBuddy 走 API 代推）。GitHub Pages 约 1~2 分钟 CDN 刷新后生效。
5. **用户端**：App 内点「检查更新」→ 弹「发现新版本」→ 点「立即更新」清缓存刷新，即看到最新版。**全程不用重装 APK。**

- 数据更新：未部署云函数时，需手动更新 `data.json`（重新跑抓取脚本生成）；部署云函数后自动实时。
- **只有**改 `server.url`、原生图标 / App 名 / 包名 / 权限 / Capacitor 插件时，才需要重新打包并重装 APK。

## 五、常见问题

- **页面显示"本地静态数据"**：没部署云函数，正常现象，数据停在 26125。按"二"部署后即变实时。
- **推送被拒绝 / 提示 publickey**：按"一·第 3 步"切到 https 地址并改用 Token 登录。
- **GitHub Pages 打不开**：确认仓库是 Public、Pages 源选的是 `main` 分支 `/root`，且 `index.html` 在仓库根目录。
- **免责声明**：本工具所有"预测/概率"均为历史统计参考，不构成购彩建议。
