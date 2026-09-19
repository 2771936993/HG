import requests
import chardet
import subprocess
import os
import time
import socket
from datetime import datetime
from pathlib import Path

# 获取脚本所在目录
SCRIPT_DIR = Path(__file__).parent

# Git 用户配置
GIT_EMAIL = "2771936993@qq.com"
GIT_NAME = "2771936993"

file_urls = {
    "http://10.10.10.251/hg.txt": "hg.txt",
    "http://10.10.10.251/hg1.txt": "hg1.txt",
    "http://10.10.10.251/hg2.txt": "hg2.txt",
    "http://10.10.10.251/yx.txt": "yx.txt",
}

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Referer": "http://10.10.10.251/"
}

def wait_for_network(host='10.10.10.251', port=80, timeout=60):
    """等待目标主机网络就绪"""
    start = time.time()
    print(f"等待网络连接 {host}:{port}...")
    while time.time() - start < timeout:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            result = sock.connect_ex((host, port))
            sock.close()
            if result == 0:
                print(f"✓ 网络已就绪，能连接到 {host}:{port}")
                return True
        except:
            pass
        print(f"  等待中... ({int(time.time() - start)}s)")
        time.sleep(3)
    print(f"✗ 等待超时 {timeout}秒，{host}:{port} 仍不可达")
    return False

def wait_for_github(timeout=30):
    """等待 GitHub 可访问"""
    start = time.time()
    print(f"等待 GitHub 连接...")
    while time.time() - start < timeout:
        try:
            socket.create_connection(("github.com", 80), timeout=3)
            print("✓ GitHub 网络已就绪")
            return True
        except:
            pass
        print(f"  等待 GitHub... ({int(time.time() - start)}s)")
        time.sleep(2)
    print("✗ GitHub 连接超时")
    return False

def is_rule(line: str) -> bool:
    line = line.strip()
    if not line or line.startswith(("!", "#", "[Adblock")):
        return False
    return True

def git_push(retry_count=3):
    """自动提交并推送到 GitHub，支持重试"""
    os.chdir(SCRIPT_DIR)
    
    # 先等待 GitHub 可访问
    if not wait_for_github():
        print("  GitHub 不可达，跳过本次推送")
        return False
    
    for attempt in range(retry_count):
        print(f"  Git 推送尝试 {attempt + 1}/{retry_count}")
        
        # 配置 Git 用户信息
        subprocess.run(["git", "config", "user.email", GIT_EMAIL], capture_output=True)
        subprocess.run(["git", "config", "user.name", GIT_NAME], capture_output=True)
        
        # 拉取远程最新代码
        subprocess.run(["git", "pull", "origin", "main"], capture_output=True, text=True)
        
        # 添加所有更改
        subprocess.run(["git", "add", "."], capture_output=True, text=True)
        
        # 提交
        commit_msg = f"auto sync rules {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        result = subprocess.run(["git", "commit", "-m", commit_msg], capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"  ✓ 已提交: {commit_msg}")
            # 推送
            push_result = subprocess.run(["git", "push", "origin", "main"], capture_output=True, text=True)
            if push_result.returncode == 0:
                print("  ✓ Git 推送成功")
                return True
            else:
                print(f"  ✗ Git 推送失败: {push_result.stderr}")
                if attempt < retry_count - 1:
                    print(f"  等待 5 秒后重试...")
                    time.sleep(5)
        else:
            if "nothing to commit" in result.stderr:
                print("   没有需要提交的更改")
                return True
            else:
                print(f"  ✗ Git 提交失败: {result.stderr}")
                if attempt < retry_count - 1:
                    time.sleep(3)
    
    print("  ✗ Git 推送最终失败")
    return False

def sync_with_retry(max_retries=3):
    """带重试的主同步函数"""
    for attempt in range(max_retries):
        print(f"\n同步尝试 {attempt + 1}/{max_retries}")
        
        try:
            # 等待内网服务器网络就绪
            if not wait_for_network():
                if attempt < max_retries - 1:
                    print("  等待 10 秒后重试...")
                    time.sleep(10)
                    continue
                else:
                    print("✗ 内网服务器连接失败，放弃本次同步")
                    return False
            
            # 执行同步
            sync()
            return True
            
        except requests.exceptions.ConnectionError as e:
            print(f"  ✗ 连接错误: {e}")
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 10
                print(f"  等待 {wait_time} 秒后重试...")
                time.sleep(wait_time)
            else:
                print("✗ 同步失败，已达最大重试次数")
                return False
        except Exception as e:
            print(f"  ✗ 未知错误: {e}")
            if attempt < max_retries - 1:
                time.sleep(5)
            else:
                return False
    
    return False

def sync():
    """原有的同步逻辑"""
    session = requests.Session()
    beijing = datetime.utcnow().timestamp() + 8 * 3600
    update_time = datetime.fromtimestamp(beijing).strftime("%Y-%m-%d %H:%M:%S")

    for url, fname in file_urls.items():
        print(f"同步 {fname}")
        
        # 使用带超时的请求
        r = session.get(url, headers=headers, timeout=30)
        r.raise_for_status()

        enc = chardet.detect(r.content)["encoding"] or "utf-8"
        lines = r.content.decode(enc, errors="ignore").splitlines()

        filtered = [l for l in lines if not l.strip().startswith(("! Version:", "! Total count:"))]
        cnt = sum(1 for l in filtered if is_rule(l))

        out = (
            f"! Version:    最后同步时间: {update_time}\n"
            f"! Total count: {cnt}\n"
            + "\n".join(filtered)
        )
        
        file_path = SCRIPT_DIR / fname
        file_path.write_text(out, encoding="utf-8")
        print(f"  ✓ {fname}  {cnt} 条")

    print("\n" + "="*40)
    print("开始 Git 推送...")
    git_push()
    print("="*40)

if __name__ == "__main__":
    print(f"执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*40)
    
    success = sync_with_retry(max_retries=3)
    
    if not success:
        print("\n✗ 同步失败，请检查网络连接")
        exit(1)
    else:
        print("\n✓ 同步完成")
        exit(0)