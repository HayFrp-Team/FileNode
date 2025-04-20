# HayFrp File Node

## Employ

- 推荐使用 Docker 部署
- 直接使用 Python 请注意env、systemd、crontab的配置

> 如果无法连接到 Docker Hub 以及 GHCR， 可自行构建镜像或在Action中下载构件（使用docker load -i hayfrp_file_node.tar导入）。
> 
> Docker端口映射必须保证通信端口与配置一致。运行命令和配置参数从团队空间获取。

## API

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