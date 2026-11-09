# -*- coding: utf-8 -*-
"""
大乐透实时开奖云函数（腾讯云 SCF / 函数 URL 部署）
=================================================
- 抓取 500 彩票网大乐透历史接口，解析最近 120 期真实开奖
- 返回带 CORS 头的 JSON 数组，结构与前端 FALLBACK 完全一致：
  [{"code","date","week","front":[5],"back":[2],"p1":{"count","money"},"p2":{...}}, ...]  （降序，最新在前）
- 前端（index.html）把 DLT_SCF_URL 指向本函数 URL 后，打开网页即实时拿到最新一期，无需本机常驻服务

部署步骤（腾讯云控制台）：
  1. 函数服务 → 新建 → 运行环境 Python 3.10 → 上传/粘贴本文件，入口函数填 main_handler
  2. 触发管理 → 创建「函数 URL」→ 启用，认证方式选「不认证」
  3. 复制函数 URL，填到前端 index.html 的常量 DLT_SCF_URL，再推送 GitHub Pages
     （网页热更新即可，不用重装 APK；用户 App 点「检查更新」即生效）
  4. 函数配置里把「响应体透传」打开；本函数已自带跨域头（Allow-Origin=*），函数 URL 仍需允许 OPTIONS 预检
说明：
  - 数据源 500 彩票网 history.php 为公开页面，已带浏览器 UA + Referer 抓取，解析 <tbody id=tdata> 表格
  - 若 500 网临时不可用，前端会自动回退到同源 data.json / 内置 FALLBACK
"""
import json
import re
import ssl
import datetime
import urllib.request

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
HIST_URL = "https://datachart.500.com/dlt/history/newinc/history.php?start=25001&end=26999"
WK = {'0': '日', '1': '一', '2': '二', '3': '三', '4': '四', '5': '五', '6': '六'}


def fetch_html(url):
    ctx = ssl.create_default_context()
    req = urllib.request.Request(
        url,
        headers={'User-Agent': UA, 'Referer': 'https://datachart.500.com/dlt/'}
    )
    with urllib.request.urlopen(req, timeout=12, context=ctx) as r:
        return r.read().decode('utf-8', 'ignore')


def parse(html):
    m = re.search(r'<tbody[^>]*id=["\']tdata["\'][^>]*>(.*?)</tbody>', html, re.S)
    if not m:
        return []
    rows = re.findall(r'<tr[^>]*>(.*?)</tr>', m.group(1), re.S)
    out = []
    for r in rows:
        tds = [re.sub(r'<[^>]+>', '', t).strip()
               for t in re.findall(r'<td[^>]*>(.*?)</td>', r, re.S)]
        if len(tds) < 16:
            continue
        code = tds[1]
        if not re.fullmatch(r'\d{5}', code):
            continue
        front = tds[2:7]
        back = tds[7:9]
        date = tds[15]
        try:
            w = datetime.datetime.strptime(date, '%Y-%m-%d').strftime('%w')
        except Exception:
            w = ''
        p1 = {
            'count': int((tds[10] or '0').replace(',', '')),
            'money': int((tds[11] or '0').replace(',', ''))
        }
        p2 = {
            'count': int((tds[12] or '0').replace(',', '')),
            'money': int((tds[13] or '0').replace(',', ''))
        }
        out.append({
            'code': code, 'date': date, 'week': WK.get(w, ''),
            'front': front, 'back': back, 'p1': p1, 'p2': p2
        })
    out.sort(key=lambda x: int(x['code']), reverse=True)
    return out[:120]


def _resp(code, body):
    return {
        "isBase64Encoded": False,
        "statusCode": code,
        "headers": {
            "Content-Type": "application/json; charset=utf-8",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET,OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Expose-Headers": "Content-Type"
        },
        "body": json.dumps(body, ensure_ascii=False)
    }


def main_handler(event, context):
    try:
        html = fetch_html(HIST_URL)
        data = parse(html)
        if not data:
            return _resp(502, {"error": "empty"})
    except Exception as e:
        return _resp(502, {"error": str(e)})
    return _resp(200, data)
