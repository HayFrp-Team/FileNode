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
async def list_files():
    return {
        "code": 200,
        "files": sorted([
            f for f in os.listdir(config.workdir) 
            if os.path.isfile(os.path.join(config.workdir, f))
        ]),
        "node": config.node_uuid,
        "msg": "success"
    }

@app.get("/api/info/{filename}")
async def get_file_info(request: Request, filename: str):
    filepath = os.path.join(config.workdir, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="文件不存在")
    
    file_hash = calculate_hash(filepath)
    base_url = str(request.base_url)
    return {
        "code": 200,
        "filename": filename,
        "hash": file_hash,
        "downloadUrl": f"{base_url}{filename}",
        "node": config.node_uuid,
        "msg": "success"
    }

@app.get("/{filename}")
async def download_file(filename: str):
    filepath = os.path.join(config.workdir, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="文件不存在")
    return FileResponse(filepath, filename=filename)

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
            li { margin: 10px 0; }
            a { color: #0066cc; text-decoration: none; }
            a:hover { text-decoration: underline; }
        </style>
    </head>
    <body>
        <h1>HayFrp 文件列表</h1>
        <ul id="fileList"></ul>
        <script>
            async function loadFiles() {
                const response = await fetch('/api/list');
                const { files } = await response.json();
                const list = document.getElementById('fileList');
                
                files.forEach(async file => {
                    const li = document.createElement('li');
                    const a = document.createElement('a');
                    
                    const infoResponse = await fetch(`/api/info/${file}`);
                    const fileInfo = await infoResponse.json();
                    
                    a.href = fileInfo.downloadUrl;
                    a.textContent = file;
                    
                    li.appendChild(a);
                    list.appendChild(li);
                });
            }
            loadFiles();
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
    - 路径: `/{filename}`
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