from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.plugins.action import ActionBase
from ansible.utils.display import Display
from http.server import BaseHTTPRequestHandler, HTTPServer
import os

import time

nodes = dict()
display = Display()

class IPMI:
    # BOOT_DISK_CMD = "ipmitool -I lanplus -U admin -P password -H 127.0.0.1 -p 6230 chassis bootdev disk"
    def __init__(self, node, ipmi_user, ipmi_password, ipmi_address, ipmi_port=623, ipmi_uefi=False):
        self.node = node
        self.user = ipmi_user
        self.password = ipmi_password
        self.host = ipmi_address
        self.port = ipmi_port
        self.uefi = ipmi_uefi

    def __str__(self):
        return f"-U {self.user} -P {self.password} -H {self.host} -p {self.port}"

    def set_boot_disk(self):
        cmd = f"ipmitool -I lanplus -U {self.user} -P {self.password} -H {self.host} -p {self.port} chassis bootdev disk"
        if self.uefi:
            cmd = f"{cmd} options=efiboot"
        return os.system(cmd)

class MyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        dummy, node, action = self.path.split('/')
        results = None
        if action == 'post' and node in nodes.keys():
            results = nodes[node].set_boot_disk()
            del nodes[node]
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(bytes("<html><head><title>Boot Control</title></head>", "utf-8"))
        self.wfile.write(bytes("<p>Request: %s</p>" % self.path, "utf-8"))
        self.wfile.write(bytes("<body>", "utf-8"))
        self.wfile.write(bytes("<p>chassis bootdev disk: %s</p>" % results, "utf-8"))
        self.wfile.write(bytes("</body></html>", "utf-8"))
        display.display("Set Boot Disk for: %s, result: %s" % (node, results))

class ActionModule(ActionBase):

    def run(self, tmp=None, task_vars=None):
        if task_vars is None:
            task_vars = dcit()

        result = super(ActionModule, self).run(tmp, task_vars)
        del tmp

        hostName = self._task.args.get('hostname', None)
        serverPort = self._task.args.get('serverport', 8000)
        timeout = self._task.args.get('timeut',600)
        for node in self._task.args.get('nodes', []):
            nodes[node['node']] = IPMI(**node)

        module_return = dict(changed=True)

        webServer = HTTPServer((hostName, serverPort), MyServer)
        webServer.timeout = 60

        expire_time = time.time() + timeout
        while len(nodes) > 0 and time.time() < expire_time:
            webServer.handle_request()
            module_return = dict(changed=True)
            display.display("Nodes left to bootstrap: %s" % len(nodes))

        return module_return
