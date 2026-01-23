---
name: insight
description: 上传 CDID 文件到远程服务，获取 DNA/DAA 详情数据。当用户需要查询设备指纹详情时使用。
user_invokable: true
version: v1.1.2
---

# 数据洞察服务 - 获取设备详情

上传包含 CDID 列表的文件，调用远程服务获取对应的 DNA/DAA 详情数据。

API 地址: http://172.17.129.204:6829

## 输入文件格式

上传的 Excel 文件需包含 CDID 列：

| cdid |
|------|
| abc123 |
| def456 |

> 文件可包含其他列，但必须有 cdid 列。如果用户上传的是 csv 格式，不要做格式转换，后端也支持 CSV 格式。

## 接口说明

### 1. 创建任务

**请求**
```
POST /api/statistical-analysis/v1/task/create
Content-Type: multipart/form-data
```

**参数**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | string | 是 | 任务名称 |
| package_name | string | 是 | 包名 |
| file | file | 是 | 包含 CDID 列表的 csv 文件 |
| start | string | 是 | 开始日期 YYYY-MM-DD |
| end | string | 是 | 结束日期 YYYY-MM-DD |
| message | string | 否 | 数据类型 dna/daa，可多选 |

**示例**
```bash
curl -X POST http://172.17.129.204:6829/api/statistical-analysis/v1/task/create \
  -F "name=测试任务" \
  -F "package_name=com.example.app" \
  -F "file=@./cdid_list.csv" \
  -F "message=dna" \
  -F "message=daa"
```

**返回**
```json
{"code":0,"message":"success","data":{"task_id":"1234567890"}}
```

### 2. 查询任务列表

**请求**
```
POST /api/statistical-analysis/v1/task/list
Content-Type: application/json
```

**参数**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | int | 是 | 页码 |
| limit | int | 是 | 每页数量 |
| name | string | 否 | 任务名称（模糊匹配） |
| status | string | 否 | 状态: pending/running/success/failed |
| package_name | string | 否 | 包名（模糊匹配） |

**示例**
```bash
curl -X POST http://172.17.129.204:6829/api/statistical-analysis/v1/task/list \
  -H "Content-Type: application/json" \
  -d '{"page":1,"limit":10}'
```

**返回**
```json
{
  "code": 0,
  "message": "success",
  "count": 100,
  "data": [
    {
      "id": "1234567890",
      "name": "测试任务",
      "status": "success",
      "package_name": "com.example.app",
      "time_range": ["2025-01-01", "2025-01-07"],
      "message": ["dna", "daa"],
      "created_at": "2025-01-04 15:30:00",
      "creator_name": "张三",
      "url": "https://..."
    }
  ]
}
```

### 3. 查询任务详情

**请求**
```
GET /api/statistical-analysis/v1/task/detail?task_id=xxx
```

**示例**
```bash
curl "http://172.17.129.204:6829/api/statistical-analysis/v1/task/detail?task_id=1234567890"
```

**返回**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "task_id": "1234567890",
    "name": "测试任务",
    "status": "success",
    "package_name": "com.example.app",
    "start": "2025-01-01",
    "end": "2025-01-07",
    "file_path": "result.xlsx",
    "oss_url": "https://bucket.oss.com/path/result.xlsx",
    "created_at": "2025-01-04 15:30:00",
    "updated_at": "2025-01-04 16:00:00"
  }
}
```

## 输出结果

任务完成后返回包含 DNA/DAA 详情的 Excel 文件，包含 cdid、did、oaid、idfa、imei、android_id、rc_rules、rc_scenes 等字段。

注意：这个任务可能耗时很久，你需要，每隔一分钟去查询一次任务的状态，当任务成功后，通过 oss_url 下载数据文件，然后使用 analyzer skill 进行多发/碰撞/风险检测。


## 使用说明

根据用户需求使用 Bash 工具执行 curl 命令调用相应接口。

- 创建任务时，文件路径使用用户提供的本地路径
- 查询列表时，根据用户描述构造合适的查询参数
- 查询详情可获取完整的 OSS 下载地址
