# GitNexus 项目中文架构文档

> **文档版本**: v1.0.0  
> **最后更新**: 2025年4月10日  
> **适用范围**: GitNexus v1.5.3

---

## 目录

1. [项目概览](#项目概览)
2. [软件架构](#软件架构)
3. [核心技术](#核心技术)
4. [关键流程](#关键流程)
5. [编译构建](#编译构建)
6. [使用方法](#使用方法)
7. [技术栈对比](#技术栈对比)

---

## 项目概览

### 项目定位

**GitNexus** 是一个为AI编程助手提供代码智能的图数据库引擎。它将任意代码库索引为知识图谱——包括每个依赖、调用链、功能聚类和执行流——然后通过智能工具暴露这些信息，让AI代理不会遗漏任何代码上下文。

**核心价值**：
- 解决AI编辑器（Cursor、Claude Code、Codex等）不理解代码库结构的问题
- 防止AI在修改函数时遗漏47个依赖函数，导致破坏性变更
- 通过预计算结构（聚类、追踪、评分）让工具在一次调用中返回完整上下文
- 使小模型也能获得完整的架构清晰度，与大模型竞争

### 项目组成

这是一个TypeScript/JavaScript **Monorepo**，包含两个主要产品：

| 组件 | 路径 | 功能 |
|------|------|------|
| **GitNexus CLI/Core** | `gitnexus/` | 主产品——TypeScript CLI、索引pipeline、MCP服务器、本地HTTP API、嵌入生成（可选） |
| **GitNexus Web UI** | `gitnexus-web/` | React/Vite浏览器应用——图可视化 + AI聊天，可连接到`gitnexus serve`后端 |
| gitnexus-shared | `gitnexus-shared/` | 共享类型定义和工具函数 |
| Claude Plugin | `gitnexus-claude-plugin/` | Claude marketplace静态配置 |
| Cursor Integration | `gitnexus-cursor-integration/` | Cursor编辑器静态配置 |
| SWE-bench Eval | `eval/` | Python评估框架（可选，需要Docker + LLM API密钥） |

---

## 软件架构

### 整体架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        GitNexus 架构全景                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌──────────────┐         ┌──────────────┐                   │
│   │   CLI入口     │         │   Web UI     │                   │
│   │ (gitnexus/   │         │ (gitnexus-   │                   │
│   │  src/cli/)   │         │   web/src/)  │                   │
│   └─────┬────────┘         └──────┬───────┘                   │
│         │                          │                           │
│         ├─ analyze ──────►         │                           │
│         │  索引pipeline            │  HTTP Bridge              │
│         │                          │  (gitnexus serve)         │
│         ├─ mcp ───────────►        │                           │
│         │  MCP服务器               │                           │
│         │                          │                           │
│         ├─ serve ─────────────────►│                           │
│         │  HTTP API服务器          │                           │
│         │                          │                           │
│   ┌─────▼────────┐         ┌──────▼───────┐                   │
│   │  Core索引     │         │   可视化层    │                   │
│   │  Pipeline     │◄────────│  Sigma.js    │                   │
│   │  (ingestion/) │         │  WebGL       │                   │
│   └─────┬────────┘         └──────┬───────┘                   │
│         │                          │                           │
│         ▼                          ▼                           │
│   ┌──────────────┐         ┌──────────────┐                   │
│   │  知识图谱     │         │  LLM Agent   │                   │
│   │  (graph/)    │         │  LangChain   │                   │
│   └─────┬────────┘         │  ReAct       │                   │
│         │                  └──────┬───────┘                   │
│         ▼                          │                           │
│   ┌──────────────┐                 │                           │
│   │  LadybugDB    │◄───────────────┘                           │
│   │  图数据库     │                                             │
│   │  (.gitnexus/ │                                             │
│   │   lbug/)     │                                             │
│   └──────────────┘                                             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 核心索引Pipeline架构

#### Pipeline编排器 (`gitnexus/src/core/ingestion/pipeline.ts`)

**主入口函数**: `runPipelineFromRepo(repoPath, onProgress)`

**架构模式**: 分块处理 + 增量解析

```
┌─────────────────────────────────────────────────────────────────┐
│                    GitNexus 索引Pipeline                          │
├─────────────────────────────────────────────────────────────────┤
│ Phase 1-2: Structure扫描 (0-20%)                                │
│   walkRepositoryPaths() → processStructure()                    │
│   Gitignore-aware文件树遍历                                      │
│                                                                 │
│ Phase 3-4: 分块解析+解析 (20-82%)                                │
│   20MB chunks → Worker Pool / Sequential fallback               │
│   processParsing → processImports → processCalls                │
│                                                                 │
│ Phase 5: Communities聚类 (82-92%)                               │
│   processCommunities() → Leiden算法                              │
│                                                                 │
│ Phase 6: Processes执行流 (92-99%)                               │
│   processProcesses() → BFS从入口点追踪                            │
└─────────────────────────────────────────────────────────────────┘
```

#### 六阶段详解

| 阶段 | 核心文件 | 功能描述 |
|------|----------|----------|
| **Phase 1-2: Structure** | `structure-processor.ts` | Gitignore-aware文件树遍历，创建File/Folder节点 + CONTAINS边，Markdown/COBOL预处理 |
| **Phase 3: Parsing** | `parsing-processor.ts` + `parse-worker.ts` | Worker Pool并行解析（>15文件自动启用），LRU AST缓存（容量50），20MB/chunk字节预算分块 |
| **Phase 4: Resolution** | `call-processor.ts` + `import-processor.ts` | Import解析（跨文件符号引用），Call解析（函数调用图构建），Heritage解析（类继承/接口实现），TypeEnv类型推断 |
| **Phase 5: Clustering** | `community-processor.ts` | Leiden社区发现算法（graphology-vendored），CALLS/EXTENDS/IMPLEMENTS边输入，输出Community节点 + MEMBER_OF边 |
| **Phase 6: Processes** | `process-processor.ts` | BFS从entry point追踪，Entry Point评分（导出状态、调用比、命名模式、AST框架检测器加成），输出Process节点 + STEP_IN_PROCESS边 |

### MCP服务器架构

#### 启动流程

```
CLI: gitnexus mcp
    ↓
LocalBackend.init() → 读取 ~/.gitnexus/registry.json
    ↓
startMCPServer(backend) → 创建MCP Server实例
    ↓
CompatibleStdioServerTransport → 监听stdin/stdout
```

#### LocalBackend多Repo连接池

**核心设计**：
- `repos: Map<string, RepoHandle>` - 管理所有已索引的repo
- `contextCache: Map<string, CodebaseContext>` - 轻量级上下文缓存（无需打开DB）
- `initializedRepos: Set<string>` - 懒加载标记

**连接池机制**：
```typescript
// 懒加载：首次查询时才打开LadybugDB连接
private async ensureInitialized(repoId: string): Promise<void> {
  // 1. 检查连接是否过期（索引重建后自动重连）
  // 2. 调用 initLbug(repoId, lbugPath)
  // 3. 预热 MAX_CONNS_PER_REPO=8 个Connection
}
```

**LRU淘汰策略**：
- `MAX_POOL_SIZE = 5` - 最多同时打开5个repo
- `IDLE_TIMEOUT_MS = 5分钟` - 空闲超时自动关闭
- `MAX_CONNS_PER_REPO = 8` - 每个repo最多8个并发连接

#### 16个MCP工具实现

**核心工具（11个）**：

| 工具 | 实现方法 | 核心逻辑 |
|------|----------|----------|
| `query` | `LocalBackend.query()` | BM25 + 语义搜索 → RRF融合 → 按Process分组返回 |
| `context` | `LocalBackend.context()` | 符号查找 → 分类引用(CALLS/IMPORTS/EXTENDS等) → Process参与度 |
| `impact` | `LocalBackend._runImpactBFS()` | BFS遍历图 → 按深度分组 → 计算风险等级 |
| `detect_changes` | `LocalBackend.detectChanges()` | git diff → 映射到符号 → 查找受影响的Process |
| `rename` | `LocalBackend.rename()` | 图引用(高置信度) + 文本搜索(低置信度) → 多文件编辑 |
| `cypher` | `LocalBackend.cypher()` | 直接执行Cypher查询，拦截写操作 |
| `route_map` | `LocalBackend.routeMap()` | Route节点 + FETCHES边 → 消费者映射 |
| `tool_map` | `LocalBackend.toolMap()` | Tool节点 + HANDLES_TOOL边 |
| `shape_check` | `LocalBackend.shapeCheck()` | responseKeys vs accessedKeys → 不匹配检测 |
| `api_impact` | `LocalBackend.apiImpact()` | 组合route_map + shape_check + impact |
| `list_repos` | `LocalBackend.listRepos()` | 刷新registry并返回repo列表 |

**Group工具（5个）**：

| 工具 | 方法 | 跨Repo逻辑 |
|------|------|-----------|
| `group_list` | `groupList()` | 列出所有group配置 |
| `group_sync` | `groupSync()` | 提取HTTP/gRPC契约 → 跨repo匹配 → 写入contracts.json |
| `group_contracts` | `groupContracts()` | 读取contracts.json，过滤展示 |
| `group_query` | `groupQuery()` | 遍历group内所有repo → 调用query() → RRF合并结果 |
| `group_status` | `groupStatus()` | 检查每个repo的索引过期状态和契约过期状态 |

#### MCP资源系统

**URI解析层级**：
```
gitnexus://repos                          → 全局repo列表
gitnexus://repo/{name}/context            → 代码库概览 + 过期检查
gitnexus://repo/{name}/clusters           → 所有功能模块(Leiden聚类)
gitnexus://repo/{name}/processes          → 所有执行流
gitnexus://repo/{name}/schema             → 图Schema(Cypher参考)
gitnexus://repo/{name}/cluster/{name}     → 模块详情(成员列表)
gitnexus://repo/{name}/process/{name}     → 执行流步骤追踪
```

### Web UI架构

#### 技术栈概览

**前端框架**：
- React 18.3 + TypeScript 5.4
- Vite 5.2 构建工具
- Tailwind CSS v4 (通过 @tailwindcss/vite 插件)

**核心依赖**：
```json
{
  "sigma": "^3.0.2",              // WebGL图渲染
  "graphology": "^0.26.0",        // 图数据结构
  "d3": "^7.9.0",                 // 辅助计算
  "langchain": "^1.2.10",         // AI Agent框架
  "@langchain/langgraph": "^1.1.0",  // ReAct agent
  "axios": "^1.13.2",             // HTTP客户端
  "mermaid": "^11.12.2",          // 图表渲染
  "lucide-react": "^0.562.0"      // 图标库
}
```

#### WebGL可视化架构（Sigma.js + Graphology）

```
KnowledgeGraph (内存图)
    ↓ knowledgeGraphToGraphology()
Graphology Graph (Sigma兼容格式)
    ↓ useSigma hook
Sigma WebGL Renderer
```

**关键实现细节**：

1. **初始化Sigma实例** (`useSigma.ts`)：
   - 配置：renderLabels, labelFont, defaultEdgeType, edgeProgramClasses
   - nodeReducer/edgeReducer：高亮/隐藏逻辑，边样式

2. **ForceAtlas2布局** (Web Worker运行)：
   - gravity: 小图0.8 / 大图0.15
   - scalingRatio: 小图15 / 大图100
   - barnesHutOptimize: 节点数>200启用

3. **节点定位策略** (`graph-adapter.ts`)：
   - 结构节点使用黄金角度分布
   - 子节点定位在父节点附近
   - 社区聚类中心点计算
   - 符号节点按聚类着色

**性能优化**：
- `hideEdgesOnMove: true` - 移动时隐藏边
- `zIndex: true` - Z排序
- Barnes-Hut优化（大图）
- 动态节点大小缩放

#### 后端Bridge模式

**重要发现**: Web UI **不直接运行LadybugDB WASM或Tree-sitter WASM**！

**实际架构**：
- **后端模式**: Web UI通过HTTP API连接 `gitnexus serve`，后端使用**原生LadybugDB**
- **查询路由**: 所有Cypher查询、搜索、grep都通过 `backend-client.ts` 发送到后端

**连接流程**：
```
1. 用户输入服务器URL (或 ?server= 查询参数)
2. normalizeServerUrl() 规范化URL
3. probeBackend() 探测后端可用性
4. fetchRepos() 获取可用仓库列表
5. fetchGraph() 下载图数据
6. createKnowledgeGraph() 构建内存图
7. initializeAgent() 初始化LLM agent
```

**API端点**：
- `/api/graph` - 获取完整图数据
- `/api/query` - Cypher查询
- `/api/search` - 混合搜索
- `/api/grep` - 正则搜索
- `/api/file` - 文件读取
- `/api/embed` - 向量嵌入生成
- `/api/processes` / `/api/clusters` - 流程和聚类数据

#### LLM Agent架构

**框架**: LangChain + LangGraph ReAct Agent

**支持的LLM提供商（8个）**：
- OpenAI (gpt-4o, gpt-4o-mini等)
- Azure OpenAI
- Google Gemini
- Anthropic Claude
- Ollama (本地)
- OpenRouter
- MiniMax
- GLM (智谱AI)

**Agent工具（7个）**：
```typescript
const tools = [
  searchTool,    // 混合搜索 + 流程分组
  cypherTool,    // Cypher查询（自动嵌入向量）
  grepTool,      // 正则搜索
  readTool,      // 文件读取
  overviewTool,  // 代码库概览
  exploreTool,   // 深度探索符号/聚类/流程
  impactTool     // 影响分析（上游/下游依赖）
];
```

---

## 核心技术

### Tree-sitter多语言解析器集成

#### 设计模式：策略模式 + 编译时穷尽性检查

**LanguageProvider接口** (`language-provider.ts`)：
```typescript
interface LanguageProvider {
  id: SupportedLanguages;
  extensions: readonly string[];
  treeSitterQueries: string;        // Tree-sitter查询字符串
  typeConfig: LanguageTypeConfig;   // 类型提取配置
  exportChecker: ExportChecker;     // 导出检测
  importResolver: ImportResolverFn; // 导入解析
  importSemantics?: 'named' | 'wildcard' | 'namespace';
  mroStrategy?: 'first-wins' | 'c3' | 'leftmost-base';
  implicitImportWirer?: Function;   // Swift/C隐式导入
  // ... 更多可选钩子
}
```

**编译时保障**：`providers`表使用`satisfies Record<SupportedLanguages, LanguageProvider>`，任何新增语言枚举必须实现提供者，否则编译失败。

#### 14种语言特性支持矩阵

| 语言 | Imports | Named Bindings | Heritage | Type Annotations | Constructor Inference | Config |
|------|---------|----------------|----------|-----------------|----------------------|--------|
| TypeScript | ✓ resolveTypescriptImport | ✓ extractTsNamedBindings | ✓ extends/implements | ✓ typescriptConfig | ✓ | tsconfig.json paths |
| JavaScript | ✓ resolveTypescriptImport | ✓ extractTsNamedBindings | ✓ extends | - | ✓ | tsconfig.json paths |
| Python | ✓ resolvePythonImport (PEP 328) | ✓ extractPythonNamedBindings | ✓ superclasses | ✓ pythonConfig | ✓ | - |
| Java | ✓ resolveJavaImport | ✓ extractJavaNamedBindings | ✓ superclass | ✓ jvmConfig | ✓ | - |
| Kotlin | ✓ resolveKotlinImport | ✓ extractKotlinNamedBindings | ✓ delegation_specifier | ✓ jvmConfig | ✓ | - |
| C# | ✓ resolveCSharpImport | ✓ extractCSharpNamedBindings | ✓ base_list | ✓ csharpConfig | ✓ | .csproj RootNamespace |
| Go | ✓ resolveGoImport (package级) | - | ✓ struct embedding | ✓ goConfig | ✓ | go.mod module path |
| Rust | ✓ resolveRustImport (crate::) | ✓ extractRustNamedBindings | ✓ impl trait | ✓ rustConfig | ✓ | - |
| PHP | ✓ resolvePhpImport (PSR-4) | ✓ extractPhpNamedBindings | ✓ base_clause | ✓ phpConfig | ✓ | composer.json autoload |
| Ruby | ✓ resolveRubyImport | - | ✓ include/extend | - | ✓ | - |
| Swift | ✓ resolveSwiftImport | - | ✓ inheritance_specifier | ✓ swiftConfig | ✓ | Package.swift targets |
| C | ✓ resolveCImport | - | - | ✓ cCppConfig | ✓ | - |
| C++ | ✓ resolveCppImport | - | ✓ base_class_clause | ✓ cCppConfig | ✓ | - |
| Dart | ✓ resolveDartImport | - | ✓ extends/with/implements | ✓ dartConfig | ✓ | - |

### Import Resolution三级机制

#### Tier 1: 语言特定预处理

**Python**: PEP 328相对导入 + 邻近查找
```typescript
if (importPath.startsWith('.')) {
  // 计算目录层级，向上遍历
}
// 邻近模块优先：检查同目录__init__.py和.py文件
```

**TypeScript**: tsconfig path aliases
```typescript
if (tsconfigPaths && !importPath.startsWith('.')) {
  for (const [aliasPrefix, targetPrefix] of tsconfigPaths.aliases) {
    if (importPath.startsWith(aliasPrefix)) {
      // 重写路径
    }
  }
}
```

#### Tier 2: 相对导入解析

**标准相对路径解析**（./ 和 ../）：
```typescript
const currentDir = currentFile.split('/').slice(0, -1);
for (const part of importPath.split('/')) {
  if (part === '..') currentDir.pop();
  else if (part !== '.') currentDir.push(part);
}
```

#### Tier 3: 后缀匹配

**构建后缀索引实现O(1)查找**：
```typescript
// 将importPath转为路径后缀，在allFileList中查找匹配
const pathParts = pathLike.split('/').filter(Boolean);
const resolved = suffixResolve(pathParts, normalizedFileList, allFileList, index);
```

### Constructor Inference实现

#### 类型推断层级（type-env.ts）

```typescript
// Tier 0: 显式类型注解
config.extractDeclaration(node, scopeEnv);  // 提取 let x: User = ...

// Tier 1: 构造函数推断
config.extractInitializer(node, scopeEnv, classNames);  // 推断 let x = new User()

// Tier 2: 传播推断
resolveFixpointBindings(pendingItems, env, returnTypeLookup, symbolTable, parentMap);
// 处理链式推断：
// const user = getUser();      // callResult → User
// const addr = user.address;   // fieldAccess → Address
// const city = addr.getCity(); // methodCallResult → City
```

#### Receiver类型解析（call-processor.ts）

```typescript
// self/this/super AST解析
if (varName === 'self' || varName === 'this') {
  return findEnclosingClassName(callNode);  // 向上遍历AST找类名
}

// 虚拟派发覆盖（Phase P）
if (receiverTypeName && receiverName && typeEnv.constructorTypeMap.size > 0) {
  const ctorType = typeEnv.constructorTypeMap.get(`${scope}\0${receiverName}`);
  // Animal a = new Dog() → 使用Dog而非Animal
}
```

### Framework Detection机制

#### 路径模式检测（70+模式）

```typescript
// framework-detection.ts
if (p.includes('/pages/api/') || (p.includes('/app/') && p.endsWith('route.ts'))) {
  return { framework: 'nextjs-api', entryPointMultiplier: 3.0 };
}
if ((p.includes('/controller/') || p.includes('/controllers/')) && p.endsWith('.java')) {
  return { framework: 'spring', entryPointMultiplier: 3.0 };
}
```

#### AST模式检测（20+框架）

```typescript
// 装饰器/注解/属性检测
FRAMEWORK_AST_PATTERNS = {
  nestjs: ['@Controller', '@Get', '@Post', '@Put', '@Delete'],
  spring: ['@RestController', '@Controller', '@GetMapping'],
  aspnet: ['[ApiController]', '[HttpGet]', '[Route]'],
  laravel: ['Route::get', 'Route::post'],
  actix: ['#[get', '#[post', '#[actix_web'],
  // ...
}
```

### LadybugDB存储架构

#### Schema设计

**节点表（26种）**：
- File, Folder, Function, Class, Method, Interface, Struct, Enum, Trait, Impl, Macro
- Community, Process, Route, Tool, Section等

**关系表（1种）**：
- `CodeRelation` (带type属性区分CALLS/IMPORTS/EXTENDS/IMPLEMENTS/MEMBER_OF/STEP_IN_PROCESS等)

**向量表**：
- `CodeEmbedding(nodeId, embedding FLOAT[384])`

#### 加载流程

```typescript
loadGraphToLbug(graph, repoPath)
  → streamAllCSVsToDisk()      // 内存图→CSV文件
  → COPY ... FROM "file.csv"   // 批量导入
  → createFTSIndex()           // 全文索引
```

### Embedding生成流程

```
runEmbeddingPipeline()
  ↓
Phase 1: Load Model (transformers.js / HTTP API)
  ↓
Phase 2: Query embeddable nodes (File, Function, Class, Method)
  ↓
Phase 3: Batch embed (default 64/batch)
  ↓
Phase 4: Create vector index (HNSW + cosine)
```

**默认模型**: `snowflake-arctic-embed-xs` (384维)

### 混合搜索架构（BM25 + 语义 + RRF融合）

```typescript
hybridSearch(query)
  → BM25: LadybugDB FTS索引
  → Semantic: 向量索引 (cosine similarity)
  → RRF merge: 1/(k + rank) 融合分数
```

---

## 关键流程

### analyze命令完整执行路径

```
CLI: gitnexus analyze [path]
    ↓
runFullAnalysis(repoPath)  [run-analyze.ts]
    ↓
Phase 1: runPipelineFromRepo(repoPath, onProgress)  [pipeline.ts]
    ├─ walkRepositoryPaths()  [filesystem-walker.ts]
    ├─ processStructure()  [structure-processor.ts]
    ├─ processMarkdown() / processCobol()
    ├─ processParsing()  [parsing-processor.ts]
    │   ├─ Worker Pool初始化 (>15文件)
    │   ├─ loadParser() / loadLanguage()  [parser-loader.ts]
    │   ├─ parser.parse(content)
    │   ├─ query.matches(tree.rootNode)  // Tree-sitter queries
    │   └─ extract symbols → graph.addNode()
    ├─ processImports()  [import-processor.ts]
    │   ├─ 语言特定resolver调用
    │   ├─ 相对路径解析
    │   └─ 后缀匹配查找
    ├─ processCalls()  [call-processor.ts]
    │   ├─ Receiver类型推断
    │   ├─ Call边构建
    │   ├─ Heritage边构建  [heritage-processor.ts]
    │   └─ MRO线性化  [mro-processor.ts]
    ├─ processCommunities()  [community-processor.ts]
    │   ├─ Leiden算法执行
    │   ├─ Community节点创建
    │   └─ MEMBER_OF边添加
    └─ processProcesses()  [process-processor.ts]
        ├─ Entry Point评分
        ├─ BFS追踪
        └─ Process节点 + STEP_IN_PROCESS边
    ↓
Phase 2: loadGraphToLbug(graph, repoPath)  [lbug-adapter.ts]
    ├─ streamAllCSVsToDisk()  [csv-generator.ts]
    ├─ LadybugDB批量导入
    ├─ createFTSIndex()
    └─ 保存meta.json
    ↓
Phase 3 (可选): runEmbeddingPipeline()  [embedding-pipeline.ts]
    ├─ 模型加载
    ├─ 批量嵌入生成
    └─ 向量索引创建
    ↓
Phase 4: updateRegistry(repoPath)  [repo-manager.ts]
    └─ 写入 ~/.gitnexus/registry.json
    ↓
完成
```

### query工具执行流程

```
MCP Tool: query({query: "authentication middleware"})
    ↓
LocalBackend.query(params)  [local-backend.ts]
    ├─ ensureInitialized(repoId)
    ├─ 混合搜索
    │   ├─ BM25: LadybugDB FTS查询
    │   ├─ Semantic: 向量相似度查询
    │   └─ RRF融合
    ├─ Process分组
    │   ├─ 查询Process节点
    │   ├─ 查询STEP_IN_PROCESS边
    │   └─ 按priority排序
    ├─ symbol详情填充
    │   ├─ 获取filePath, startLine, endLine
    │   ├─ 获取node kind
    │   └─ 分类引用关系
    └─ 返回结果 + Next-Step提示
```

### context工具执行流程

```
MCP Tool: context({name: "validateUser"})
    ↓
LocalBackend.context(params)  [local-backend.ts]
    ├─ ensureInitialized(repoId)
    ├─ 符号查找
    │   ├─ 精确匹配 (UID)
    │   ├─ 文件路径过滤
    │   └─ 模糊匹配 (名称)
    ├─ 分类引用提取
    │   ├─ incoming: CALLS, IMPORTS, EXTENDS, IMPLEMENTS
    │   ├─ outgoing: CALLS, IMPORTS, EXTENDS, IMPLEMENTS
    │   └─ 分类 + 置信度标记
    ├─ Process参与度
    │   ├─ 查询STEP_IN_PROCESS边
    │   ├─ 获取Process名称
    │   └─ 获取step索引
    ├─ 内容获取 (可选)
    │   ├─ 读取源文件
    │   └─ 提取符号源代码
    └─ 返回360度视图 + Next-Step提示
```

### impact工具执行流程（BFS遍历）

```
MCP Tool: impact({target: "UserService", direction: "upstream"})
    ↓
LocalBackend.impact(params)  [local-backend.ts]
    ├─ ensureInitialized(repoId)
    ├─ 目标符号查找
    ├─ BFS初始化
    │   ├─ queue: [target]
    │   ├─ visited: Set
    │   ├─ depthMap: Map
    │   └─ results: []
    ├─ BFS循环
    │   ├─ dequeue当前节点
    │   ├─ 查询邻居节点
    │   │   ├─ upstream: CALLS, IMPORTS, EXTENDS, IMPLEMENTS
    │   │   └─ downstream: CALLS, IMPORTS, EXTENDS, IMPLEMENTS
    │   ├─ 计算深度
    │   ├─ 收集置信度
    │   ├─ 添加到results
    │   └─ enqueue未访问邻居
    ├─ 深度分组
    │   ├─ d=1: WILL BREAK
    │   ├─ d=2: LIKELY AFFECTED
    │   ├─ d=3: MAY NEED TESTING
    │   └─ 计算风险等级
    └─ 返回blast radius + Next-Step提示
```

---

## 编译构建

### 项目结构

```
GitNexus/
├── gitnexus/                    # CLI/MCP核心包
│   ├── src/                     # TypeScript源码
│   │   ├── cli/                 # CLI命令实现
│   │   ├── core/                # 核心业务逻辑
│   │   │   ├── ingestion/       # 索引pipeline
│   │   │   ├── graph/           # 知识图谱
│   │   │   ├── lbug/            # LadybugDB适配
│   │   │   ├── embeddings/      # 嵌入生成
│   │   │   ├── search/          # 搜索引擎
│   │   │   └── wiki/            # Wiki生成
│   │   ├── mcp/                 # MCP服务器
│   │   │   ├── local/           # LocalBackend
│   │   │   ├── server.ts        # MCP服务器
│   │   │   ├── tools.ts         # 工具定义
│   │   │   └─ resources.ts      # 资源系统
│   │   ├── server/              # HTTP API服务器
│   │   └── lib/                 # 工具函数
│   ├── test/                    # 测试文件
│   │   ├── unit/                # 单元测试
│   │   └─ integration/          # 集成测试
│   ├── scripts/                 # 构建脚本
│   │   └── build.js             # 主构建脚本
│   ├── dist/                    # 编译输出
│   ├── package.json             # 依赖声明
│   └── tsconfig.json            # TypeScript配置
│
├── gitnexus-web/                # Web UI
│   ├── src/                     # React源码
│   │   ├── components/          # UI组件
│   │   ├── hooks/               # React Hooks
│   │   ├── core/                # 核心逻辑
│   │   │   ├── graph/           # 图数据层
│   │   │   ├── llm/             # LLM Agent
│   │   │   └─ ingestion/        # 索引pipeline
│   │   ├── services/            # 后端通信
│   │   ├── lib/                 # 工具函数
│   │   └── vendor/              # Vendored库
│   ├── test/                    # 测试文件
│   ├── package.json             # 依赖声明
│   ├── tsconfig.json            # TypeScript配置
│   └─ vite.config.ts            # Vite配置
│
├── gitnexus-shared/             # 共享类型
│   ├── src/                     # TypeScript源码
│   ├── dist/                    # 编译输出
│   └── package.json             # 依赖声明
│
├── .github/                     # CI/CD
│   └── workflows/               # GitHub Actions
│       ├── ci.yml               # 主CI编排
│       ├── ci-quality.yml       # TypeScript检查
│       ├── ci-tests.yml         # 单元+集成测试
│       ├── ci-e2e.yml           # E2E测试
│       └── publish.yml          # npm发布
│
└── docs/                        # 文档
```

### 构建流程

#### CLI/Core构建 (`gitnexus/scripts/build.js`)

**构建步骤**：

1. **编译gitnexus-shared**：
```bash
cd gitnexus-shared && npx tsc
```

2. **编译gitnexus**：
```bash
cd gitnexus && npx tsc
```

3. **内联gitnexus-shared到dist**：
```bash
cp gitnexus-shared/dist → gitnexus/dist/_shared
```

4. **重写imports**：
```javascript
// 将 'gitnexus-shared' 重写为相对路径
from 'gitnexus-shared' → from './_shared/index.js'
```

5. **设置CLI入口可执行权限**：
```bash
chmod 755 dist/cli/index.js
```

**TypeScript配置** (`gitnexus/tsconfig.json`)：
```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "outDir": "dist",
    "rootDir": "src",
    "strict": false,
    "esModuleInterop": true,
    "declaration": true
  }
}
```

#### Web UI构建

**开发模式**：
```bash
cd gitnexus-web
npm install
npm run dev  # Vite开发服务器，端口5173
```

**生产构建**：
```bash
npm run build  # tsc -b && vite build
```

**TypeScript配置** (`gitnexus-web/tsconfig.json`)：
```json
{
  "compilerOptions": {
    "target": "ES2020",
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "moduleResolution": "bundler",
    "jsx": "react-jsx",
    "strict": true,
    "esModuleInterop": true
  }
}
```

### CI/CD流程

#### GitHub Actions编排 (`ci.yml`)

**触发条件**：
- push到main分支
- pull_request到main分支
- 忽略`.md`, `docs/**`, `LICENSE`变更

**Job依赖关系**：
```
┌──────────────┐
│   quality    │ TypeScript检查
└──────┬───────┘
       │
┌──────▼───────┐
│    tests     │ 单元+集成测试
└──────┬───────┘
       │
┌──────▼───────┐
│     e2e      │ E2E测试（仅gitnexus-web变更时）
└──────┬───────┘
       │
┌──────▼───────┐
│  ci-status   │ 统一CI门控
└──────────────┘
```

**质量检查** (`ci-quality.yml`)：
```bash
cd gitnexus && npx tsc --noEmit
cd gitnexus-web && npx tsc -b --noEmit
```

**测试运行** (`ci-tests.yml`)：
```bash
cd gitnexus && npm test                    # vitest run test/unit
cd gitnexus && npm run test:integration    # vitest run test/integration
cd gitnexus-web && npm test                # vitest run
```

**E2E测试** (`ci-e2e.yml`)：
```bash
# 仅当gitnexus-web/**变更时触发
cd gitnexus && npx gitnexus serve         # 启动后端
cd gitnexus-web && npm run dev            # 启动前端
cd gitnexus-web && E2E=1 npx playwright test  # E2E测试
```

### Pre-commit Hook

**Husky配置** (`.husky/pre-commit`)：
- `gitnexus/`文件变更 → `tsc --noEmit` + `vitest run --project default`
- `gitnexus-web/`文件变更 → `tsc -b --noEmit` + `vitest run`

**跳过hook**：
```bash
git commit --no-verify  # 谨慎使用
```

### 测试结构

| 包 | Runner | 测试类型 | 命令 |
|---|--------|---------|------|
| gitnexus | Vitest | 单元测试 | `npm test` |
| gitnexus | Vitest | 集成测试 | `npm run test:integration` |
| gitnexus | Vitest | 全量测试 | `npm run test:all` |
| gitnexus-web | Vitest | 单元测试 | `npm test` |
| gitnexus-web | Playwright | E2E测试 | `npm run test:e2e` |

**测试覆盖率**：
```bash
cd gitnexus && npm run test:coverage
cd gitnexus-web && npm run test:coverage
```

---

## 使用方法

### 快速开始

#### 安装与索引

```bash
# 全局安装（推荐）
npm install -g gitnexus

# 或使用npx（无需安装）
npx gitnexus analyze
```

#### 一键索引

```bash
# 从仓库根目录运行
cd /path/to/your/repo
npx gitnexus analyze
```

**analyze命令会自动完成**：
1. 索引代码库
2. 安装agent skills到`.claude/skills/`
3. 注册Claude Code hooks
4. 创建`AGENTS.md`和`CLAUDE.md`上下文文件

#### MCP配置

**自动配置（推荐）**：
```bash
npx gitnexus setup  # 自动检测编辑器并写入配置
```

**手动配置**：

**Claude Code** (完整支持——MCP + skills + hooks)：
```bash
# macOS / Linux
claude mcp add gitnexus -- npx -y gitnexus@latest mcp

# Windows
claude mcp add gitnexus -- cmd /c npx -y gitnexus@latest mcp
```

**Cursor** (`~/.cursor/mcp.json`，全局配置)：
```json
{
  "mcpServers": {
    "gitnexus": {
      "command": "npx",
      "args": ["-y", "gitnexus@latest", "mcp"]
    }
  }
}
```

**Codex**：
```bash
codex mcp add gitnexus -- npx -y gitnexus@latest mcp
```

**OpenCode** (`~/.config/opencode/config.json`)：
```json
{
  "mcp": {
    "gitnexus": {
      "type": "local",
      "command": ["gitnexus", "mcp"]
    }
  }
}
```

### CLI命令详解

#### 核心命令

| 命令 | 功能 | 示例 |
|------|------|------|
| `gitnexus setup` | 配置MCP（一次性） | `gitnexus setup` |
| `gitnexus analyze [path]` | 索引仓库 | `gitnexus analyze` |
| `gitnexus analyze --force` | 强制重新索引 | `gitnexus analyze --force` |
| `gitnexus analyze --embeddings` | 启用嵌入生成 | `gitnexus analyze --embeddings` |
| `gitnexus analyze --skills` | 生成repo-specific skills | `gitnexus analyze --skills` |
| `gitnexus mcp` | 启动MCP服务器 | `gitnexus mcp` |
| `gitnexus serve` | 启动HTTP服务器（Web UI连接） | `gitnexus serve` |
| `gitnexus list` | 列出已索引仓库 | `gitnexus list` |
| `gitnexus status` | 查看索引状态 | `gitnexus status` |
| `gitnexus clean` | 清理索引 | `gitnexus clean --force` |
| `gitnexus wiki` | 生成Wiki文档 | `gitnexus wiki --model gpt-4o` |

#### 直接工具命令（无MCP开销）

| 命令 | 功能 | 示例 |
|------|------|------|
| `gitnexus query <query>` | 搜索知识图谱 | `gitnexus query "authentication" -r MyRepo` |
| `gitnexus context [name]` | 360度符号视图 | `gitnexus context validateUser -r MyRepo` |
| `gitnexus impact <target>` | 影响范围分析 | `gitnexus impact UserService -d upstream` |
| `gitnexus cypher <query>` | Cypher查询 | `gitnexus cypher "MATCH (n) RETURN count(n)"` |

#### Group命令（多repo/monorepo服务追踪）

| 命令 | 功能 | 示例 |
|------|------|------|
| `gitnexus group create <name>` | 创建group | `gitnexus group create my-services` |
| `gitnexus group add <name> <repo>` | 添加repo到group | `gitnexus group add my-services auth-service` |
| `gitnexus group sync <name>` | 提取契约并匹配 | `gitnexus group sync my-services` |
| `gitnexus group query <name> <q>` | 跨repo搜索 | `gitnexus group query my-services "login"` |
| `gitnexus group status <name>` | 检查group状态 | `gitnexus group status my-services` |

### MCP工具使用示例

#### query工具：Process分组搜索

```typescript
query({query: "authentication middleware"})

// 返回结果：
processes:
  - summary: "LoginFlow"
    priority: 0.042
    symbol_count: 4
    process_type: cross_community
    step_count: 7

process_symbols:
  - name: validateUser
    type: Function
    filePath: src/auth/validate.ts
    process_id: proc_login
    step_index: 2

definitions:
  - name: AuthConfig
    type: Interface
    filePath: src/types/auth.ts
```

#### context工具：360度符号视图

```typescript
context({name: "validateUser"})

// 返回结果：
symbol:
  uid: "Function:validateUser"
  kind: Function
  filePath: src/auth/validate.ts
  startLine: 15

incoming:
  calls: [handleLogin, handleRegister, UserController]
  imports: [authRouter]

outgoing:
  calls: [checkPassword, createSession]

processes:
  - name: LoginFlow (step 2/7)
  - name: RegistrationFlow (step 3/5)
```

#### impact工具：影响范围分析

```typescript
impact({target: "UserService", direction: "upstream", minConfidence: 0.8})

// 返回结果：
TARGET: Class UserService (src/services/user.ts)

UPSTREAM (what depends on this):
  Depth 1 (WILL BREAK):
    handleLogin [CALLS 90%] -> src/api/auth.ts:45
    handleRegister [CALLS 90%] -> src/api/auth.ts:78
    UserController [CALLS 85%] -> src/controllers/user.ts:12
  Depth 2 (LIKELY AFFECTED):
    authRouter [IMPORTS] -> src/routes/auth.ts
```

#### detect_changes工具：预提交检查

```typescript
detect_changes({scope: "all"})

// 返回结果：
summary:
  changed_count: 12
  affected_count: 3
  changed_files: 4
  risk_level: medium

changed_symbols: [validateUser, AuthService, ...]
affected_processes: [LoginFlow, RegistrationFlow, ...]
```

#### rename工具：多文件重命名

```typescript
rename({symbol_name: "validateUser", new_name: "verifyUser", dry_run: true})

// 返回结果：
status: success
files_affected: 5
total_edits: 8
graph_edits: 6     (high confidence)
text_search_edits: 2  (review carefully)
changes: [...]
```

### Web UI使用

#### 在线访问

**直接访问**: [gitnexus.vercel.app](https://gitnexus.vercel.app)

**使用流程**：
1. 打开网站
2. 拖放ZIP文件或上传代码
3. 开始探索图谱和AI聊天

#### 本地Bridge模式

**启动后端**：
```bash
cd gitnexus
npx gitnexus serve  # 默认端口4747
```

**连接Web UI**：
1. 打开 [gitnexus.vercel.app](https://gitnexus.vercel.app)
2. 输入后端URL: `http://localhost:4747`
3. 自动检测所有已索引repo
4. 无需重新上传或索引

#### 本地开发Web UI

```bash
git clone https://github.com/abhigyanpatwari/gitnexus.git
cd gitnexus/gitnexus-shared && npm install && npm run build
cd ../gitnexus-web && npm install
npm run dev
```

### 系统要求

| 环境 | CLI/Core | Web UI |
|------|----------|--------|
| **Node.js** | ≥20.0.0 | ≥20.0.0 |
| **Git** | 必需（用于commit追踪） | 可选 |
| **浏览器** | - | Chrome/Edge/Firefox/Safari (WebGL支持) |
| **内存** | 大repo需要8GB heap | ~5K文件限制 |
| **Python** | Tree-sitter构建需要（可选） | - |

### 常见问题解决

#### 索引过期

**症状**: MCP或resources警告索引落后HEAD

**解决**：
```bash
npx gitnexus analyze  # 更新索引
npx gitnexus status   # 检查状态
```

#### MCP找不到repo

**症状**: `GitNexus: No indexed repos yet`

**解决**：
```bash
cd /path/to/repo
npx gitnexus analyze  # 在每个项目执行
```

#### Embedding丢失

**症状**: `stats.embeddings = 0` in `.gitnexus/meta.json`

**解决**：
```bash
# 重新索引时必须传递--embeddings
npx gitnexus analyze --embeddings
```

#### LadybugDB锁错误

**症状**: 多进程冲突

**解决**：
- 只有一个进程应打开repo的`.gitnexus/lbug`
- 停止MCP或analyze，然后重试

---

## 技术栈对比

### CLI vs Web技术栈对比表

| 维度 | CLI版本 | Web UI版本 |
|------|---------|-----------|
| **运行时** | Node.js原生 | 浏览器 |
| **数据库** | LadybugDB原生 | 通过HTTP API（后端） |
| **解析器** | Tree-sitter原生绑定 | 后端代理 |
| **嵌入** | transformers.js (GPU/CPU) | 后端处理 |
| **可视化** | 无 | Sigma.js WebGL |
| **Agent** | MCP服务器 | LangChain ReAct |
| **并发** | Worker threads | 主线程（I/O密集） |
| **存储** | 文件系统持久化 | 内存（会话级） |
| **规模限制** | 任意大小 | ~5K文件（浏览器内存限制） |
| **隐私** | 完全本地，无网络 | 浏览器内或后端连接 |
| **MCP支持** | 16个工具 + 7个资源 | 7个Agent工具 |
| **LLM提供商** | MCP客户端决定 | 8个提供商集成 |
| **聚类算法** | Graphology (Node) | Graphology (Browser) |
| **搜索模式** | BM25 + 语义 + RRF | BM25 + 语义 + RRF |
| **布局算法** | 无 | ForceAtlas2 (Web Worker) |

### 性能优化策略对比

| 策略 | CLI | Web UI |
|------|-----|--------|
| **AST缓存** | LRU (容量50) | 无（后端处理） |
| **并行解析** | Worker Pool (>15文件) | 无（后端处理） |
| **分块处理** | 20MB/chunk | 无（后端处理） |
| **图布局** | 无 | ForceAtlas2 + Barnes-Hut |
| **渲染优化** | 无 | hideEdgesOnMove, zIndex |
| **连接池** | MAX_CONNS_PER_REPO=8 | HTTP连接复用 |
| **索引持久化** | `.gitnexus/lbug` | 无（内存图） |
| **嵌入批量** | 64/batch | 后端处理 |

---

## 附录

### 关键文件路径索引

**核心Pipeline**：
- `/home/lmm/github_test/GitNexus/gitnexus/src/core/ingestion/pipeline.ts`
- `/home/lmm/github_test/GitNexus/gitnexus/src/core/run-analyze.ts`

**六阶段Processor**：
- `/home/lmm/github_test/GitNexus/gitnexus/src/core/ingestion/structure-processor.ts`
- `/home/lmm/github_test/GitNexus/gitnexus/src/core/ingestion/parsing-processor.ts`
- `/home/lmm/github_test/GitNexus/gitnexus/src/core/ingestion/call-processor.ts`
- `/home/lmm/github_test/GitNexus/gitnexus/src/core/ingestion/community-processor.ts`
- `/home/lmm/github_test/GitNexus/gitnexus/src/core/ingestion/process-processor.ts`

**MCP服务器**：
- `/home/lmm/github_test/GitNexus/gitnexus/src/cli/mcp.ts`
- `/home/lmm/github_test/GitNexus/gitnexus/src/mcp/server.ts`
- `/home/lmm/github_test/GitNexus/gitnexus/src/mcp/local/local-backend.ts`

**Web UI核心**：
- `/home/lmm/github_test/GitNexus/gitnexus-web/src/App.tsx`
- `/home/lmm/github_test/GitNexus/gitnexus-web/src/hooks/useSigma.ts`
- `/home/lmm/github_test/GitNexus/gitnexus-web/src/core/llm/agent.ts`

**语言解析器**：
- `/home/lmm/github_test/GitNexus/gitnexus/src/core/ingestion/languages/index.ts`
- `/home/lmm/github_test/GitNexus/gitnexus/src/core/ingestion/language-provider.ts`
- `/home/lmm/github_test/GitNexus/gitnexus/src/core/tree-sitter/parser-loader.ts`

**LadybugDB**：
- `/home/lmm/github_test/GitNexus/gitnexus/src/core/lbug/lbug-adapter.ts`
- `/home/lmm/github_test/GitNexus/gitnexus/src/core/lbug/schema.ts`

### 文档参考

**官方文档**：
- [ARCHITECTURE.md](../ARCHITECTURE.md) — 包架构、索引→图→MCP流程
- [RUNBOOK.md](../RUNBOOK.md) — 运维命令和故障恢复
- [GUARDRAILS.md](../GUARDRAILS.md) — 安全边界和操作规则
- [CONTRIBUTING.md](../CONTRIBUTING.md) — 许可、开发设置、PR流程
- [TESTING.md](../TESTING.md) — 测试命令详解

**技能文档** (`.claude/skills/gitnexus/`):
- `gitnexus-exploring/SKILL.md` — 代码探索工作流
- `gitnexus-debugging/SKILL.md` — Bug追踪工作流
- `gitnexus-impact-analysis/SKILL.md` — 影响分析工作流
- `gitnexus-refactoring/SKILL.md` — 安全重构工作流
- `gitnexus-cli/SKILL.md` — CLI命令参考
- `gitnexus-guide/SKILL.md` — 工具/资源快速参考

---

**文档结束**

> 本文档基于GitNexus v1.5.3编写，详细描述了项目的软件架构、核心技术、关键流程、编译构建和使用方法。如需更新或补充，请参考官方英文文档或直接查阅源码。