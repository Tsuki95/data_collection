# -*- coding: utf-8 -*-
# Suqi 20250117
import os
import subprocess

# Get the current directory path
current_dir = os.path.dirname(os.path.abspath(__file__))

# Define the list of scripts to run
scripts = [
    "CSD_search.py",
    "web_analysis.py",
    "xyz_download.py"
]

# Run each script in sequence
for script in scripts:
    script_path = os.path.join(current_dir, script)
    if os.path.exists(script_path):
        print(f"正在运行脚本: {script}")
        try:
            subprocess.run(["python", script_path], check=True)
            print(f"脚本 {script} 运行完成。\n")
        except subprocess.CalledProcessError as e:
            print(f"脚本 {script} 运行失败: {e}\n")
    else:
        print(f"未找到脚本: {script}")
