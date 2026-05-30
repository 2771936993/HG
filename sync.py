import requests
import chardet
from datetime import datetime
from pathlib import Path

file_urls = {
    "http://hgzs.uunat.com/hg.txt": "hg.txt",
    "http://hgzs.uunat.com/hg1.txt": "hg1.txt",
    "http://hgzs.uunat.com/hg2.txt": "hg2.txt",
    "http://hgzs.uunat.com/yx.txt": "yx.txt",
}

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Referer": "http://hgzs.uunat.com/"
}

def is_rule(line: str) -> bool:
    line = line.strip()
    if not line or line.startswith(("!", "#", "[Adblock")):
        return False
    return True

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
        Path(fname).write_text(out, encoding="utf-8")
        print(f"  ✓ {fname}  {cnt} 条")

if __name__ == "__main__":
    sync()
