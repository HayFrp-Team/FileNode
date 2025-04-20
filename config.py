import os

class Config:
    # 工作目录，存放上传的文件
    workdir = os.path.join(os.path.dirname(__file__), 'dw')
    
    # 服务监听端口
    port = 5000

config = Config()