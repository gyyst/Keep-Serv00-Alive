import os
import time
from datetime import datetime
import random
import sys

def update_status_file():
    """更新status.md文件，添加时间戳"""
    status_path = 'keepAlive/status.md'
    
    # 检查status文件是否存在
    if not os.path.exists(status_path):
        with open(status_path, 'w', encoding='utf-8') as f:
            f.write('# Keep-Serv00-Alive 状态文件\n\n')
    
    # 读取现有内容
    with open(status_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找并更新或添加时间戳部分
    timestamp_section = '## 最后更新时间\n'
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    new_timestamp_line = f'最后活动时间: {current_time}\n'
    
    if '## 最后更新时间' in content:
        # 更新现有时间戳
        lines = content.split('\n')
        updated_lines = []
        in_timestamp_section = False
        timestamp_updated = False
        
        for line in lines:
            if line.startswith('## 最后更新时间'):
                in_timestamp_section = True
                updated_lines.append(line)
            elif in_timestamp_section and line.startswith('最后活动时间:'):
                updated_lines.append(new_timestamp_line.strip())
                timestamp_updated = True
            elif line.startswith('##') and in_timestamp_section:
                if not timestamp_updated:
                    updated_lines.append(new_timestamp_line.strip())
                in_timestamp_section = False
                updated_lines.append(line)
            else:
                updated_lines.append(line)
        
        if in_timestamp_section and not timestamp_updated:
            updated_lines.append(new_timestamp_line.strip())
        
        updated_content = '\n'.join(updated_lines)
    else:
        # 添加新的时间戳部分
        updated_content = content
        if not updated_content.endswith('\n\n'):
            if updated_content.endswith('\n'):
                updated_content += '\n'
            else:
                updated_content += '\n\n'
        
        updated_content += timestamp_section + new_timestamp_line
    
    # 写回文件
    with open(status_path, 'w', encoding='utf-8') as f:
        f.write(updated_content)
    
    print(f"status.md 已更新，添加时间戳: {current_time}")

def create_keepalive_file():
    """创建一个包含当前时间戳的文件"""
    keepalive_dir = 'keepAlive'
    os.makedirs(keepalive_dir, exist_ok=True)
    
    # 清理旧文件，只保留最新的5个文件
    cleanup_old_files(keepalive_dir, keep_count=0)
    
    # 创建新的时间戳文件
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    random_suffix = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=5))
    filename = f"{keepalive_dir}/keepalive_{timestamp}_{random_suffix}.txt"
    
    with open(filename, 'w') as f:
        f.write(f"Repository activity timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"This file was automatically generated to keep the GitHub Actions cron jobs active.\n")
    
    print(f"已创建活动文件: {filename}")
    return filename

def cleanup_old_files(directory, keep_count=5, file_prefix='keepalive_'):
    """保留指定目录中最新的几个文件，删除其余文件
    
    Args:
        directory (str): 要清理的目录路径
        keep_count (int): 要保留的最新文件数量
        file_prefix (str): 要清理的文件前缀，默认为'keepalive_'
    
    Returns:
        int: 删除的文件数量
    """
    if not os.path.exists(directory):
        print(f"目录不存在: {directory}")
        return 0
    
    files = [os.path.join(directory, f) for f in os.listdir(directory) 
             if os.path.isfile(os.path.join(directory, f)) and f.startswith(file_prefix)]
    
    # 按修改时间排序
    files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    
    # 删除旧文件
    deleted_count = 0
    for old_file in files[keep_count:]:
        try:
            os.remove(old_file)
            print(f"已删除旧文件: {old_file}")
            deleted_count += 1
        except Exception as e:
            print(f"删除文件失败 {old_file}: {str(e)}")
    
    return deleted_count

def cleanup_all_txt_files(directory='keepAlive', keep_count=5):
    """清理指定目录中的所有txt文件，只保留最新的几个
    
    Args:
        directory (str): 要清理的目录路径，默认为'keepAlive'
        keep_count (int): 要保留的最新文件数量，默认为5
    """
    print(f"开始清理 {directory} 目录中的旧txt文件...")
    deleted_count = cleanup_old_files(directory, keep_count, file_prefix='keepalive_')
    print(f"清理完成，共删除 {deleted_count} 个旧文件，保留 {keep_count} 个最新文件")

def main():
    # 检查命令行参数
    if len(sys.argv) > 1 and sys.argv[1] == 'cleanup':
        # 如果有额外参数指定保留数量
        keep_count = 5  # 默认值
        if len(sys.argv) > 2 and sys.argv[2].isdigit():
            keep_count = int(sys.argv[2])
        cleanup_all_txt_files(keep_count=keep_count)
        return
    
    print(f"开始执行保活任务: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 更新状态文件
    update_status_file()
    
    # 创建时间戳文件
    created_file = create_keepalive_file()
    
    print(f"保活任务完成: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"已更新status.md并创建文件: {created_file}")

if __name__ == '__main__':
    main()