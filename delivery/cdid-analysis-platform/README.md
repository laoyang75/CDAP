# CDID 数据分析平台（交付包）

本目录为“可交付版本”，只保留一个启动入口：`launcher_web.py`。

## 启动

1) 安装依赖（推荐 venv）
```bash
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
```

2) 启动（唯一入口）
```bash
./venv/bin/python launcher_web.py
```

3) 打开启动器：`http://localhost:5555`，点击“启动服务”

## 访问

- 用户端：`http://localhost:8000`
  - 创建任务：`/create`
  - 我的任务：`/tasks`
- 管理后台：`http://localhost:8000/admin`

默认管理员：
- 用户名：`admin`
- 密码：`admin123`

## 文档

- 快速上手：`docs/QUICKSTART.md`
- 接手说明：`docs/HANDOFF.md`
- 交付检查：`docs/DELIVERY_CHECKLIST.md`
