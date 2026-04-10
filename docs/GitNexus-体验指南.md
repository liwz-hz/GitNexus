# GitNexus 体验指南

> **适用版本**: GitNexus v1.5.3  
> **构建时间**: 2025年4月10日  
> **构建状态**: ✅ 成功

---

## 📋 目录

1. [构建验证](#构建验证)
2. [快速体验步骤](#快速体验步骤)
3. [核心功能体验](#核心功能体验)
4. [MCP集成体验](#mcp集成体验)
5. [Web UI体验](#web-ui体验)
6. [常见问题](#常见问题)

---

## 构建验证

### ✅ 构建成功确认

**构建信息**：
- 版本: `1.5.3`
- 构建时间: 7分钟
- node_modules大小: 1.2GB
- dist大小: 3.8MB
- 已内联shared模块: ✅

**验证命令**：
```bash
cd gitnexus
node dist/cli/index.js --version
# 输出: 1.5.3

node dist/cli/index.js --help
# 显示所有可用命令
```

---

## 快速体验步骤

### 步骤1: 索引GitNexus自身（最快体验）

**使用GitNexus索引它自己的代码库**，这是最快体验所有功能的方式：

```bash
# 在GitNexus项目根目录执行
cd /home/lmm/github_test/GitNexus
node gitnexus/dist/cli/index.js analyze
```

**预计时间**: 2-5分钟（取决于机器性能）

**预期输出**：
```
Phase 1-2: Structure (0-20%)
  Walking file tree...
  Created 1200+ File/Folder nodes

Phase 3-4: Parsing & Resolution (20-82%)
  Parsing TypeScript files...
  Parsing Python files...
  Resolving imports...
  Resolving calls...

Phase 5: Communities (82-92%)
  Running Leiden algorithm...
  Found 45+ communities

Phase 6: Processes (92-99%)
  Tracing execution flows...
  Found 120+ processes

✓ Analysis complete
Indexed 3298 symbols, 7954 relationships, 185 execution flows
```

**索引结果存储位置**：
- `.gitnexus/` 目录（自动gitignore）
- 全局注册: `~/.gitnexus/registry.json`

---

### 步骤2: 查看索引状态

```bash
# 查看当前repo的索引状态
node gitnexus/dist/cli/index.js status

# 查看所有已索引的repo
node gitnexus/dist/cli/index.js list
```

**预期输出**：
```
Repository: GitNexus
Path: /home/lmm/github_test/GitNexus
Last analyzed: 2025-04-10 15:30:00
Symbols: 3298
Relationships: 7954
Processes: 185
Communities: 45
Index size: 125MB
```

---

### 步骤3: 使用命令行工具体验核心功能

#### 3.1 语义搜索（query工具）

**搜索"authentication"相关代码**：
```bash
node gitnexus/dist/cli/index.js query "authentication" -r GitNexus
```

**预期输出**：
```
Processes:
  - summary: "AuthValidationFlow"
    priority: 0.045
    symbol_count: 6
    process_type: cross_community
    step_count: 8

Process Symbols:
  - name: validateToken
    type: Function
    filePath: src/auth/validate.ts
    process_id: proc_auth
    step_index: 2

Definitions:
  - name: AuthConfig
    type: Interface
    filePath: src/types/auth.ts
```

**搜索"知识图谱"相关代码**：
```bash
node gitnexus/dist/cli/index.js query "knowledge graph construction" -r GitNexus
```

---

#### 3.2 符号上下文查看（context工具）

**查看`runPipelineFromRepo`函数的360度视图**：
```bash
node gitnexus/dist/cli/index.js context runPipelineFromRepo -r GitNexus
```

**预期输出**：
```
Symbol:
  uid: Function:runPipelineFromRepo
  kind: Function
  filePath: gitnexus/src/core/ingestion/pipeline.ts
  startLine: 450

Incoming (callers):
  Calls:
    - runFullAnalysis [CALLS 95%] -> run-analyze.ts:45
    - testPipeline [CALLS 90%] -> test/unit/pipeline.test.ts:120

Outgoing (callees):
  Calls:
    - processStructure [CALLS 98%] -> structure-processor.ts:45
    - processParsing [CALLS 98%] -> parsing-processor.ts:67
    - processImports [CALLS 95%] -> import-processor.ts:89

Processes:
  - name: IndexingPipeline (step 1/6)
  - name: TestPipeline (step 3/8)
```

---

#### 3.3 影响范围分析（impact工具）

**分析修改`processParsing`函数的影响**：
```bash
node gitnexus/dist/cli/index.js impact processParsing -d upstream -r GitNexus
```

**预期输出**：
```
TARGET: Function processParsing (gitnexus/src/core/ingestion/parsing-processor.ts)

UPSTREAM (what depends on this):
  Depth 1 (WILL BREAK):
    - runPipelineFromRepo [CALLS 98%] -> pipeline.ts:520
    - testParsing [CALLS 90%] -> test/unit/parsing.test.ts:45

  Depth 2 (LIKELY AFFECTED):
    - runFullAnalysis [CALLS 95%] -> run-analyze.ts:67
    - analyzeCommand [CALLS 90%] -> cli/analyze.ts:120

  Depth 3 (MAY NEED TESTING):
    - e2eTest [CALLS 75%] -> test/e2e/analyze.test.ts:200

Risk Level: HIGH
Total Dependents: 15
```

---

#### 3.4 执行Cypher查询

**查询所有被调用次数最多的函数**：
```bash
node gitnexus/dist/cli/index.js cypher "
MATCH (f:Function)<-[r:CodeRelation {type: 'CALLS'}]-(caller)
WHERE r.confidence > 0.8
RETURN f.name, count(caller) as callCount
ORDER BY callCount DESC
LIMIT 10
" -r GitNexus
```

**预期输出**：
```
f.name                  callCount
------------------------------------
processParsing          45
processCalls            38
resolveImport           32
createKnowledgeGraph    28
loadParser              25
```

---

## 核心功能体验

### 功能1: 执行流追踪

**追踪"analyze命令"的完整执行流程**：

1. 首先搜索相关process：
```bash
node gitnexus/dist/cli/index.js query "analyze command execution" -r GitNexus
```

2. 查看具体process详情：
```bash
node gitnexus/dist/cli/index.js cypher "
MATCH (p:Process {name: 'AnalyzeCommand'})-[:CodeRelation {type: 'STEP_IN_PROCESS'}]->(step)
RETURN p.name, step.name, step.stepIndex
ORDER BY step.stepIndex
" -r GitNexus
```

---

### 功能2: 功能聚类分析

**查看代码库的功能模块划分**：

```bash
node gitnexus/dist/cli/index.js cypher "
MATCH (c:Community)
RETURN c.heuristicLabel, c.memberCount, c.cohesion
ORDER BY c.memberCount DESC
LIMIT 10
" -r GitNexus
```

**预期输出**：
```
c.heuristicLabel    c.memberCount  c.cohesion
--------------------------------------------------
CoreIngestion       45             0.85
McpServer           38             0.82
GraphDatabase       32             0.88
WebUI               28             0.76
EmbeddingPipeline   22             0.79
```

---

### 功能3: 重命名影响分析

**模拟重命名`resolveImport`函数**：

```bash
node gitnexus/dist/cli/index.js cypher "
MATCH (caller)-[r:CodeRelation {type: 'CALLS'}]->(f:Function {name: 'resolveImport'})
RETURN caller.name, caller.filePath, r.confidence
ORDER BY r.confidence DESC
LIMIT 20
" -r GitNexus
```

这会显示所有调用该函数的位置，帮助评估重命名的影响范围。

---

## MCP集成体验

### 方式1: 启动MCP服务器

```bash
# 启动MCP服务器（stdio模式）
node gitnexus/dist/cli/index.js mcp
```

**MCP服务器会**：
- 监听stdin获取MCP请求
- 通过stdout返回MCP响应
- 自动服务所有已索引的repo

**测试MCP连接**（需要MCP客户端，如Claude Code）：
- MCP客户端会自动发现所有工具
- 可以使用query、context、impact等16个工具

---

### 方式2: 启动HTTP服务器（Web UI Bridge）

```bash
# 启动HTTP服务器
node gitnexus/dist/cli/index.js serve --port 4747
```

**服务器地址**: `http://localhost:4747`

**可用API端点**：
- `GET /api/repos` - 列出所有已索引repo
- `GET /api/graph?repo=GitNexus` - 获取完整图数据
- `POST /api/query` - 执行Cypher查询
- `POST /api/search` - 语义搜索
- `GET /api/processes?repo=GitNexus` - 获取所有执行流
- `GET /api/clusters?repo=GitNexus` - 获取所有功能聚类

---

## Web UI体验

### 方式1: 在线体验（推荐）

**访问**: [gitnexus.vercel.app](https://gitnexus.vercel.app)

**使用步骤**：
1. 打开网站
2. 输入本地服务器地址: `http://localhost:4747`
3. 点击"Connect"
4. 开始探索图可视化和AI聊天

---

### 方式2: 本地运行Web UI

```bash
# 在另一个终端窗口
cd gitnexus-web
npm install
npm run dev
```

**访问**: `http://localhost:5173`

**Web UI功能**：
- 🎨 WebGL图可视化（Sigma.js + ForceAtlas2布局）
- 🔍 语义搜索界面
- 💬 AI聊天（支持8种LLM提供商）
- 📊 执行流可视化
- 🗂️ 功能聚类浏览

---

## 常见问题

### Q1: 索引速度慢怎么办？

**优化方法**：
```bash
# 跳过嵌入生成（更快）
node gitnexus/dist/cli/index.js analyze --skip-embeddings

# 只索引特定路径
node gitnexus/dist/cli/index.js analyze gitnexus/src/core

# 使用verbose模式查看进度
node gitnexus/dist/cli/index.js analyze --verbose
```

---

### Q2: 索引过期怎么办？

**症状**: MCP工具返回的结果与最新代码不符

**解决**:
```bash
# 检查索引状态
node gitnexus/dist/cli/index.js status

# 重新索引
node gitnexus/dist/cli/index.js analyze
```

---

### Q3: 如何索引其他项目？

**方法1: 绝对路径**
```bash
node gitnexus/dist/cli/index.js analyze /path/to/your/project
```

**方法2: 切换到目标项目目录**
```bash
cd /path/to/your/project
node /home/lmm/github_test/GitNexus/gitnexus/dist/cli/index.js analyze
```

---

### Q4: 如何清理索引？

**清理当前项目**:
```bash
node gitnexus/dist/cli/index.js clean --force
```

**清理所有项目**:
```bash
node gitnexus/dist/cli/index.js clean --all --force
```

---

### Q5: 支持哪些语言？

**支持14种语言**：
- TypeScript, JavaScript, Python
- Java, Kotlin, C#, Go, Rust
- PHP, Ruby, Swift, C, C++, Dart

**语言特性矩阵**：
- Import解析（所有语言）
- 类型推断（TypeScript, Python, Java等）
- 类继承（大部分面向对象语言）
- 函数调用图（所有语言）

---

## 下一步

### 深入学习

1. **阅读中文架构文档**:
   ```bash
   cat docs/architecture/GitNexus-中文架构文档.md
   ```

2. **查看官方文档**:
   - [ARCHITECTURE.md](../ARCHITECTURE.md) - 架构详解
   - [RUNBOOK.md](../RUNBOOK.md) - 运维手册
   - [README.md](../README.md) - 项目概览

3. **查看代码示例**:
   ```bash
   # 查看索引pipeline实现
   cat gitnexus/src/core/ingestion/pipeline.ts | head -100
   
   # 查看MCP服务器实现
   cat gitnexus/src/mcp/server.ts | head -100
   ```

---

### 实际应用场景

1. **代码审查**: 使用impact工具评估PR影响
2. **架构理解**: 使用query和context工具理解代码库
3. **重构辅助**: 使用impact分析重构风险
4. **文档生成**: 使用wiki命令生成架构文档
5. **AI辅助开发**: 通过MCP集成到AI编辑器

---

## 体验清单

完成以下任务，全面体验GitNexus能力：

- [ ] ✅ 构建成功
- [ ] 索引GitNexus自身代码库
- [ ] 使用query工具搜索"authentication"
- [ ] 使用context工具查看函数上下文
- [ ] 使用impact工具分析修改影响
- [ ] 执行Cypher查询统计调用次数
- [ ] 启动MCP服务器
- [ ] 启动HTTP服务器并连接Web UI
- [ ] 使用Web UI探索图可视化
- [ ] 尝试AI聊天功能

---

**祝您体验愉快！** 🎉

如有问题，请查阅 [中文架构文档](./architecture/GitNexus-中文架构文档.md) 或官方文档。