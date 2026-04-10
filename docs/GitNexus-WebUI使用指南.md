# GitNexus Web UI 使用指南

> **适用版本**: GitNexus v1.5.3  
> **文档更新**: 2025年4月10日

---

## 📋 目录

1. [快速启动](#快速启动)
2. [访问Web UI](#访问web-ui)
3. [功能概览](#功能概览)
4. [详细操作指南](#详细操作指南)
5. [常见问题](#常见问题)

---

## 快速启动

### 前置条件

- ✅ GitNexus已成功构建
- ✅ 已索引至少一个代码库
- ✅ Node.js >= 20.0.0

---

### 步骤1: 启动GitNexus API服务器

**在项目根目录执行**：

```bash
cd /home/lmm/github_test/GitNexus

# 启动API服务器（后台运行）
nohup node gitnexus/dist/cli/index.js serve --host 0.0.0.0 --port 4747 > /tmp/gitnexus-server.log 2>&1 &
```

**验证服务器启动成功**：

```bash
# 等待2-3秒
sleep 3

# 检查日志
tail -10 /tmp/gitnexus-server.log
```

**预期输出**：
```
MCP HTTP endpoints mounted at /api/mcp
GitNexus server running on http://localhost:4747
```

**测试API**：

```bash
curl http://localhost:4747/api/repos
```

**预期返回**（JSON格式）：
```json
{
  "repos": [
    {
      "name": "GitNexus",
      "path": "/home/lmm/github_test/GitNexus",
      "symbolCount": 4138,
      "relationshipCount": 9364
    }
  ]
}
```

---

### 步骤2: 启动Web UI

**安装Web UI依赖（首次运行）**：

```bash
cd gitnexus-web
npm install
```

**启动Web UI开发服务器**：

```bash
# 后台运行
nohup npm run dev > /tmp/gitnexus-web.log 2>&1 &
```

**验证Web UI启动成功**：

```bash
# 等待5秒
sleep 5

# 检查日志
tail -20 /tmp/gitnexus-web.log
```

**预期输出**：
```
VITE v5.4.21  ready in 2015 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

---

## 访问Web UI

### 在浏览器中打开

**方式1: localhost（推荐）**

```
http://localhost:5173
```

**方式2: 使用IP地址（备用）**

如果localhost不工作，使用WSL IP：

```bash
# 获取WSL IP
hostname -I
# 假设输出: 7.249.216.24 ...

# 在浏览器访问
http://7.249.216.24:5173
```

---

### WSL2镜像网络模式访问

在WSL2镜像网络模式下，Windows和WSL共享同一个网络命名空间，因此：

- ✅ 可以直接使用 `localhost`
- ✅ 可以使用WSL的IP地址
- ✅ 无需额外网络配置

---

## 功能概览

### 界面布局

```
┌────────────────────────────────────────────────────────────────┐
│  GitNexus - 代码库图可视化                        [设置] [帮助] │
├──────────────┬─────────────────────────────────┬───────────────┤
│              │                                 │               │
│  📂 文件树    │      📊 WebGL图可视化画布        │   💬 AI聊天   │
│              │                                 │               │
│  🔍 搜索框    │    ┌──────┐      ┌──────┐     │               │
│              │    │ 节点1│──────│ 节点2│     │  选择LLM提供商  │
│  ├─ src/     │    └──────┘      └──────┘     │               │
│  ├─ core/    │         │                       │  输入API Key   │
│  └─ cli/     │    ┌────▼────┐                 │               │
│              │    │  节点3  │                 │  输入问题...   │
│              │    └─────────┘                 │               │
│              │                                 │               │
├──────────────┴─────────────────────────────────┴───────────────┤
│  状态栏: 4138个符号 | 9364个关系 | 319个聚类 | 300个执行流       │
└────────────────────────────────────────────────────────────────┘
```

---

### 核心功能

| 功能 | 位置 | 说明 |
|------|------|------|
| **文件树浏览器** | 左侧面板 | 浏览代码库文件结构 |
| **语义搜索** | 左侧搜索框 | 自然语言搜索代码 |
| **图可视化** | 中央画布 | WebGL渲染知识图谱 |
| **执行流查看** | 顶部Processes标签 | 查看代码执行流程 |
| **功能聚类查看** | 顶部Clusters标签 | 查看功能模块划分 |
| **AI聊天** | 右侧面板 | 基于知识图谱的AI问答 |

---

## 详细操作指南

### 1. 文件树浏览器

**功能**: 浏览已索引代码库的文件结构

**操作**：
- 点击文件夹展开/折叠
- 点击文件查看详情
- 双击文件在图中定位

**快捷键**：
- `Ctrl + F`: 快速搜索文件

---

### 2. 语义搜索

**功能**: 使用自然语言搜索相关代码

**使用方法**：
1. 在左侧搜索框输入查询
2. 例如：`"authentication middleware"`
3. 按回车或点击搜索按钮

**搜索结果包含**：
- 相关的执行流（Processes）
- 相关的符号定义（Definitions）
- 相关的代码引用（References）

**示例查询**：
```
"知识图谱构建"
"错误处理流程"
"用户认证"
"数据库连接"
```

---

### 3. WebGL图可视化

**功能**: 交互式知识图谱可视化

#### 3.1 导航操作

| 操作 | 方法 |
|------|------|
| **平移** | 鼠标左键拖拽 |
| **缩放** | 鼠标滚轮 |
| **选中节点** | 单击节点 |
| **展开连接** | 双击节点 |
| **查看详情** | 右键节点 |

#### 3.2 节点类型

| 颜色 | 节点类型 |
|------|----------|
| 🔵 蓝色 | File（文件） |
| 🟢 绿色 | Function（函数） |
| 🟡 黄色 | Class（类） |
| 🟠 橙色 | Interface（接口） |
| 🟣 紫色 | Community（功能聚类） |
| 🔴 红色 | Process（执行流） |

#### 3.3 边类型

| 边类型 | 说明 |
|--------|------|
| CALLS | 函数调用关系 |
| IMPORTS | 导入关系 |
| EXTENDS | 继承关系 |
| IMPLEMENTS | 接口实现 |
| MEMBER_OF | 属于某个聚类 |
| STEP_IN_PROCESS | 执行流中的步骤 |

#### 3.4 布局算法

Web UI使用 **ForceAtlas2** 算法自动布局：
- 节点间通过引力/斥力平衡
- 相关节点自动聚类
- 支持大图优化（Barnes-Hut）

**手动调整布局**：
- 点击顶部 "Relayout" 按钮
- 拖拽节点固定位置

---

### 4. 执行流查看

**功能**: 查看代码从入口点到终点的完整执行路径

**打开方式**：
1. 点击顶部 "Processes" 标签
2. 或在搜索结果中点击某个Process

**执行流信息**：
```
Process: LoginFlow
Type: cross_community
Steps: 7

Step 1: handleLogin() - API入口
Step 2: validateUser() - 用户验证
Step 3: checkPassword() - 密码检查
Step 4: createSession() - 会话创建
Step 5: cacheUser() - 缓存更新
Step 6: logEvent() - 审计日志
Step 7: returnToken() - 响应生成
```

**操作**：
- 点击某个步骤，图中高亮显示
- 点击 "View in Graph" 跳转到图可视化
- 点击 "Export" 导出为Mermaid图

---

### 5. 功能聚类查看

**功能**: 查看代码库的功能模块划分

**打开方式**：
1. 点击顶部 "Clusters" 标签
2. 或在图中点击Community节点

**聚类信息**：
```
Community: CoreIngestion
Cohesion: 0.85
Members: 45

Top Members:
- processParsing
- processCalls
- resolveImport
- createKnowledgeGraph
```

**操作**：
- 点击成员查看详情
- 点击 "View in Graph" 在图中定位
- 点击 "Expand" 展开所有成员

---

### 6. AI聊天功能

**功能**: 基于知识图谱的智能问答

#### 6.1 配置LLM提供商

**步骤**：
1. 点击右侧面板的 "Settings" 图标
2. 选择LLM提供商（支持8种）

**支持的提供商**：
- OpenAI (gpt-4o, gpt-4o-mini)
- Azure OpenAI
- Google Gemini
- Anthropic Claude
- Ollama (本地)
- OpenRouter
- MiniMax
- GLM (智谱AI)

3. 输入API Key
4. 点击 "Connect"

#### 6.2 使用AI聊天

**示例问题**：
```
"这个项目的核心架构是什么？"
"用户认证流程是怎样的？"
"如何添加新的语言解析器？"
"这个函数被哪些地方调用？"
"这个模块的主要职责是什么？"
```

**AI回答特点**：
- ✅ 基于知识图谱的准确信息
- ✅ 自动引用代码位置 `[[file:line]]`
- ✅ 可以生成Mermaid架构图
- ✅ 最多50步递归查询

#### 6.3 Agent工具

AI Agent会自动使用以下7个工具：
- **search**: 语义搜索
- **cypher**: Cypher查询
- **grep**: 正则搜索
- **read**: 读取文件
- **overview**: 代码库概览
- **explore**: 深度探索
- **impact**: 影响分析

---

## 高级功能

### 1. 导出图数据

**导出为PNG图片**：
1. 点击右上角 "Export" 按钮
2. 选择 "Export as PNG"
3. 保存图片

**导出为JSON数据**：
```bash
curl http://localhost:4747/api/graph?repo=GitNexus > graph.json
```

---

### 2. Cypher查询

**在Web UI中执行Cypher查询**：
1. 点击顶部 "Query" 标签
2. 输入Cypher查询语句
3. 点击 "Execute"

**示例查询**：

```cypher
// 查询被调用次数最多的函数
MATCH (f:Function)<-[r:CodeRelation {type: 'CALLS'}]-(caller)
WHERE r.confidence > 0.8
RETURN f.name, count(caller) as callCount
ORDER BY callCount DESC
LIMIT 10

// 查询某个聚类的所有成员
MATCH (c:Community {heuristicLabel: 'CoreIngestion'})<-[:CodeRelation {type: 'MEMBER_OF'}]-(member)
RETURN member.name, member.kind

// 查询两个函数之间的调用路径
MATCH path = shortestPath(
  (start:Function {name: 'analyzeCommand'})-[:CodeRelation {type: 'CALLS'}*]-(end:Function {name: 'parseFile'})
)
RETURN path
```

---

### 3. 多仓库管理

**查看所有已索引的repo**：
```bash
node gitnexus/dist/cli/index.js list
```

**切换repo**：
1. 点击左上角的repo下拉菜单
2. 选择要查看的repo
3. Web UI会自动重新加载图数据

---

## 常见问题

### Q1: Web UI无法连接后端服务器

**症状**: 显示 "Failed to connect to server"

**解决方法**：

1. **检查后端服务器是否运行**：
```bash
ps aux | grep "gitnexus serve" | grep -v grep
```

2. **检查端口是否监听**：
```bash
netstat -tlnp | grep 4747
```

3. **重启后端服务器**：
```bash
pkill -f "gitnexus serve"
nohup node gitnexus/dist/cli/index.js serve --host 0.0.0.0 --port 4747 > /tmp/gitnexus-server.log 2>&1 &
```

---

### Q2: 图可视化显示空白

**症状**: 中央画布没有显示任何节点

**原因**: 没有索引代码库

**解决方法**：
```bash
# 索引代码库
cd /home/lmm/github_test/GitNexus
node gitnexus/dist/cli/index.js analyze

# 重启后端服务器
pkill -f "gitnexus serve"
nohup node gitnexus/dist/cli/index.js serve --host 0.0.0.0 --port 4747 > /tmp/gitnexus-server.log 2>&1 &

# 刷新Web UI浏览器页面
```

---

### Q3: AI聊天返回错误

**症状**: AI聊天返回 "API Error" 或 "Invalid API Key"

**解决方法**：

1. **检查API Key是否正确**
2. **检查网络连接**（是否能访问LLM API）
3. **尝试使用其他LLM提供商**
4. **查看浏览器控制台错误信息**（F12打开开发者工具）

---

### Q4: WSL中无法访问localhost

**症状**: Windows浏览器无法访问 `http://localhost:5173`

**解决方法**：

**方式1: 使用WSL IP地址**：
```bash
# 获取WSL IP
hostname -I
# 假设输出: 7.249.216.24

# 在浏览器访问
http://7.249.216.24:5173
```

**方式2: 重启WSL网络**（在Windows PowerShell中）：
```powershell
wsl --shutdown
# 然后重新打开WSL终端
```

**方式3: 检查Windows防火墙**：
- 临时关闭防火墙测试
- 或允许Node.js通过防火墙

---

### Q5: 图渲染很慢

**症状**: 图可视化卡顿、渲染缓慢

**原因**: 节点数量过多（>5000个）

**解决方法**：

1. **使用过滤器**：
   - 点击顶部 "Filter" 按钮
   - 选择只显示特定类型的节点
   - 例如：只显示Function和Class

2. **使用搜索定位**：
   - 不要查看整个图
   - 使用搜索功能定位到特定节点
   - 双击节点展开局部连接

3. **查看聚类视图**：
   - 切换到 "Clusters" 标签
   - 查看功能模块划分
   - 点击某个聚类查看局部图

---

## 性能优化

### 大型代码库优化

**对于大型代码库（>5000个符号）**：

1. **索引时跳过嵌入生成**：
```bash
node gitnexus/dist/cli/index.js analyze --skip-embeddings
```

2. **使用过滤器减少节点数量**：
   - 只显示特定类型的节点
   - 隐藏测试文件
   - 设置置信度阈值

3. **分模块查看**：
   - 使用聚类功能
   - 查看单个模块的图
   - 逐步探索

---

## 管理命令

### 查看服务状态

```bash
# 查看所有gitnexus相关进程
ps aux | grep -E "gitnexus|vite" | grep -v grep

# 查看端口占用
netstat -tlnp | grep -E "4747|5173"

# 查看日志
tail -f /tmp/gitnexus-server.log
tail -f /tmp/gitnexus-web.log
```

---

### 停止服务

```bash
# 停止API服务器
pkill -f "gitnexus serve"

# 停止Web UI
pkill -f "vite"

# 停止所有
pkill -f "gitnexus"
pkill -f "vite"
```

---

### 重启服务

```bash
# 重启API服务器
pkill -f "gitnexus serve"
sleep 2
nohup node gitnexus/dist/cli/index.js serve --host 0.0.0.0 --port 4747 > /tmp/gitnexus-server.log 2>&1 &

# 重启Web UI
pkill -f "vite"
sleep 2
cd gitnexus-web && nohup npm run dev > /tmp/gitnexus-web.log 2>&1 &
```

---

## 快速参考

### 常用URL

| 服务 | URL |
|------|-----|
| Web UI | http://localhost:5173 |
| API服务器 | http://localhost:4747 |
| 在线Web UI | https://gitnexus.vercel.app |
| API文档 | http://localhost:4747/api/docs |

---

### 常用API端点

| 端点 | 说明 |
|------|------|
| `/api/repos` | 列出所有repo |
| `/api/graph?repo=GitNexus` | 获取完整图数据 |
| `/api/processes?repo=GitNexus` | 获取所有执行流 |
| `/api/clusters?repo=GitNexus` | 获取所有聚类 |
| `/api/search` | 语义搜索 |
| `/api/query` | Cypher查询 |

---

### 快捷键

| 快捷键 | 功能 |
|--------|------|
| `Ctrl + F` | 快速搜索 |
| `Ctrl + /` | 切换侧边栏 |
| `Ctrl + G` | 图全屏 |
| `Ctrl + Space` | AI聊天聚焦 |
| `Esc` | 取消选择 |

---

## 下一步

- 📖 阅读 [中文架构文档](./architecture/GitNexus-中文架构文档.md)
- 🎯 查看 [体验指南](./GitNexus-体验指南.md)
- 🌐 访问 [在线Web UI](https://gitnexus.vercel.app)
- 💬 加入 [Discord社区](https://discord.gg/AAsRVT6fGb)

---

**祝您使用愉快！** 🎉