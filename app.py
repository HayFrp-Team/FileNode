from fastapi import FastAPI, Request, HTTPException, status, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
import os
import hashlib
import time
import threading
import subprocess
from config import config
from pathlib import Path

app = FastAPI()

# 同步锁和时间记录
last_sync_time = 0
sync_lock = threading.Lock()

# 确保上传目录存在
os.makedirs(config.workdir, exist_ok=True)

# 计算文件哈希值
def calculate_hash(fpath: str) -> str:
    with open(fpath, 'rb') as f:
        return hashlib.new('sha256', f.read()).hexdigest()

@app.get("/api/list")
async def list_files(request: Request):
    base_path = request.query_params.get('path', '')
    target_dir = os.path.abspath(os.path.join(config.workdir, base_path))
    
    if not target_dir.startswith(os.path.abspath(config.workdir)):
        return JSONResponse(status_code=400, content={"code": 400, "msg": "非法路径请求"})
    
    files = []
    for root, dirs, filenames in os.walk(target_dir):
        rel_root = os.path.relpath(root, config.workdir)
        for f in filenames:
            full_path = os.path.join(rel_root, f).replace('\\', '/')
            files.append(full_path)
    
    return {
        "code": 200,
        "files": sorted(files),
        "node": config.node_uuid,
        "msg": "success"
    }

@app.get("/api/info/{filename:path}")
async def get_file_info(request: Request, filename: str):
    full_path = os.path.abspath(os.path.join(config.workdir, filename))
    if not full_path.startswith(os.path.abspath(config.workdir)) or not os.path.isfile(full_path):
        raise HTTPException(status_code=404, detail="文件不存在")
    
    file_hash = calculate_hash(full_path)
    base_url = str(request.base_url)
    from starlette.datastructures import URL
    return {
        "code": 200,
        "filename": filename,
        "hash": file_hash,
        "downloadUrl": f"{base_url}{filename}",
        "node": config.node_uuid,
        "msg": "success"
    }

@app.get("/favicon.ico")
async def favicon():
    favicon_path = Path("favicon.ico")
    if favicon_path.is_file():
        return FileResponse(favicon_path)
    else:
        raise HTTPException(status_code=404, detail="Favicon not found")

@app.get("/files/{file_path:path}")
async def download_file(file_path: str):
    full_path = os.path.abspath(os.path.join(config.workdir, file_path))
    if not full_path.startswith(os.path.abspath(config.workdir)) or not os.path.isfile(full_path):
        raise HTTPException(status_code=404, detail="文件不存在")
    return FileResponse(full_path, filename=os.path.basename(full_path))

@app.get("/", response_class=HTMLResponse)
async def index():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>HayFrp File Node</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
            h1 { color: #333; }
            ul { list-style: none; padding: 0; }
            li { margin: 2px 0; padding-left: 20px; }
            .folder { color: #666; }
            a { color: #0066cc; text-decoration: none; display: block; }
            a:hover { background-color: #f5f5f5; }
        </style>
    </head>
    <body>
        <h1>HayFrp 文件列表</h1>
        <ul id="fileList"></ul>
        <script>
            function createTree(files) {
                const tree = {}
                files.forEach(path => {
                    path.split('/').reduce((acc, cur) => {
                        acc.children = acc.children || {}
                        if (!acc.children[cur]) {
                            acc.children[cur] = { name: cur, isDir: !path.endsWith(cur) }
                        }
                        return acc.children[cur]
                    }, { children: tree })
                })

                function buildHTML(node, path = '') {
                    return Object.values(node.children || {}).map(child => {
                        const fullPath = path ? `${path}/${child.name}` : child.name
                        return `<li>
                            ${child.isDir 
                                ? `<span class="folder">📁 ${child.name}</span>` 
                                : `<a href="/files/${fullPath}" target="_blank">📄 ${child.name}</a>`}
                            ${child.children ? `<ul>${buildHTML(child, fullPath)}</ul>` : ''}
                        </li>`
                    }).join('')
                }

                return buildHTML({ children: tree })
            }

            async function loadFiles(path = '') {
                const response = await fetch(`/api/list?path=${encodeURIComponent(path)}`)
                const { files } = await response.json()
                document.getElementById('fileList').innerHTML = createTree(files)
            }
            loadFiles()
        </script>
    </body>
    </html>
    '''

@app.get("/docs", response_class=HTMLResponse)
async def api_docs():
    return """
    # 文件下载API使用指南
    ## API端点
    ### 1. 获取文件列表
    - 路径: `/api/list`
    - 方法: GET
    
    ### 2. 获取文件信息
    - 路径: `/api/info/{filename}`
    - 方法: GET
    
    ### 3. 文件下载
    - 路径: `/files/{filename}`
    - 方法: GET
    """

@app.post("/api/sync")
async def run_sync(background_tasks: BackgroundTasks):
    global last_sync_time
    
    current_time = time.time()
    if current_time - last_sync_time < config.SYNC_COOLDOWN:
        raise HTTPException(status_code=429, detail="操作过于频繁，请5分钟后再试")
    
    async def sync_task():
        try:
            result = subprocess.run(
                ['python', 'sync.py'],
                capture_output=True,
                text=True,
                check=True
            )
            return result
        except subprocess.CalledProcessError as e:
            return e
    
    background_tasks.add_task(sync_task)
    last_sync_time = current_time
    return {
        "code": 200,
        "msg": "同步任务已启动",
        "node": config.node_uuid
    }

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.status_code, "error": exc.detail}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=config.port)