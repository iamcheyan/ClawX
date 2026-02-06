#!/usr/bin/env python3
"""
Mini Twitter 本地预览服务器
"""
import os
from flask import Flask, send_from_directory

# 设置静态网站目录（即生成的 HTML 所在的目录）
STATIC_SITE_DIR = "/home/tetsuya/twitter.openclaw.lcmd"

app = Flask(__name__)

@app.route('/')
def index():
    return send_from_directory(STATIC_SITE_DIR, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(STATIC_SITE_DIR, path)

if __name__ == '__main__':
    print(f"🚀 Mini Twitter Preview Server running...")
    print(f"📂 Serving: {STATIC_SITE_DIR}")
    print(f"🌍 URL: http://0.0.0.0:5000")
    # 监听 0.0.0.0 以便从外部访问
    app.run(host='0.0.0.0', port=5000, debug=False)
