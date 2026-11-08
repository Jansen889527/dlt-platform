#!/usr/bin/env bash
# 大乐透安卓 APK 一键构建脚本（在装有 Android Studio 的 Mac 上运行）
# 用法：cd ~/WorkBuddy/dlt-platform/android-app && bash build-apk.sh
set -e

cd "$(dirname "$0")"

echo "================ 0/5 检查 Node.js ================"
if ! command -v node >/dev/null 2>&1; then
  echo "❌ 未检测到 Node.js。请先安装："
  echo "   方式一（推荐）：brew install node"
  echo "   方式二：官网 https://nodejs.org 下载 LTS 版 pkg 安装"
  echo "   装完重开终端再跑本脚本。"
  exit 1
fi
echo "✅ Node.js $(node --version) / npm $(npm --version)"

echo "================ 1/5 探测 Android SDK ================"
if [ -z "$ANDROID_HOME" ] && [ -z "$ANDROID_SDK_ROOT" ]; then
  if [ -d "$HOME/Library/Android/sdk" ]; then
    export ANDROID_HOME="$HOME/Library/Android/sdk"
    export ANDROID_SDK_ROOT="$HOME/Library/Android/sdk"
  fi
fi
if [ -z "$ANDROID_HOME" ]; then
  echo "❌ 未找到 Android SDK。请先打开 Android Studio 一次（会自动下载 SDK），"
  echo "   或手动 export ANDROID_HOME=你的sdk路径 后重跑。"
  exit 1
fi
echo "✅ ANDROID_HOME=$ANDROID_HOME"
export PATH="$ANDROID_HOME/platform-tools:$ANDROID_HOME/cmdline-tools/latest/bin:$PATH"

echo "================ 2/5 配置网络（代理自动探测） ================"
# 先试直连
if curl -sS -o /dev/null -m 6 https://registry.npmjs.org 2>/dev/null; then
  echo "✅ 终端可直连外网，无需代理。"
else
  echo "   终端直连外网失败，尝试探测本地代理端口..."
  PROXY_FOUND=""
  for p in 7890 7891 7897 1087 6152 10808 8080 8888 10809 7892 7893; do
    if curl -sS -o /dev/null -m 3 -x "http://127.0.0.1:$p" https://registry.npmjs.org 2>/dev/null; then
      PROXY_FOUND="http://127.0.0.1:$p"
      break
    fi
  done
  if [ -n "$PROXY_FOUND" ]; then
    export http_proxy="$PROXY_FOUND"
    export https_proxy="$PROXY_FOUND"
    export HTTP_PROXY="$PROXY_FOUND"
    export HTTPS_PROXY="$PROXY_FOUND"
    echo "✅ 检测到本地代理 $PROXY_FOUND，已自动设置（npm/gradle 将走代理下载）"
  else
    echo "⚠️ 未检测到本地代理端口。npm install 和 gradle 需要联网下载依赖，"
    echo "   请先打开你的翻墙/代理软件，并确认它开启了本地 HTTP 代理端口"
    echo "   （Clash 默认 7890，可在软件里查看 Port），然后执行："
    echo "       export https_proxy=http://127.0.0.1:端口"
    echo "   再重跑本脚本。或保持软件开启后重跑本脚本（会自动重试探测）。"
    exit 1
  fi
fi

echo "================ 3/5 安装 Web 依赖 ================"
npm install

echo "================ 4/5 同步网页到原生工程 ================"
npx cap sync android

echo "================ 5/5 构建 APK（debug 可直接安装） ================"
cd android
chmod +x gradlew 2>/dev/null || true
./gradlew assembleDebug

APK="app/build/outputs/apk/debug/app-debug.apk"
if [ -f "$APK" ]; then
  echo ""
  echo "🎉 构建成功！APK 位于："
  echo "   $(pwd)/$APK"
  echo ""
  echo "   下一步：把这个 .apk 文件用数据线 / 微信 / 聊天工具传到安卓手机，"
  echo "   在手机上点击它即可安装（debug 包无需上架商店，可能需允许\"未知来源\"安装）。"
  echo "   安装后打开 App，联网即加载最新大乐透页面；离线则用壳内大乐透快照。"
else
  echo "❌ 未找到 APK，请检查上面的 gradle 报错（多半是网络/SDK 问题）。"
  exit 1
fi
