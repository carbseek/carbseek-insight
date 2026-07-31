# CarbSeek Insight 部署文档

碳产业研发情报驾驶舱。整体由三部分组成：

```
├── 静态前端（根目录 *.html + data/*.json）   → GitHub Pages 托管
├── server/   Express + SQLite 后端 API        → 本地/服务器常驻运行
└── admin/    Vite + React 管理后台 SPA        → 构建后由后端 /admin 路径托管
```

---

## 1. 环境要求

- Node.js **≥ 22.13**（后端使用内置 `node:sqlite`，无需安装数据库；本机验证版本 v22.23.1）
- npm（随 Node 安装）
- Windows 可直接使用仓库自带的 `deploy.bat` / `auto_update.bat`

## 2. 后端服务（server/）

### 2.1 安装与配置

```bash
cd server
npm install
cp .env.example .env   # Windows: copy .env.example .env
```

编辑 `server/.env`：

| 变量 | 说明 | 默认值 |
|---|---|---|
| `PORT` | 服务端口 | `3001` |
| `JWT_SECRET` | JWT 签名密钥，**生产必须改成随机长字符串** | `dev-only-insecure-secret` |
| `ADMIN_USERNAME` | 初始管理员用户名 | `admin` |
| `ADMIN_PASSWORD` | 兜底管理员密码（仅当 users 表中无该用户时生效） | `changeme` |
| `ADMIN_INITIAL_PASSWORD` | 首次启动播种 users 表时的初始密码 | `admin123` |

### 2.2 数据库

- 数据库文件：`server/data/carbseek.db`（首次启动自动创建，schema 见 `server/db/schema.sql`）
- **users 表**：首次启动时若不存在 admin 用户，自动播种 `admin` / `admin123`（scrypt 哈希存储）。
  生产部署请登录后立即修改密码，或事先设置 `ADMIN_INITIAL_PASSWORD`。
- `carbseek.db`、`-shm`、`-wal` 均在 `.gitignore` 中，不会提交到仓库。

### 2.3 启动

```bash
cd server
npm start        # node --env-file=.env index.js
# 或开发模式（文件变更自动重启）
npm run dev
```

验证：

```bash
curl http://localhost:3001/api/health
# {"ok":true}

curl -X POST http://localhost:3001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
# {"token":"<JWT>","expires_in":"7d"}
```

### 2.4 主要 API

| 接口 | 鉴权 | 说明 |
|---|---|---|
| `POST /api/auth/login` | 无 | 登录，返回 JWT（7 天有效） |
| `GET /api/dashboard` | 无 | 首页聚合数据 |
| `GET /api/evidence` `/api/opportunities` `/api/radar-items` 等 | 无 | 公开读取，支持筛选参数 |
| `POST/PUT/DELETE /api/<entity>` | Bearer | 增删改（evidence、opportunities、radar_items、policies、articles、competitors、trends、recommendations、reports、intel-center） |
| `POST /api/admin/export` | Bearer | 将 SQLite 导出回 `data/*.json` |

写操作请求头需携带：`Authorization: Bearer <login 返回的 token>`。

### 2.5 数据同步（SQLite ↔ JSON）

静态站点以 `data/*.json` 为唯一真相源，后端提供双向同步：

```bash
cd server
npm run import   # data/*.json → SQLite
npm run export   # SQLite → data/*.json（也可 POST /api/admin/export）
```

后台改完数据 → 调用 export → `git commit && push` → GitHub Pages 自动更新。

## 3. 管理后台（admin/）

```bash
cd admin
npm install
npm run dev      # 本地开发（Vite，默认代理到 :3001）
npm run build    # 产出 admin/dist/
```

构建后后端会自动把 `admin/dist/` 挂载到 `http://localhost:3001/admin`，
用 admin 账号登录即可在线维护证据库、机会库、雷达、周报等数据。

## 4. 静态站点部署（GitHub Pages）

1. 仓库：https://github.com/carbseek/carbseek-insight （分支 `master`）
2. Settings → Pages → Source 选择 **GitHub Actions**（工作流见 `.github/workflows/`）
3. 推送后 1-2 分钟访问 `https://carbseek.github.io/carbseek-insight/`

详细步骤与其他托管方式（Netlify / Vercel / 自定义域名）见 [DEPLOY.md](DEPLOY.md)。

## 5. 每周自动更新

`auto_update.bat` / `scheduler.bat`（Windows 计划任务，每周一 08:17）：
采集情报 → 更新 `data/*.json` → 生成周报 → commit & push。

## 6. 生产部署清单

- [ ] `.env` 中设置强随机 `JWT_SECRET`（如 `node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"`）
- [ ] 修改默认管理员密码（不要长期使用 `admin123`）
- [ ] 用反向代理（Nginx/Caddy）为后端启用 HTTPS，并将 CORS `Access-Control-Allow-Origin` 收紧到站点域名
- [ ] 定期备份 `server/data/carbseek.db`
- [ ] 用进程管理器常驻运行，如 `pm2 start index.js --name carbseek-insight --cwd server`

## 7. 故障排查

| 现象 | 处理 |
|---|---|
| 启动报 `node:sqlite` 找不到 | Node 版本过低，升级到 ≥ 22.13 |
| 登录返回 401 | 确认 users 表中有该用户；或删掉 `carbseek.db` 重启重新播种 |
| 端口被占用 | 改 `.env` 中 `PORT` |
| 后台页面 404 | 先在 `admin/` 执行 `npm run build` |
