# GitNexus 构建脚本使用说明

## 快速开始

在 GitNexus 项目根目录下运行：

```bash
python3 build.py
```

这就是全部！脚本会自动完成所有构建步骤。

---

## 使用方法

### 完整构建（推荐）

```bash
python3 build.py
```

**执行步骤**：
1. ✅ 检查 Node.js 环境
2. ✅ 安装 gitnexus-shared 依赖
3. ✅ 构建 gitnexus-shared
4. ✅ 安装 gitnexus 主包依赖（5-10分钟）
5. ✅ 构建 gitnexus 主包
6. ✅ 验证构建结果

---

### 清理后重新构建

```bash
python3 build.py --clean
```

**适用场景**：
- 构建出现问题，需要重新开始
- 依赖版本更新后需要重新安装
- 想要完全干净的构建环境

**清理内容**：
- `gitnexus-shared/node_modules/`
- `gitnexus-shared/dist/`
- `gitnexus/node_modules/`
- `gitnexus/dist/`

---

### 跳过依赖安装（快速重新编译）

```bash
python3 build.py --skip-deps
```

**适用场景**：
- 依赖已经安装，只想重新编译
- 修改了源码，需要快速重新构建
- 开发过程中的增量构建

**执行步骤**：
1. ✅ 检查 Node.js 环境
2. ✅ 构建 gitnexus-shared
3. ✅ 构建 gitnexus 主包
4. ✅ 验证构建结果

**预计时间**: 30秒 - 1分钟（比完整构建快很多）

---

### 详细输出模式

```bash
python3 build.py --verbose
```

**适用场景**：
- 构建失败，需要查看详细错误信息
- 想要了解构建过程的每一步
- 调试构建问题

---

## 常见用法示例

### 首次构建

```bash
# 1. 克隆项目
git clone https://github.com/your-username/GitNexus.git
cd GitNexus

# 2. 运行构建脚本
python3 build.py
```

### 开发过程中重新编译

```bash
# 修改了源码后
python3 build.py --skip-deps
```

### 构建出问题，完全重头开始

```bash
python3 build.py --clean
```

### 查看详细构建过程

```bash
python3 build.py --verbose
```

---

## 输出示例

### 成功构建

```
============================================================
                   GitNexus 自动构建脚本                    
============================================================

ℹ 项目根目录: /home/user/GitNexus

[步骤 0/6] 检查环境
────────────────────────────────────────────────────────────
ℹ Node.js 版本: v20.11.0
✓ Node.js 版本满足要求 (v20.11.0)
ℹ npm 版本: 10.2.4

[步骤 1/6] 安装 gitnexus-shared 依赖
────────────────────────────────────────────────────────────
ℹ 安装 gitnexus-shared 依赖...
✓ gitnexus-shared 依赖安装完成

[步骤 2/6] 构建 gitnexus-shared
────────────────────────────────────────────────────────────
ℹ 构建 gitnexus-shared...
✓ gitnexus-shared 构建完成

[步骤 3/6] 安装 gitnexus 主包依赖（预计 5-10 分钟）
────────────────────────────────────────────────────────────
ℹ 安装 gitnexus 依赖...
✓ gitnexus 依赖安装完成

[步骤 4/6] 构建 gitnexus 主包
────────────────────────────────────────────────────────────
ℹ 构建 gitnexus...
✓ gitnexus 构建完成

[步骤 5/6] 验证构建结果
────────────────────────────────────────────────────────────
✓ dist 目录 存在
✓ CLI 入口 存在
✓ Shared 模块 存在
ℹ 测试 CLI...
✓ CLI 版本: 1.5.3

============================================================
                        构建成功！                          
============================================================

ℹ 下一步:
  1. 索引 GitNexus 自身:
     cd gitnexus && node dist/cli/index.js analyze

  2. 启动 MCP 服务器:
     cd gitnexus && node dist/cli/index.js mcp

  3. 启动 Web UI:
     cd gitnexus-web && npm run dev
```

---

## 故障排除

### 问题1: `python3: command not found`

**解决方法**：
```bash
# Ubuntu/Debian
sudo apt-get install python3

# CentOS/RHEL
sudo yum install python3

# macOS
brew install python3
```

---

### 问题2: `Node.js 未安装`

**解决方法**：
```bash
# 使用 nvm 安装（推荐）
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
nvm install 20
nvm use 20

# 或直接安装
# Ubuntu/Debian
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# macOS
brew install node@20
```

---

### 问题3: `Node.js 版本过低`

**解决方法**：
```bash
# 使用 nvm 升级
nvm install 20
nvm use 20

# 或安装 Node.js >= 20.0.0
```

---

### 问题4: 依赖安装超时

**症状**：
```
✗ 命令超时: npm install
```

**解决方法**：
```bash
# 使用国内镜像
npm config set registry https://registry.npmmirror.com

# 重新运行构建
python3 build.py --clean
```

---

### 问题5: 构建失败，想查看详细错误

**解决方法**：
```bash
python3 build.py --verbose
```

---

## 高级用法

### 组合参数

```bash
# 清理后详细构建
python3 build.py --clean --verbose

# 快速重新编译，显示详细输出
python3 build.py --skip-deps --verbose
```

---

## 脚本特性

✅ **自动环境检查**: 检查 Node.js 和 npm 版本  
✅ **彩色输出**: 成功/错误/警告信息清晰区分  
✅ **进度显示**: 显示当前步骤和总步骤数  
✅ **错误处理**: 任何步骤失败都会停止并报告  
✅ **超时保护**: npm install 超时设置为 10 分钟  
✅ **构建验证**: 自动验证构建结果  
✅ **用户友好**: 提供下一步操作提示  

---

## 与手动构建对比

### 手动构建（需要记住很多命令）

```bash
cd gitnexus-shared
npm install
npm run build

cd ../gitnexus
npm install
npm run build

node dist/cli/index.js --version
```

### 自动构建（一条命令）

```bash
python3 build.py
```

**优势**：
- ✅ 不需要记忆命令
- ✅ 自动检查环境
- ✅ 自动验证结果
- ✅ 彩色输出更清晰
- ✅ 错误提示更友好

---

## 脚本源码

查看脚本源码：

```bash
cat build.py
```

或在线查看：
```
https://github.com/your-username/GitNexus/blob/main/build.py
```

---

## 反馈与贡献

如果构建脚本有问题，欢迎：
- 提交 Issue: https://github.com/your-username/GitNexus/issues
- 提交 PR 改进脚本

---

**祝构建顺利！** 🎉