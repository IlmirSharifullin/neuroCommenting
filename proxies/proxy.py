import re

import python_socks


class Proxy:
    with open('proxies/proxies.txt') as f:
        proxy_file = f.read().split('\n')
        proxy_count = len(proxy_file)

    def __init__(self, obj):
        if isinstance(obj, int):
            index = obj
            # pattern - {login}:{password}@{ip}:{port}
            self.proxy_line = self.proxy_file[index]
        elif isinstance(obj, str):
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
            if port.is_digit():
                return True
        except Exception:
            return False
        return False
