import os

class Config:
    @property
    def workdir(self) -> str:
        """文件存储目录，默认./file"""
        return os.getenv('WORKDIR', 'file')
    
    @property
    def port(self) -> int:
        """服务端口，默认5000"""
        return int(os.getenv('PORT', '5000'))
    
    @property
    def SYNC_COOLDOWN(self) -> int:
        """同步接口请求限制"""
        return int(os.getenv('SYNC_COOLDOWN', '300'))

    @property
    def max_retry(self) -> int:
        """下载失败重试次数，默认3"""
        return int(os.getenv('MAX_RETRY', '3'))

    @property
    def node_uuid(self) -> str:
        """节点UUID"""
        return os.getenv('NODE_UUID', 'non-official')

    @property
    def api_url(self) -> str:
        """API服务地址"""
        return os.getenv('APIURL', 'https://apiv3.hayfrp.com')

config = Config()