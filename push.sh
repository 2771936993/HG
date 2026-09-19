#!/bin/bash
cd /www/wwwroot/adguard-rules

git add hg.txt hg1.txt hg2.txt yx.txt
git commit -m "自动同步 AdGuard 规则 $(date '+%Y-%m-%d %H:%M')" || exit 0
git push
