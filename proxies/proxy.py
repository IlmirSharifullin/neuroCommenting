import python_socks


class Proxy:
    with open('proxies/proxies.txt') as f:
        proxy_file = f.read().split('\n')

    def __init__(self, index):
        self.proxy_str = self.proxy_file[index]
        user_pass, address_port_region = self.proxy_str.split('@')
        self.username, self.password = user_pass.split(':')
        self.address, self.port = address_port_region.split(':')
        self.dict = {
            'proxy_type': python_socks.ProxyType.HTTP,
            'addr': self.address,
            'port': self.port,
            'username': self.username,
            'password': self.password
        }


