import requests
import hashlib
import os
import base64
from multiprocessing import Pool, cpu_count
from config import config
from typing import Dict, List

# 获取文件列表
def fetch_remote_files() -> List[Dict[str, str]]:
    try:
        resp = requests.get(f"{config.api_url}/api/filelist", params={'node': config.node_uuid}, timeout=10)
        if resp.status_code == 200:
            return resp.json().get('data', [])
    except Exception as e:
        print(f'获取远程文件列表失败: {str(e)}')
    return []


# 计算文件哈希值
def calculate_hash(fpath: str) -> str:
    with open(fpath, 'rb') as f:
        return hashlib.new('sha256', f.read()).hexdigest()

# 获取本地文件列表
def get_local_files() -> Dict[str, str]:
    file_map = {}
    with Pool(cpu_count()) as pool:
        target_dir = os.path.abspath(config.workdir)
        files = []
        for root, dirs, filenames in os.walk(target_dir):
            rel_root = os.path.relpath(root, config.workdir)
            for f in filenames:
                full_path = os.path.join(rel_root, f).replace('\\', '/')
                files.append(config.workdir+"/"+full_path)

        hashes = pool.map(calculate_hash, files)
        
        for fname, fhash in zip(files, hashes):
            file_map[os.path.basename(fname)] = fhash
    return file_map

# 下载文件
def download_file(task: Dict[str, str]) -> bool:
    filename = task['filename']
    expected_hash = task['hash']
    
    for attempt in range(config.max_retry + 1):
        try:
            params = {'name': filename, 'hash': expected_hash, 'node': config.node_uuid}
            resp = requests.get(f"{config.api_url}/api/get", 
                              params=params, timeout=30)
            
            if resp.status_code != 200:
                continue
                
            data = resp.json()
            if data.get('code') != 200:
                continue
                
            file_data = base64.b64decode(data['filedata'])
            received_hash = hashlib.sha256(file_data).hexdigest()
            
            if received_hash != expected_hash:
                print(f'文件哈希不匹配: {filename}')
                continue
                
            dest_path = os.path.join(config.workdir, filename)
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            with open(dest_path, 'wb') as f:
                f.write(file_data)
                
            print(f'成功下载: {filename}')
            return True
            
        except Exception as e:
            print(f'下载失败 ({attempt+1}/{config.max_retry}): {str(e)}')
    
    print(f'文件下载失败已达到最大重试次数: {filename}')
    return False


def main():
    remote_files = {item['filename']: item['hash'] 
                   for item in fetch_remote_files()}
    local_files = get_local_files()
    
    # 生成需要下载的任务列表
    download_tasks = []
    for filename, remote_hash in remote_files.items():
        local_hash = local_files.get(filename)
        if local_hash != remote_hash:
            download_tasks.append({'filename': filename, 'hash': remote_hash})
    
    # 多进程下载
    with Pool(cpu_count()) as pool:
        results = pool.map(download_file, download_tasks)
        
    success_count = sum(results)
    print(f'同步完成，成功下载 {success_count}/{len(download_tasks)} 个文件')


if __name__ == '__main__':
    main()