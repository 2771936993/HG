import requests
import chardet
import subprocess
import os
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

def is_rule(line: str) -> bool:
    line = line.strip()
    if not line or line.startswith(("!", "#", "[Adblock")):
        return False
    return True

def git_push():
    """自动提交并推送到 GitHub"""
    os.chdir(SCRIPT_DIR)
    
    # 配置 Git 用户信息（防止未配置的情况）
    subprocess.run(["git", "config", "user.email", GIT_EMAIL], capture_output=True)
    subprocess.run(["git", "config", "user.name", GIT_NAME], capture_output=True)
    
    # 拉取远程最新代码（兼容老版本 Git）
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
        else:
            print(f"  ✗ Git 推送失败: {push_result.stderr}")
    else:
        if "nothing to commit" in result.stderr:
            print("   没有需要提交的更改")
        else:
            print(f"  ✗ Git 提交失败: {result.stderr}")

def sync():
    session = requests.Session()
    beijing = datetime.utcnow().timestamp() + 8 * 3600
    update_time = datetime.fromtimestamp(beijing).strftime("%Y-%m-%d %H:%M:%S")

    for url, fname in file_urls.items():
        print(f"同步 {fname}")
        r = session.get(url, headers=headers, timeout=60)
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
        
        # 保存到脚本所在目录
        file_path = SCRIPT_DIR / fname
        file_path.write_text(out, encoding="utf-8")
        print(f"  ✓ {fname}  {cnt} 条")

    print("\n" + "="*40)
    print("开始 Git 推送...")
    git_push()
    print("="*40)

if __name__ == "__main__":
    sync()
