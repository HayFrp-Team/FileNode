from flask import Flask, request, send_from_directory, jsonify, render_template_string
import os
from werkzeug.utils import secure_filename
import hashlib

app = Flask(__name__)

# 配置
UPLOAD_FOLDER = 'dw'

app.config.update({
    'UPLOAD_FOLDER': UPLOAD_FOLDER
})

# 确保上传目录存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)



def calculate_hash(filepath):
    sha256 = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            sha256.update(chunk)
    return sha256.hexdigest()

@app.route('/api/files', methods=['GET'])
def list_files():
    return jsonify({
        'files': os.listdir(app.config['UPLOAD_FOLDER'])
    })

@app.route('/api/fileinfo/<filename>', methods=['GET'])
def get_file_info(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(filepath):
        return jsonify({'error': '文件不存在'}), 404
    
    file_hash = calculate_hash(filepath)
    return jsonify({
        'filename': filename,
        'hash': file_hash,
        'downloadUrl': f"{request.host_url}download/{filename}"
    })

@app.route('/api/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({'error': '没有文件部分'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400
    

    
    filename = secure_filename(file.filename)
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    
    return jsonify({
        'message': '文件上传成功',
        'filename': filename,
        'url': f"{request.host_url}download/{filename}"
    })

@app.route('/download/<filename>')
def download(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(filepath):
        return jsonify({'error': '文件不存在'}), 404
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

@app.route('/')
def index():
    files = os.listdir(app.config['UPLOAD_FOLDER'])
    return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <title>文件列表</title>
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
            <h1>文件列表</h1>
            <ul id="fileList"></ul>
            <script>
                async function loadFiles() {
                    const response = await fetch('/api/files');
                    const { files } = await response.json();
                    
                    const list = document.getElementById('fileList');
                    files.forEach(async file => {
                        const li = document.createElement('li');
                        const a = document.createElement('a');
                        
                        // 获取文件信息
                        const infoResponse = await fetch(`/api/fileinfo/${file}`);
                        const fileInfo = await infoResponse.json();
                        
                        a.href = fileInfo.downloadUrl;
                        a.textContent = file;
                        a.onclick = (e) => {
                            e.preventDefault();
                            alert(JSON.stringify(fileInfo, null, 2));
                            return false;
                        };
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
- 路径: `/api/files`
- 方法: GET
- 返回格式:
```json
{
    "files": ["file1.txt", "file2.pdf"]
}
```

### 2. 获取文件信息
- 路径: `/api/fileinfo/<filename>`
- 方法: GET
- 返回格式:
```json
{
    "filename": "file1.txt",
    "hash": "sha256哈希值",
    "downloadUrl": "http://host/download/file1.txt"
}
```

### 3. 文件上传
- 路径: `/api/upload`
- 方法: POST
- 请求格式: multipart/form-data
- 返回格式:
```json
{
    "message": "文件上传成功",
    "filename": "file1.txt",
    "url": "http://host/download/file1.txt"
}
```

### 4. 文件下载
- 路径: `/download/<filename>`
- 方法: GET
- 返回: 文件内容
""", 200, {'Content-Type': 'text/markdown'}

if __name__ == '__main__':
    app.run(debug=True, port=5000)