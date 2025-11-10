#!/usr/bin/env python3
"""
诊断脚本：检查二进制文件的状态
"""
import os
import sys
import subprocess

def check_file(filepath):
    """检查文件的各种属性"""
    
    print("=" * 70)
    print(f"检查文件: {filepath}")
    print("=" * 70)
    
    # 1. 检查文件是否存在
    if not os.path.exists(filepath):
        print("❌ 文件不存在!")
        return
    print("✅ 文件存在")
    
    # 2. 检查文件权限
    stat_info = os.stat(filepath)
    mode = stat_info.st_mode
    print(f"\n文件权限: {oct(mode)}")
    
    # 检查是否可执行
    is_executable = os.access(filepath, os.X_OK)
    if is_executable:
        print("✅ 文件具有可执行权限")
    else:
        print("❌ 文件没有可执行权限!")
        print(f"   修复命令: chmod +x {filepath}")
    
    # 3. 检查文件类型
    try:
        result = subprocess.run(['file', filepath], capture_output=True, text=True)
        print(f"\n文件类型: {result.stdout.strip()}")
    except Exception as e:
        print(f"⚠️  无法检查文件类型: {e}")
    
    # 4. 检查隔离属性 (macOS only - 这很重要!)
    if sys.platform == 'darwin':
        print("\n检查隔离属性 (Quarantine)...")
        try:
            result = subprocess.run(
                ['xattr', '-l', filepath],
                capture_output=True,
                text=True,
                timeout=5
            )
            if 'com.apple.quarantine' in result.stdout:
                print("❌ 文件具有隔离属性 (这会导致程序被杀死!)")
                print("   修复命令: xattr -d com.apple.quarantine " + filepath)
            else:
                print("✅ 文件没有隔离属性")
        except Exception as e:
            print(f"⚠️  无法检查隔离属性: {e}")
    
    # 5. 检查代码签名 (macOS only)
    if sys.platform == 'darwin':
        print("\n检查代码签名...")
        try:
            result = subprocess.run(
                ['codesign', '-dvv', filepath],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                stderr = result.stderr
                print("✅ 文件已签名:")
                print(stderr)
                
                # 检查签名类型
                if 'adhoc' in stderr.lower():
                    print("\n✅ 这是 adhoc 签名（正常，ARM64 程序需要签名才能运行）")
                elif 'linker-signed' in stderr.lower():
                    print("\n✅ 这是 linker 签名（正常，ARM64 程序需要签名才能运行）")
                else:
                    print("\n⚠️  这是开发者签名（修改后需要重新签名）")
                    print(f"   重新签名: codesign -s - -f {filepath}")
                
                # 验证签名有效性
                verify_result = subprocess.run(
                    ['codesign', '-v', filepath],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if verify_result.returncode == 0:
                    print("✅ 签名有效")
                else:
                    print("❌ 签名已失效（文件被修改后签名会失效）")
                    print(f"   重新签名: codesign -s - -f {filepath}")
            else:
                print("❌ 文件未签名")
                print("⚠️  在 Apple Silicon (ARM64) 上，未签名的程序无法运行!")
                print(f"   修复命令: codesign -s - {filepath}")
        except Exception as e:
            print(f"⚠️  无法检查签名: {e}")
    
    # 6. 尝试执行文件
    print("\n尝试执行文件 (超时5秒)...")
    print("💡 如果程序需要用户输入，会显示为超时（这是正常的）")
    try:
        result = subprocess.run(
            [filepath],
            capture_output=True,
            text=True,
            timeout=5
        )
        print(f"退出代码: {result.returncode}")
        if result.stdout:
            print(f"标准输出:\n{result.stdout}")
        if result.stderr:
            print(f"标准错误:\n{result.stderr}")
            
        if result.returncode == 0:
            print("✅ 程序成功执行")
        elif result.returncode == -9:
            print("❌ 程序被系统杀死 (SIGKILL)!")
            print("   可能原因:")
            print("   1. 隔离属性 (Quarantine) - 最常见")
            print("   2. 二进制文件损坏")
            print("   3. 代码签名失效")
            print("\n   立即修复:")
            print(f"   xattr -d com.apple.quarantine {filepath}")
            print(f"   codesign --remove-signature {filepath}")
        else:
            print(f"⚠️  程序执行失败，退出代码: {result.returncode}")
            
    except subprocess.TimeoutExpired:
        print("⚠️  程序执行超时")
        print("💡 这通常意味着程序正常启动并等待用户输入（这是好的！）")
        print("   如果程序因签名问题无法运行，会立即被杀死（退出代码 -9）")
    except Exception as e:
        print(f"❌ 无法执行程序: {e}")
        print(f"   错误类型: {type(e).__name__}")
    
    # 7. 检查依赖库 (macOS/Linux)
    if sys.platform == 'darwin':
        print("\n检查动态库依赖...")
        try:
            result = subprocess.run(
                ['otool', '-L', filepath],
                capture_output=True,
                text=True,
                timeout=5
            )
            print(result.stdout)
        except Exception as e:
            print(f"⚠️  无法检查依赖: {e}")
    
    # 8. 提供快速修复命令
    print("\n" + "=" * 70)
    print("🔧 快速修复命令 (如果程序无法运行):")
    print("=" * 70)
    if sys.platform == 'darwin':
        print(f"# 1. 移除隔离属性 (如果有)")
        print(f"xattr -d com.apple.quarantine {filepath}")
        print(f"\n# 2. 重新签名 (ARM64 必须!)")
        print(f"codesign -s - -f {filepath}")
        print(f"\n# 3. 验证签名")
        print(f"codesign -v {filepath}")
        print(f"\n# 4. 确保可执行权限")
        print(f"chmod +x {filepath}")
        print(f"\n# 5. 运行程序")
        print(f"{filepath}")
        print(f"\n💡 重要说明:")
        print(f"   - ARM64 程序必须有签名才能运行")
        print(f"   - 修改程序后必须重新签名")
        print(f"   - 'codesign -s -' 创建 adhoc 签名（无需开发者证书）")
    
    print("\n" + "=" * 70)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: python3 diagnose.py <binary_file>")
        print("示例: python3 diagnose.py /path/to/test")
        sys.exit(1)
    
    filepath = sys.argv[1]
    check_file(filepath)

