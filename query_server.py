# -*- coding: utf-8 -*-

import os
import sys
reload(sys)
sys.setdefaultencoding("utf-8")
import tornado.ioloop
import tornado.web

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        name = self.get_argument("card")
        if name == "all":
            cmd = 'echo "select cards from pigs_20 where length(email)>17 and level>=30;" | sqlite3 data.db | tr "," "\n" | grep -v 小乔 | egrep -v "^张辽" | egrep -v "^$" | sort | uniq -c | sort -k1n'
        else:
            cmd = 'echo "select email, level, last_login, cards from pigs_20 where level>=30 and cards like \'%%{}%%\';" | sqlite3 data.db | grep -v alita'.format(name)
        self.write("<pre>" + os.popen(cmd).read() + "</pre>")

def make_app():
    return tornado.web.Application([
        (r"/", MainHandler),
    ])

if __name__ == "__main__":
    app = make_app()
    app.listen(8081)
    tornado.ioloop.IOLoop.current().start()
