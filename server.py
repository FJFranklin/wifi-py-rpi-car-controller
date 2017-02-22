import os
import web

global_server_instance = 0

def global_server ():
    global global_server_instance
    if global_server_instance == 0:
        global_server_instance = server (globals ())
    return global_server_instance

class server (object):
    def __init__ (self, global_vars):
        urls = (
            '/', 'server_index',
            '/query', 'server_query',
            '/command', 'server_command'
        )
        self.app = web.application (urls, global_vars)
        self.app.internalerror = web.debugerror
        self.handler = None
        return

    def set_handler (self, handler):
        self.handler = handler
        return

    def run (self):
        self.app.run ()
        return

    def index (self):
        return open('static/index.html', 'r').read ()

    def query (self, name, value):
        if self.handler is None:
            response = ''
        else:
            response = self.handler.query (name, value)
        return response

    def command (self, name, value):
        if self.handler is None:
            response = ''
        else:
            response = self.handler.command (name, value)

        if name == 'stop':
            self.app.stop ()

        return response

class server_index:
    def GET (self):
        return global_server().index ()

class server_query:
    def GET (self):
        args = web.input (name='', value='')
        if (args.name != ''):
            return global_server().query (args.name, args.value)

class server_command:
    def GET (self):
        args = web.input (name='', value='')
        if (args.name != ''):
            return global_server().command (args.name, args.value)

if __name__ == "__main__":
    global_server().run ()
