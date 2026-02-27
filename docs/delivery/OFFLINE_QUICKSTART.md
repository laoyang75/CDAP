# 历史线下快速上手（归档）

> 来源：`delivery/cdid-analysis-platform/docs/QUICKSTART.md`

# 快速上手（10 分钟跑通）

## 0) 前置

- Python 3.9+
- 已安装 Gemini CLI（命令 `gemini --version` 可用）

## 1) 安装依赖

在 `delivery/cdid-analysis-platform/` 目录执行：

```bash
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
```

## 2) 配置（最少改 2 个点）

编辑 `config/config.yaml`：

- `gemini.model`：设置为你当前可用的模型（示例：`gemini-3-flash-preview`）
- （可选）标准模式需要内网时：确认 `upstream.base_url` 可达

## 3) 启动（唯一入口）

```bash
./venv/bin/python launcher_web.py
```

打开启动器：`http://localhost:5555`，点击“启动服务”。

## 4) 用“调试模式”最快跑通一次

1) 打开用户端：`http://localhost:8000/create`
2) 勾选“调试模式”
3) 上传一个已下载好的 `raw_data.xlsx`
4) 选择至少一个管线，提交创建任务
5) 在 `http://localhost:8000/tasks` 查看进度，完成后点进详情页可直接预览报告

## 5) 常用入口

- 我的任务：`http://localhost:8000/tasks`
- 管理后台：`http://localhost:8000/admin`

默认管理员：
- 用户名：`admin`
- 密码：`admin123`

