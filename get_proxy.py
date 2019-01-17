# - coding: utf-8 -

import traceback
import socket
import socks
import requests

proxy_count = 1000
proxies = requests.get("https://proxy.ishield.cn/?types=0&count={}".format(proxy_count)).json()

with open("proxy.txt", "w") as f:
    for proxy in proxies:
        try:
            HOST = '128.14.230.246'
            PORT = 30000
            host, port, _ = proxy
            socks.set_default_proxy(socks.HTTP, host, port)
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((HOST, PORT))
                s.close()
            r = requests.head("http://sgz-login.fingerfunol.com:30006", timeout=2)
            if r.status_code in [200, 404]:
                f.write("{} {}".format(host, port))
                f.write("\n")
        except:
            print(traceback.format_exc())
            print("proxy not supported")
            continue
