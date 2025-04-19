# 文件下载服务

一个简单的文件上传下载服务，基于Flask框架实现。

## 功能特性
- 文件上传
- 文件下载
- 文件列表查看
- 文件哈希校验

## 快速开始

### 安装依赖
```bash
pip install flask werkzeug



## API文档
### 1. 获取文件列表
- 路径 : /api/files
- 方法 : GET
- 示例响应 :
```json
{
    "files": ["file1.txt", "file2.pdf"]
}
 ```

### 2. 获取文件信息
- 路径 : /api/fileinfo/<filename>
- 方法 : GET
- 示例响应 :
```json
{
    "filename": "file1.txt",
    "hash": "sha256哈希值",
    "downloadUrl": "http://host/download/file1.txt"
}
 ```
```

### 3. 文件上传
- 路径 : /api/upload
- 方法 : POST
- 请求格式 : multipart/form-data
- 示例请求 :
```bash
curl -X POST -F "file=@test.txt" http://localhost:5000/api/upload
 ```
```

### 4. 文件下载
- 路径 : /download/<filename>
- 方法 : GET
## 项目结构
```plaintext
.
├── app.py          # 主程序
├── README.md       # 项目文档
└── dw/             # 上传文件存储目录
 ```