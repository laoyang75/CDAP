# Web UI 实现说明 - 基于现有原型

**日期**: 2026-01-24
**状态**: 待实施
**参考**: `docs/final-requirements/ui-mockups/`

---

## 📌 重要说明

### ⚠️ 必须遵守的规则

1. **严格参考现有 UI 原型**
   - 所有 UI 实现必须基于 `docs/final-requirements/ui-mockups/` 中的 8 个 HTML 文件
   - 不要自己重新设计界面布局
   - 保持与原型一致的视觉风格和交互逻辑

2. **界面语言必须是中文**
   - 所有页面标题、按钮、表单标签都使用中文
   - 所有提示信息、错误消息使用中文
   - 所有导航菜单使用中文

3. **保留原型的样式设计**
   - 导航栏背景色：`#2c3e50`
   - 主色调：蓝色系 (`#3498db`, `#2980b9`)
   - 卡片阴影：`box-shadow: 0 2px 4px rgba(0,0,0,0.1)`
   - 文件上传拖拽区域的交互效果

---

## 📋 UI 原型清单

### 用户界面（3 个页面）

#### 1. user-create-task.html - 创建任务页
**路径**: `docs/final-requirements/ui-mockups/user-create-task.html`

**关键元素**：
```html
<!-- 导航栏 -->
<nav class="navbar" style="background-color: #2c3e50">
  <a class="navbar-brand">
    <i class="bi bi-graph-up-arrow"></i> CDID 数据分析平台
  </a>
  <ul class="navbar-nav">
    <li><a href="...">创建任务</a></li>
    <li><a href="...">我的任务</a></li>
  </ul>
</nav>

<!-- 页面标题 -->
<h2><i class="bi bi-file-earmark-plus"></i> 创建分析任务</h2>
<p class="text-muted">上传 CDID 文件，选择分析管线...</p>

<!-- 表单字段 -->
<form id="createTaskForm">
  <!-- 任务名称 -->
  <label class="required">任务名称</label>
  <input type="text" name="name" required>

  <!-- 客户名称（带自动完成） -->
  <label class="required">客户名称</label>
  <input type="text" name="client_name" list="clientList">
  <datalist id="clientList"></datalist>
  <small class="text-muted">开始输入以检索客户</small>

  <!-- 应用包名（自动填充） -->
  <label class="required">应用包名</label>
  <input type="text" name="package_name" readonly>
  <small class="text-muted">根据客户名称自动填充</small>

  <!-- 分析管线 -->
  <label class="required">分析管线</label>
  <select name="pipeline_id" required>
    <option value="">请选择管线...</option>
  </select>

  <!-- 时间范围 -->
  <div class="row">
    <div class="col">
      <label class="required">开始日期</label>
      <input type="date" name="start_date" required>
    </div>
    <div class="col">
      <label class="required">结束日期</label>
      <input type="date" name="end_date" required>
    </div>
  </div>

  <!-- 数据类型 -->
  <label>数据类型</label>
  <div class="form-check">
    <input type="checkbox" id="msgDna" value="dna">
    <label for="msgDna">DNA</label>
  </div>
  <div class="form-check">
    <input type="checkbox" id="msgDaa" value="daa">
    <label for="msgDaa">DAA</label>
  </div>

  <!-- 文件上传（拖拽区域） -->
  <label class="required">CDID 文件</label>
  <div class="file-upload-area" id="fileUploadArea">
    <i class="bi bi-cloud-upload" style="font-size: 48px"></i>
    <p>拖拽文件到此处，或点击选择文件</p>
    <input type="file" id="fileInput" accept=".csv,.txt" hidden>
    <small class="text-muted">支持 CSV 格式</small>
  </div>

  <!-- 提交按钮 -->
  <button type="submit" class="btn btn-primary btn-lg">
    <i class="bi bi-play-circle"></i> 创建任务
  </button>
</form>
```

**交互逻辑（JavaScript）**：
```javascript
// 1. 加载客户列表并填充 datalist
// 2. 客户名称输入时自动填充包名
// 3. 加载活跃管线列表
// 4. 文件拖拽上传
// 5. 表单提交后显示成功提示并跳转
```

---

#### 2. user-task-list.html - 任务列表页
**路径**: `docs/final-requirements/ui-mockups/user-task-list.html`

**关键元素**：
```html
<!-- 页面标题 -->
<h2><i class="bi bi-list-check"></i> 我的任务</h2>

<!-- 筛选区域 -->
<div class="filter-section">
  <div class="row">
    <div class="col">
      <label>状态筛选</label>
      <select id="statusFilter">
        <option value="">全部状态</option>
        <option value="queued">排队中</option>
        <option value="fetching">获取数据中</option>
        <option value="analyzing">分析中</option>
        <option value="reporting">生成报告中</option>
        <option value="done">已完成</option>
        <option value="failed">失败</option>
      </select>
    </div>
    <div class="col">
      <label>管线筛选</label>
      <select id="pipelineFilter">
        <option value="">全部管线</option>
      </select>
    </div>
    <div class="col">
      <label>搜索</label>
      <input type="text" id="searchInput" placeholder="搜索任务名称或客户...">
    </div>
  </div>
</div>

<!-- 任务表格 -->
<table class="table table-hover">
  <thead>
    <tr>
      <th>任务名称</th>
      <th>客户名称</th>
      <th>管线</th>
      <th>状态</th>
      <th>进度</th>
      <th>创建时间</th>
      <th>操作</th>
    </tr>
  </thead>
  <tbody>
    <!-- 任务行示例 -->
    <tr onclick="location.href='user-task-detail.html?id=xxx'">
      <td>12月数据分析</td>
      <td>示例客户A</td>
      <td>多发检测</td>
      <td>
        <span class="badge status-analyzing">分析中</span>
      </td>
      <td>
        <div class="progress">
          <div class="progress-bar" style="width: 65%"></div>
        </div>
        <small>65%</small>
      </td>
      <td>2026-01-24 10:30</td>
      <td>
        <button class="btn btn-sm btn-danger" onclick="deleteTask(event, 'xxx')">
          <i class="bi bi-trash"></i>
        </button>
      </td>
    </tr>
  </tbody>
</table>
```

**状态徽章样式**：
```css
.status-queued { background-color: #95a5a6; }
.status-fetching { background-color: #3498db; }
.status-analyzing { background-color: #f39c12; }
.status-reporting { background-color: #9b59b6; }
.status-done { background-color: #27ae60; }
.status-failed { background-color: #e74c3c; }
```

---

#### 3. user-task-detail.html - 任务详情页
**路径**: `docs/final-requirements/ui-mockups/user-task-detail.html`

**关键元素**：
```html
<!-- 页面标题 -->
<h2><i class="bi bi-file-text"></i> 任务详情</h2>

<!-- 基本信息卡片 -->
<div class="card">
  <div class="card-header">
    <h5>基本信息</h5>
  </div>
  <div class="card-body">
    <div class="row">
      <div class="col-md-6">
        <p><strong>任务名称：</strong>12月数据分析</p>
        <p><strong>客户名称：</strong>示例客户A</p>
        <p><strong>应用包名：</strong>com.example.app</p>
      </div>
      <div class="col-md-6">
        <p><strong>分析管线：</strong>多发检测</p>
        <p><strong>时间范围：</strong>2026-01-01 至 2026-01-07</p>
        <p><strong>创建时间：</strong>2026-01-24 10:30</p>
      </div>
    </div>
    <div class="mt-3">
      <span class="badge status-done">已完成</span>
      <div class="progress mt-2">
        <div class="progress-bar bg-success" style="width: 100%"></div>
      </div>
    </div>
  </div>
</div>

<!-- 执行流程时间轴 -->
<div class="card mt-4">
  <div class="card-header">
    <h5>执行流程</h5>
  </div>
  <div class="card-body">
    <div class="timeline">
      <div class="timeline-item completed">
        <div class="timeline-marker"></div>
        <div class="timeline-content">
          <h6>获取数据</h6>
          <p>已完成 - 2026-01-24 10:32</p>
        </div>
      </div>
      <div class="timeline-item completed">
        <div class="timeline-marker"></div>
        <div class="timeline-content">
          <h6>数据分析</h6>
          <p>已完成 - 2026-01-24 10:35</p>
        </div>
      </div>
      <div class="timeline-item completed">
        <div class="timeline-marker"></div>
        <div class="timeline-content">
          <h6>生成报告</h6>
          <p>已完成 - 2026-01-24 10:37</p>
        </div>
      </div>
    </div>
  </div>
</div>

<!-- 报告展示 -->
<div class="card mt-4">
  <div class="card-header d-flex justify-content-between">
    <h5>分析报告</h5>
    <div>
      <a href="/jobs/xxx/raw-data" class="btn btn-sm btn-outline-primary">
        <i class="bi bi-file-earmark-excel"></i> 下载原始数据
      </a>
      <a href="/jobs/xxx/report" class="btn btn-sm btn-primary">
        <i class="bi bi-file-earmark-text"></i> 下载报告
      </a>
    </div>
  </div>
  <div class="card-body">
    <iframe id="reportFrame" style="width: 100%; height: 800px; border: none;"></iframe>
  </div>
</div>
```

---

### 管理界面（5 个页面）

#### 4. admin-pipeline-management.html - 管线管理
**路径**: `docs/final-requirements/ui-mockups/admin-pipeline-management.html`

**关键特性**：
- 卡片式管线展示
- 添加/编辑管线弹窗
- 配置：脚本目录、脚本文件、Skill 名称
- 激活/停用管线

---

#### 5. admin-script-editor.html - 脚本编辑
**路径**: `docs/final-requirements/ui-mockups/admin-script-editor.html`

**关键特性**：
- 文件树浏览器（左侧）
- 代码编辑器（右侧，可使用 CodeMirror 或 Monaco）
- 保存按钮
- Skill 引用配置（下拉选择，不支持新建）

---

#### 6. admin-client-config.html - 客户配置
**路径**: `docs/final-requirements/ui-mockups/admin-client-config.html`

**关键特性**：
- 客户列表表格（可搜索）
- 添加/编辑客户弹窗
- 批量导入按钮（CSV/Excel）
- 客户-包名映射管理

---

#### 7. admin-user-management.html - 用户管理
**路径**: `docs/final-requirements/ui-mockups/admin-user-management.html`

**关键特性**：
- 用户列表表格
- 添加/删除用户
- 权限展示（只读，对接现有接口）

---

#### 8. admin-task-monitoring.html - 任务监控
**路径**: `docs/final-requirements/ui-mockups/admin-task-monitoring.html`

**关键特性**：
- 所有用户任务汇总
- 失败任务列表（高优先级显示）
- 系统错误日志查看器
- 实时刷新

---

## 🎨 通用样式规范

### 色彩方案（从原型提取）
```css
/* 主色调 */
--primary-color: #3498db;
--primary-hover: #2980b9;
--navbar-bg: #2c3e50;

/* 状态色 */
--status-queued: #95a5a6;
--status-fetching: #3498db;
--status-analyzing: #f39c12;
--status-reporting: #9b59b6;
--status-done: #27ae60;
--status-failed: #e74c3c;

/* 背景色 */
--body-bg: #f8f9fa;
--card-bg: #ffffff;
```

### 字体和间距
```css
body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Microsoft YaHei', sans-serif;
    background-color: #f8f9fa;
}

.form-label {
    font-weight: 500;
    color: #495057;
}

.required::after {
    content: " *";
    color: #e74c3c;
}
```

### 卡片样式
```css
.card {
    border: none;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    border-radius: 8px;
}
```

---

## 🔧 JavaScript 交互规范

### 1. 客户名称自动完成
```javascript
// 从 /clients API 加载客户列表
const clientPackageMap = {};

fetch('/clients')
  .then(res => res.json())
  .then(data => {
    data.clients.forEach(client => {
      // 填充 datalist
      const option = document.createElement('option');
      option.value = client.client_name;
      clientList.appendChild(option);

      // 建立映射
      clientPackageMap[client.client_name] = client.package_name;
    });
  });

// 监听输入，自动填充包名
clientNameInput.addEventListener('input', function() {
  const clientName = this.value.trim();
  if (clientPackageMap[clientName]) {
    packageNameInput.value = clientPackageMap[clientName];
  }
});
```

### 2. 文件拖拽上传
```javascript
const uploadArea = document.getElementById('fileUploadArea');
const fileInput = document.getElementById('fileInput');

// 点击区域触发文件选择
uploadArea.addEventListener('click', () => fileInput.click());

// 拖拽事件
uploadArea.addEventListener('dragover', (e) => {
  e.preventDefault();
  uploadArea.classList.add('dragover');
});

uploadArea.addEventListener('dragleave', () => {
  uploadArea.classList.remove('dragover');
});

uploadArea.addEventListener('drop', (e) => {
  e.preventDefault();
  uploadArea.classList.remove('dragover');
  const files = e.dataTransfer.files;
  if (files.length > 0) {
    fileInput.files = files;
    // 显示文件名
  }
});
```

### 3. 任务列表实时刷新
```javascript
// 每 5 秒刷新一次任务列表
setInterval(() => {
  fetch('/jobs')
    .then(res => res.json())
    .then(data => {
      updateTaskTable(data.jobs);
    });
}, 5000);
```

---

## 📦 实现步骤

### Step 1: 创建基础模板
```python
# src/ui/templates/base.html
# 参考 user-create-task.html 的导航栏和整体结构
```

### Step 2: 转换 HTML 原型为 Jinja2 模板
```python
# 将静态 HTML 转换为动态模板
# 保留所有样式和交互逻辑
# 使用 Jinja2 语法动态填充数据
```

### Step 3: 提取公共 CSS
```python
# src/ui/static/css/main.css
# 从原型中提取样式到独立 CSS 文件
```

### Step 4: 提取公共 JavaScript
```python
# src/ui/static/js/common.js
# 提取通用函数（API 调用、提示框等）

# src/ui/static/js/create_task.js
# 页面特定逻辑
```

### Step 5: 注册路由
```python
# src/api/main.py
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app.mount("/ui/static", StaticFiles(directory="src/ui/static"), name="static")
templates = Jinja2Templates(directory="src/ui/templates")

@app.get("/ui")
async def ui_home(request: Request):
    return templates.TemplateResponse("create_task.html", {"request": request})

@app.get("/ui/jobs")
async def ui_task_list(request: Request):
    return templates.TemplateResponse("task_list.html", {"request": request})

# ... 其他路由
```

---

## ✅ 验收标准

实现完成后，必须满足：

1. **视觉一致性**
   - [ ] 导航栏颜色和布局与原型一致
   - [ ] 卡片阴影和圆角与原型一致
   - [ ] 按钮样式和颜色与原型一致
   - [ ] 状态徽章颜色与原型一致

2. **功能完整性**
   - [ ] 客户名称自动完成工作正常
   - [ ] 包名自动填充工作正常
   - [ ] 文件拖拽上传工作正常
   - [ ] 任务列表筛选工作正常
   - [ ] 实时进度条更新正常
   - [ ] 报告展示（iframe）工作正常
   - [ ] 下载按钮工作正常

3. **中文界面**
   - [ ] 所有页面标题是中文
   - [ ] 所有按钮文字是中文
   - [ ] 所有表单标签是中文
   - [ ] 所有提示信息是中文
   - [ ] 所有错误消息是中文

4. **交互体验**
   - [ ] 表单验证提示清晰
   - [ ] 成功/失败提示显示正常
   - [ ] 页面跳转逻辑正确
   - [ ] 响应式布局在不同屏幕尺寸下正常

---

## 🚫 常见错误（避免）

1. ❌ **不要重新设计界面**
   - 必须严格按照原型实现
   - 不要改变布局结构
   - 不要改变颜色方案

2. ❌ **不要使用英文文案**
   - 所有用户可见的文字必须是中文
   - 包括占位符（placeholder）

3. ❌ **不要忽略交互细节**
   - 文件拖拽的视觉反馈
   - 表单验证的提示
   - 加载状态的显示

4. ❌ **不要破坏响应式布局**
   - 保留 Bootstrap 的网格系统
   - 测试不同屏幕尺寸

---

**总结**: 严格参考 `docs/final-requirements/ui-mockups/` 中的 8 个 HTML 原型，保持视觉一致性和功能完整性，确保所有界面元素使用中文。
