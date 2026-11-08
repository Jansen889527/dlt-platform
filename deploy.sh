#!/usr/bin/env bash
# 大乐透 dlt-platform 一键部署到 GitHub（在用户本机 Mac 终端运行，非 WorkBuddy 沙箱）
set -e
cd "$(dirname "$0")"

REPO="dlt-platform"
REMOTE="origin"

# 推断 GitHub 用户名（优先用 gh 已登录账号，否则默认已知的 Jansen889527）
USER="Jansen889527"
if command -v gh >/dev/null 2>&1; then
  GH_USER=$(gh api user --jq .login 2>/dev/null || true)
  [ -n "$GH_USER" ] && USER="$GH_USER"
fi

echo "==> 目标仓库: $USER/$REPO  (分支 main)"

if command -v gh >/dev/null 2>&1; then
  echo "==> 检测到 gh CLI，尝试创建并推送..."
  if gh repo create "$REPO" --public --source . --remote "$REMOTE" --push 2>/dev/null; then
    echo "✅ 已创建仓库并推送成功"
  else
    echo "（仓库已存在或创建失败，改为直接推送）"
    git remote set-url "$REMOTE" "git@github.com:$USER/$REPO.git" 2>/dev/null || true
    git push -u "$REMOTE" main
  fi
else
  echo "==> 未检测到 gh CLI，改用 https 直接推送（会提示输入用户名和 token）。"
  git remote set-url "$REMOTE" "https://github.com/$USER/$REPO.git" 2>/dev/null || true
  if git push -u "$REMOTE" main; then
    echo "✅ 已推送成功"
  else
    echo "推送失败。请先在 GitHub 网页手动新建空仓库 $REPO(public)，"
    echo "再确认凭据：用户名填 $USER，密码处用 Personal Access Token（非登录密码）。"
    exit 1
  fi
fi

echo ""
echo "==> 下一步：打开 https://github.com/$USER/$REPO/settings/pages"
echo "     Source 选 [Deploy from a branch] → [main] → [/root] → Save"
echo "==> 站点地址：https://$USER.github.io/$REPO/"
echo "==> 安卓壳 capacitor.config.json 已指向该域名，构建 APK 后即远程加载此站点"
