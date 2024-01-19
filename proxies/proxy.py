import traceback
import python_socks
from config import logger


class Proxy:
    def __init__(self, obj: str):
        self.proxy_line = obj

        user_pass, address_port = self.proxy_line.split('@')
        self.username, self.password = user_pass.split(':')
        self.address, self.port = address_port.split(':')
        self.dict = {
            'proxy_type': python_socks.ProxyType.SOCKS5,
            'addr': self.address,
            'port': self.port,
            'username': self.username,
            'password': self.password
        }

    @classmethod
    def validate_proxy_format(cls, proxy_string):
        try:
            user_pass, address_port = proxy_string.split('@')
            username, password = user_pass.split(':')
            address, port = address_port.split(':')
            if port.isdigit():
                return True
        except Exception:
            logger.error(traceback.format_exc())
            return False
        return False
