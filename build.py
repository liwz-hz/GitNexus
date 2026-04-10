#!/usr/bin/env python3
"""
GitNexus 自动构建脚本

一键完成所有构建步骤：
1. 检查环境（Node.js版本）
2. 安装 gitnexus-shared 依赖
3. 构建 gitnexus-shared
4. 安装 gitnexus 主包依赖
5. 构建 gitnexus 主包
6. 验证构建结果

用法:
    python3 build.py              # 完整构建
    python3 build.py --clean      # 清理后重新构建
    python3 build.py --skip-deps  # 跳过依赖安装（只重新编译）
    python3 build.py --verbose    # 详细输出
"""

import os
import sys
import subprocess
import argparse
import shutil
from pathlib import Path
from typing import Optional, List

# 颜色代码
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    RESET = '\033[0m'

def print_header(text: str):
    """打印标题"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text.center(60)}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.RESET}\n")

def print_step(step: int, total: int, text: str):
    """打印步骤"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}[步骤 {step}/{total}]{Colors.RESET} {text}")
    print(f"{Colors.YELLOW}{'─'*60}{Colors.RESET}")

def print_success(text: str):
    """打印成功信息"""
    print(f"{Colors.GREEN}✓ {text}{Colors.RESET}")

def print_error(text: str):
    """打印错误信息"""
    print(f"{Colors.RED}✗ {text}{Colors.RESET}", file=sys.stderr)

def print_warning(text: str):
    """打印警告信息"""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.RESET}")

def print_info(text: str):
    """打印信息"""
    print(f"{Colors.CYAN}ℹ {text}{Colors.RESET}")

def run_command(
    cmd: List[str],
    cwd: Optional[Path] = None,
    verbose: bool = False,
    timeout: Optional[int] = None
) -> tuple[bool, str]:
    """
    运行命令
    
    Args:
        cmd: 命令列表
        cwd: 工作目录
        verbose: 是否显示详细输出
        timeout: 超时时间（秒）
    
    Returns:
        (是否成功, 输出内容)
    """
    try:
        if verbose:
            print(f"{Colors.MAGENTA}$ {' '.join(cmd)}{Colors.RESET}")
        
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=not verbose,
            text=True,
            timeout=timeout
        )
        
        if result.returncode == 0:
            return True, result.stdout if not verbose else ""
        else:
            error_msg = result.stderr if not verbose else ""
            print_error(f"命令失败: {' '.join(cmd)}")
            if error_msg:
                print_error(error_msg)
            return False, error_msg
            
    except subprocess.TimeoutExpired:
        print_error(f"命令超时: {' '.join(cmd)}")
        return False, "Timeout"
    except FileNotFoundError:
        print_error(f"命令不存在: {cmd[0]}")
        return False, f"Command not found: {cmd[0]}"
    except Exception as e:
        print_error(f"执行命令时出错: {e}")
        return False, str(e)

def check_node_version() -> bool:
    """检查Node.js版本"""
    print_step(0, 6, "检查环境")
    
    # 检查Node.js是否安装
    success, output = run_command(["node", "--version"])
    if not success:
        print_error("Node.js 未安装，请先安装 Node.js >= 20.0.0")
        return False
    
    version = output.strip()
    print_info(f"Node.js 版本: {version}")
    
    # 检查版本号
    major_version = int(version.lstrip('v').split('.')[0])
    if major_version < 20:
        print_error(f"Node.js 版本过低 ({version})，需要 >= 20.0.0")
        return False
    
    print_success(f"Node.js 版本满足要求 ({version})")
    
    # 检查npm
    success, output = run_command(["npm", "--version"])
    if not success:
        print_error("npm 未安装")
        return False
    
    print_info(f"npm 版本: {output.strip()}")
    
    return True

def install_dependencies(pkg_dir: Path, verbose: bool = False) -> bool:
    """安装依赖"""
    print_info(f"安装 {pkg_dir.name} 依赖...")
    
    cmd = ["npm", "install"]
    if verbose:
        cmd.append("--verbose")
    
    # npm install 可能很慢，设置较长的超时时间（10分钟）
    success, _ = run_command(cmd, cwd=pkg_dir, verbose=verbose, timeout=600)
    
    if success:
        print_success(f"{pkg_dir.name} 依赖安装完成")
    else:
        print_error(f"{pkg_dir.name} 依赖安装失败")
    
    return success

def build_package(pkg_dir: Path, verbose: bool = False) -> bool:
    """构建包"""
    print_info(f"构建 {pkg_dir.name}...")
    
    cmd = ["npm", "run", "build"]
    success, _ = run_command(cmd, cwd=pkg_dir, verbose=verbose, timeout=300)
    
    if success:
        print_success(f"{pkg_dir.name} 构建完成")
    else:
        print_error(f"{pkg_dir.name} 构建失败")
    
    return success

def clean_build(root_dir: Path):
    """清理构建产物"""
    print_step(0, 6, "清理构建产物")
    
    dirs_to_clean = [
        root_dir / "gitnexus-shared" / "node_modules",
        root_dir / "gitnexus-shared" / "dist",
        root_dir / "gitnexus" / "node_modules",
        root_dir / "gitnexus" / "dist",
    ]
    
    for dir_path in dirs_to_clean:
        if dir_path.exists():
            print_info(f"删除 {dir_path.relative_to(root_dir)}")
            shutil.rmtree(dir_path)
    
    print_success("清理完成")

def verify_build(gitnexus_dir: Path) -> bool:
    """验证构建结果"""
    print_step(6, 6, "验证构建结果")
    
    # 检查关键文件
    checks = [
        ("dist 目录", gitnexus_dir / "dist"),
        ("CLI 入口", gitnexus_dir / "dist" / "cli" / "index.js"),
        ("Shared 模块", gitnexus_dir / "dist" / "_shared" / "index.js"),
    ]
    
    all_passed = True
    for name, path in checks:
        if path.exists():
            print_success(f"{name} 存在")
        else:
            print_error(f"{name} 不存在: {path}")
            all_passed = False
    
    if not all_passed:
        return False
    
    # 测试CLI
    print_info("测试 CLI...")
    success, output = run_command(
        ["node", "dist/cli/index.js", "--version"],
        cwd=gitnexus_dir
    )
    
    if success:
        print_success(f"CLI 版本: {output.strip()}")
        return True
    else:
        print_error("CLI 测试失败")
        return False

def main():
    parser = argparse.ArgumentParser(
        description="GitNexus 自动构建脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    python build.py              # 完整构建
    python build.py --clean      # 清理后重新构建
    python build.py --skip-deps  # 跳过依赖安装（只重新编译）
    python build.py --verbose    # 详细输出
        """
    )
    
    parser.add_argument(
        "--clean",
        action="store_true",
        help="清理构建产物后重新构建"
    )
    
    parser.add_argument(
        "--skip-deps",
        action="store_true",
        help="跳过依赖安装（只重新编译）"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="显示详细输出"
    )
    
    args = parser.parse_args()
    
    # 获取项目根目录
    root_dir = Path(__file__).parent.absolute()
    gitnexus_shared_dir = root_dir / "gitnexus-shared"
    gitnexus_dir = root_dir / "gitnexus"
    
    # 检查目录是否存在
    if not gitnexus_shared_dir.exists():
        print_error(f"找不到 gitnexus-shared 目录: {gitnexus_shared_dir}")
        sys.exit(1)
    
    if not gitnexus_dir.exists():
        print_error(f"找不到 gitnexus 目录: {gitnexus_dir}")
        sys.exit(1)
    
    print_header("GitNexus 自动构建脚本")
    print_info(f"项目根目录: {root_dir}")
    
    # 清理
    if args.clean:
        clean_build(root_dir)
    
    # 步骤0: 检查环境
    if not check_node_version():
        sys.exit(1)
    
    total_steps = 6 if not args.skip_deps else 4
    current_step = 1
    
    try:
        # 步骤1: 安装 gitnexus-shared 依赖
        if not args.skip_deps:
            print_step(current_step, total_steps, "安装 gitnexus-shared 依赖")
            if not install_dependencies(gitnexus_shared_dir, args.verbose):
                sys.exit(1)
            current_step += 1
        
        # 步骤2: 构建 gitnexus-shared
        print_step(current_step, total_steps, "构建 gitnexus-shared")
        if not build_package(gitnexus_shared_dir, args.verbose):
            sys.exit(1)
        current_step += 1
        
        # 步骤3: 安装 gitnexus 主包依赖
        if not args.skip_deps:
            print_step(current_step, total_steps, "安装 gitnexus 主包依赖（预计 5-10 分钟）")
            if not install_dependencies(gitnexus_dir, args.verbose):
                sys.exit(1)
            current_step += 1
        
        # 步骤4: 构建 gitnexus 主包
        print_step(current_step, total_steps, "构建 gitnexus 主包")
        if not build_package(gitnexus_dir, args.verbose):
            sys.exit(1)
        current_step += 1
        
        # 步骤5: 验证构建
        print_step(current_step, total_steps, "验证构建结果")
        if not verify_build(gitnexus_dir):
            sys.exit(1)
        
        # 成功完成
        print_header("构建成功！")
        print_info("下一步:")
        print(f"  {Colors.BOLD}1.{Colors.RESET} 索引 GitNexus 自身:")
        print(f"     {Colors.CYAN}cd gitnexus && node dist/cli/index.js analyze{Colors.RESET}")
        print(f"\n  {Colors.BOLD}2.{Colors.RESET} 启动 MCP 服务器:")
        print(f"     {Colors.CYAN}cd gitnexus && node dist/cli/index.js mcp{Colors.RESET}")
        print(f"\n  {Colors.BOLD}3.{Colors.RESET} 启动 Web UI:")
        print(f"     {Colors.CYAN}cd gitnexus-web && npm run dev{Colors.RESET}")
        print()
        
    except KeyboardInterrupt:
        print_error("\n构建被用户中断")
        sys.exit(1)
    except Exception as e:
        print_error(f"构建过程中出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()