#!/bin/bash

# 定义要下载的URL列表（可自行添加更多）
URLS=(
#海哥
    "http://10.10.10.251/hg1.txt"
    #海哥哥
    "http://10.10.10.251/2.txt"
)

# 输出目录
OUTPUT_DIR="/www/wwwroot/10.10.10.251"
# 临时文件
TEMP_FILE="$OUTPUT_DIR/temp_combined.txt"
# 最终输出文件
OUTPUT_FILE="$OUTPUT_DIR/hg1.txt"

# 确保输出目录存在
mkdir -p "$OUTPUT_DIR"

# 清空临时文件
> "$TEMP_FILE"

# 逐个下载并合并文件
for url in "${URLS[@]}"; do
    echo "正在下载: $url"
    if curl -s "$url" >> "$TEMP_FILE"; then
        echo "下载成功: $url"
    else
        echo "下载失败: $url (可能URL无效或网络问题)"
    fi
done

# 计算原始总行数
original_lines=$(wc -l < "$TEMP_FILE")

# 使用 awk 去重，强制使用C locale避免编码警告
LC_ALL=C awk '{
    # 初始化key为整行
    key = $0
    
    # 查找 | 和 ^ 的位置
    pipe_pos = index($0, "|")
    caret_pos = index($0, "^")
    
    # 如果同时存在 | 和 ^，且 | 在 ^ 之前
    if (pipe_pos > 0 && caret_pos > 0 && pipe_pos < caret_pos) {
        # 提取 | 到 ^ 之间的内容
        key = substr($0, pipe_pos + 1, caret_pos - pipe_pos - 1)
    }
    
    # 如果这个键还没有出现过，则输出整行并记录
    if (!seen[key]++) {
        print
    }
}' "$TEMP_FILE" > "$OUTPUT_FILE"

# 计算去重后行数
unique_lines=$(wc -l < "$OUTPUT_FILE")

# 计算去重数量
removed=$((original_lines - unique_lines))

# 输出统计信息
echo "----------------------------------"
echo "所有文件已合并并去重，结果保存在: $OUTPUT_FILE"
echo "原始总行数: $original_lines"
echo "去重后行数: $unique_lines"
echo "去除的重复行数: $removed"

# 清理临时文件
rm "$TEMP_FILE"

# 检查文件是否成功生成
if [ -f "$OUTPUT_FILE" ]; then
    echo "文件已成功生成并替换: $OUTPUT_FILE"
else
    echo "警告: 文件生成失败"
fi