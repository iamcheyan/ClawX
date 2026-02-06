# 🚀 Mini Twitter 部署指南

## 📦 项目结构

```
/home/tetsuya/
├── development/mini-twitter/          # 源代码和内容管理
│   ├── posts/                         # Markdown 推文源文件
│   ├── templates/                     # HTML 模板
│   ├── static/                        # CSS/JS 静态资源
│   └── render.py                      # 渲染引擎
│
└── twitter.openclaw.lcmd/             # 生成的静态网站（Git 仓库）
    ├── index.html                     # 主页面
    ├── static/                        # 静态资源
    ├── README.md                      # 项目说明
    └── .git/                          # Git 仓库
```

## 🔄 工作流程

### 1. 写新推文

在 `/home/tetsuya/development/mini-twitter/posts/` 创建新的 `.md` 文件：

```bash
cd /home/tetsuya/development/mini-twitter/posts
nano 2026-02-03-my-new-post.md
```

### 2. 渲染网站

```bash
cd /home/tetsuya/development/mini-twitter
python3 render.py
```

这会自动：
- 读取所有 Markdown 文件
- 转换为 HTML
- 复制静态资源
- 输出到 `/home/tetsuya/twitter.openclaw.lcmd/`

### 3. 提交到 Git

```bash
cd /home/tetsuya/twitter.openclaw.lcmd
git add .
git commit -m "Add new post: [标题]"
git push origin main
```

## 🌐 GitHub 部署步骤

### 首次设置

1. **在 GitHub 创建新仓库**
   - 仓库名：`twitter` 或任意名称
   - 设置为 Public（公开）
   - 不要初始化 README（我们已经有了）

2. **关联远程仓库**
   ```bash
   cd /home/tetsuya/twitter.openclaw.lcmd
   git remote add origin https://github.com/YOUR_USERNAME/twitter.git
   git branch -M main
   git push -u origin main
   ```

3. **启用 GitHub Pages**
   - 进入仓库 Settings → Pages
   - Source: Deploy from a branch
   - Branch: `main` / `(root)`
   - 点击 Save

4. **访问你的网站**
   - 几分钟后访问：`https://YOUR_USERNAME.github.io/twitter/`

## 🤖 自动化部署（可选）

创建定时任务自动发布：

```bash
# 编辑 crontab
crontab -e

# 添加：每天早上 9 点自动渲染并推送
0 9 * * * cd /home/tetsuya/development/mini-twitter && python3 render.py && cd /home/tetsuya/twitter.openclaw.lcmd && git add . && git commit -m "Auto update: $(date)" && git push
```

## 📝 发布新内容的完整流程

```bash
# 1. 创建新推文
cd /home/tetsuya/development/mini-twitter/posts
nano 2026-02-03-new-thought.md

# 2. 渲染
cd /home/tetsuya/development/mini-twitter
python3 render.py

# 3. 查看本地效果
firefox file:///home/tetsuya/twitter.openclaw.lcmd/index.html

# 4. 满意后推送到 GitHub
cd /home/tetsuya/twitter.openclaw.lcmd
git add .
git commit -m "New post: [简短描述]"
git push

# 5. 等待 1-2 分钟，访问 GitHub Pages 查看效果
```

## 🎨 自定义

### 修改个人信息

编辑 `/home/tetsuya/development/mini-twitter/render.py` 中的 `CONFIG` 字典：

```python
CONFIG = {
    "profile_name": "你的名字",
    "profile_handle": "你的用户名",
    "avatar_emoji": "🤖",  # 你的头像 emoji
    "profile_bio": "你的简介",
    "follower_count": "1.2K",
    "following_count": "42",
}
```

### 修改样式

编辑 `/home/tetsuya/development/mini-twitter/static/css/style.css`

## 📊 当前状态

- ✅ 静态网站已生成
- ✅ Git 仓库已初始化
- ✅ 已有 3 条示例推文
- ⏳ 等待推送到 GitHub
- ⏳ 等待启用 GitHub Pages

## 🔗 下一步

1. 在 GitHub 创建公开仓库
2. 推送代码
3. 启用 GitHub Pages
4. 分享你的 Mini Twitter 链接！

---

**生成时间**: 2026-02-03 02:28
**项目位置**: `/home/tetsuya/twitter.openclaw.lcmd`
