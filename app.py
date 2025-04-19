from flask import Flask, request, send_from_directory, jsonify, render_template_string
import os
from werkzeug.utils import secure_filename
import hashlib
from config import config

app = Flask(__name__)

# 确保上传目录存在
os.makedirs(config.workdir, exist_ok=True)

# 计算文件哈希值
def calculate_hash(fpath: str) -> str:
    with open(fpath, 'rb') as f:
        return hashlib.new('sha256', f.read()).hexdigest()

# 列出文件列表
@app.route('/api/list', methods=['GET'])
def list_files():
    return jsonify({
        'files': sorted(
            [f for f in os.listdir(config.workdir) 
             if os.path.isfile(os.path.join(config.workdir, f))]
        )
    })

# 文件信息
@app.route('/api/info/<filename>', methods=['GET'])
def get_file_info(filename):
    filepath = os.path.join(config.workdir, filename)
    if not os.path.exists(filepath):
        return jsonify({'error': '文件不存在'}), 404
    
    file_hash = calculate_hash(filepath)
    return jsonify({
        'filename': filename,
        'hash': file_hash,
        'downloadUrl': f"{request.host_url}file/{filename}"
    })

# 文件直链
@app.route('/file/<filename>')
def download(filename):
    filepath = os.path.join(config.workdir, filename)
    if not os.path.exists(filepath):
        return jsonify({'error': '文件不存在'}), 404
    return send_from_directory(config.workdir, filename, as_attachment=True)

@app.route('/')
def index():
    files = os.listdir(config.workdir)
    return render_template_string('''
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
                        
                        // 获取文件信息
                        const infoResponse = await fetch(`/api/info/${file}`);
                        const fileInfo = await infoResponse.json();
                        
                        //a.href = fileInfo.downloadUrl;
                        a.href = `/api/info/${file}`;
                        a.textContent = file;
                        /*
                        a.onclick = (e) => {
                            e.preventDefault();
                            alert(JSON.stringify(fileInfo, null, 2));
                            return false;
                        };
                        */                        
                        li.appendChild(a);
                        list.appendChild(li);
                    });
                }
                loadFiles();
            </script>
        </body>
        </html>
    ''')

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': '请求的页面不存在'}), 404

@app.route('/docs')
def api_docs():
    return """# 文件下载API使用指南

## API端点

### 1. 获取文件列表
- 路径: `/api/list`
- 方法: GET
- 返回格式:
```json
{
    "files": ["file1.txt", "file2.pdf"]
}
```

### 2. 获取文件信息
- 路径: `/api/info/<filename>`
- 方法: GET
- 返回格式:
```json
{
    "filename": "file1.txt",
    "hash": "sha256哈希值",
    "downloadUrl": "http://host:port/file/file1.txt"
}
```

### 3. 文件下载
- 路径: `/file/<filename>`
- 方法: GET
- 返回: 文件内容
""", 200, {'Content-Type': 'text/markdown'}

if __name__ == '__main__':
    app.run(port=config.port)