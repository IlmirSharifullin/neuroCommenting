import python_socks


class Proxy:
    with open('proxies/proxies.txt') as f:
        proxy_file = f.read().split('\n')
        proxy_count = len(proxy_file)

    def __init__(self, index):
        # pattern - {login}:{password}@{ip}:{port}
        self.proxy_line = self.proxy_file[index]
        user_pass, address_port_region = self.proxy_line.split('@')
        self.username, self.password = user_pass.split(':')
        self.address, self.port = address_port_region.split(':')
        self.dict = {
            'proxy_type': python_socks.ProxyType.HTTP,
            'addr': self.address,
            'port': self.port,
            'username': self.username,
            'password': self.password
        }
