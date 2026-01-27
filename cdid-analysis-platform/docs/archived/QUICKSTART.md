# 快速启动指南

## 第一步：安装依赖

```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

## 第二步：部署 Gemini Skill

```bash
# 创建 Gemini skills 目录
mkdir -p ~/.gemini/skills/duofa-panduan

# 复制 skill 文件
cp skills/duofa-panduan/SKILL.md ~/.gemini/skills/duofa-panduan/

# 验证 Gemini CLI
gemini --version
```

## 第三步：启动服务

### 方式一：开发模式（推荐）

```bash
# 同时启动 API Server 和 Worker
./dev.sh
```

### 方式二：分别启动

```bash
# 终端 1：启动 API Server
./start_server.sh

# 终端 2：启动 Worker
./start_worker.sh
```

### 方式三：Docker 部署

```bash
# 构建并启动
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

## 第四步：访问应用

1. **打开浏览器**，访问: http://localhost:8000

2. **用户端功能**:
   - 创建任务：上传 Excel/CSV 文件
   - 查看任务列表
   - 查看任务详情和进度
   - 下载分析报告

3. **管理端功能**:
   - 登录地址: http://localhost:8000/api/admin/auth/login
   - 默认账户: admin / admin123
   - 用户管理、配置管理、任务监控

4. **API 文档**: http://localhost:8000/docs

## 第五步：测试功能

### 创建测试任务

1. 访问首页 http://localhost:8000
2. 填写表单：
   - 任务名称：测试任务
   - 包名：com.test.app
   - 开始日期：2026-01-01
   - 结束日期：2026-01-07
   - 消息类型：dna,daa
3. 上传测试文件（使用 `xuqiu/demo/波克问题数据.csv`）
4. 点击"提交任务"
5. 查看任务详情页，实时跟踪进度
6. 任务完成后下载报告

### 使用管理端

1. 发送 POST 请求登录:
```bash
curl -X POST http://localhost:8000/api/admin/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

2. 获取 access_token 后访问管理端 API:
```bash
curl -X GET http://localhost:8000/api/admin/users \
  -H "Authorization: Bearer <your-token>"
```

3. 或访问 Swagger UI: http://localhost:8000/docs

## 常见问题

### Q: Worker 无法启动？
A: 检查配置文件和日志：
```bash
cat config/config.yaml
tail -f logs/app.log
```

### Q: 任务一直 queued？
A: 确认 Worker 已启动：
```bash
ps aux | grep "src.worker.main"
```

### Q: 报告生成失败？
A: 验证 Gemini CLI：
```bash
gemini --version
gemini skills list | grep duofa-panduan
```

### Q: 无法连接内网 API？
A: 测试内网连接：
```bash
curl http://172.17.129.204:6829/health
```

## 下一步

- 修改默认管理员密码
- 配置生产环境参数（config/config.yaml）
- 设置数据库为 PostgreSQL（生产环境）
- 配置 Nginx 反向代理
- 启用 HTTPS

## 支持

遇到问题请查看：
- `docs/` 目录中的详细文档
- API 文档: http://localhost:8000/docs
- 日志文件: `logs/app.log`
