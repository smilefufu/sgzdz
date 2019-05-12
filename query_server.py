# -*- coding: utf-8 -*-

import os
import sys
#reload(sys)
#sys.setdefaultencoding("utf-8")
import tornado.ioloop
import tornado.web
from tornado.options import parse_command_line

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        name = self.get_argument("card")
        server = self.get_argument("server", "20")
        if name == "all":
            cmd = 'echo "select cards from pigs_' + server + ' where level>=30;" | sqlite3 data.db | tr "," "\n" | grep -v alita | egrep -v "^$" | sort | uniq -c | sort -k1n'
        else:
            cmd = 'echo "select email, level, last_login, cards from pigs_' + server + ' where level>=30 and cards like \'%%{}%%\';" | sqlite3 data.db | grep -v alita'.format(name)
        self.write("<pre>" + os.popen(cmd).read() + "</pre>")


class MyHandler(tornado.web.RequestHandler):
    def get(self):
        name = self.get_argument("card")
        if name == "all":
            cmd = 'echo "select cards from pigs_20 where level>=30;" | sqlite3 data.db | tr "," "\n" | grep -v 小乔 | egrep -v "^张辽" | egrep -v "^$" | sort | uniq -c | sort -k1n'
        else:
            cmd = 'echo "select email, level, last_login, cards from pigs_20 where level>=30 and cards like \'%%{}%%\';" | sqlite3 data.db'.format(name)
        self.write("<pre>" + os.popen(cmd).read() + "</pre>")

def make_app():
    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/a", MyHandler),
    ])

if __name__ == "__main__":
    parse_command_line()
    app = make_app()
    app.listen(8081)
    tornado.ioloop.IOLoop.current().start()
