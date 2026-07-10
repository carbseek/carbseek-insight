# CarbSeek Insight 部署指南

## 🚀 方式一：GitHub Pages（推荐，免费永久在线）

### 步骤 1：在 GitHub 创建仓库
1. 打开 https://github.com/new
2. Repository name 填写：`carbseek-insight`
3. 选择 **Public**（Public 才能免费使用 GitHub Pages）
4. 点击 **Create repository**

### 步骤 2：推送代码

在本地终端执行以下命令：

```bash
cd C:/Users/lipen/Documents/Kimi/Workspaces/carbseek/carbseek-os/insight

# 添加远程仓库（替换 YOUR_USERNAME 为你的 GitHub 用户名）
git remote add origin https://github.com/YOUR_USERNAME/carbseek-insight.git

# 推送代码
git branch -M main
git push -u origin main
```

### 步骤 3：启用 GitHub Pages
1. 打开仓库页面：https://github.com/YOUR_USERNAME/carbseek-insight
2. 点击 **Settings** → 左侧 **Pages**
3. Source 选择 **Deploy from a branch**
4. Branch 选择 **main** / **root**
5. 点击 **Save**

### 步骤 4：访问站点

等待 1-2 分钟后，访问：

```
https://YOUR_USERNAME.github.io/carbseek-insight/
```

🎉 完成！你的情报驾驶舱已上线。

---

## 🚀 方式二：Netlify Drop（最快，30秒搞定）

### 步骤 1：打包文件
将 `carbseek-os/insight` 目录下的所有文件打包成 zip。

### 步骤 2：拖拽上传
1. 打开 https://app.netlify.com/drop
2. 将 zip 文件直接拖拽到网页上
3. 自动部署完成，获得一个随机域名

### 步骤 3：设置自定义域名（可选）
在 Netlify 设置中配置你的自定义域名，如 `insight.carbseek.com`。

---

## 🚀 方式三：Vercel（适合技术团队）

### 步骤 1：导入 GitHub 仓库
1. 打开 https://vercel.com/new
2. 导入你的 GitHub 仓库
3. Framework Preset 选择 **Other**
4. Root Directory 设置为 `/`（因为 index.html 在根目录）
5. 点击 **Deploy**

---

## 📁 文件结构说明

```
index.html                  ← 首页（本周产业雷达）
industry-*.html            ← 四个行业页
evidence.html              ← 证据库
opportunities.html         ← 机会库
data/                      ← JSON 数据文件
scripts/insight_engine.py  ← 情报采集引擎
```

---

## 🔄 后续更新

每次更新数据后，执行：

```bash
git add .
git commit -m "update: WR-2026-W29"
git push
```

GitHub Pages 会自动重新部署。

---

## 🌐 自定义域名（可选）

### GitHub Pages 自定义域名
1. 在仓库根目录创建 `CNAME` 文件，内容为你想要的域名，如：
   ```
   insight.carbseek.com
   ```
2. 在你的域名 DNS 设置中添加 CNAME 记录指向 `YOUR_USERNAME.github.io`
3. 在 GitHub Pages 设置中确认自定义域名

---

**推荐**：先用 **方式一 GitHub Pages** 部署，稳定后再绑定自定义域名。
