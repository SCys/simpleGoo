#!/usr/bin/python3

import re
from tornado import web,gen
from tornado.log import access_log as logger
from tornado.options import define, options, parse_command_line
from tornado.httpclient import AsyncHTTPClient, HTTPRequest, HTTPError
import tornado.ioloop

define('host', 'localhost', str, 'proxy listen hostname')
define('port', 61001, int, 'proxy listen port number')
define('domain', 'example.com', str, 'proxy replace google\'s domains to this domain')
define('domain_google', 'www.google.com', str, 'google main doman')

rules = (
    re.compile(r'https?://(\w+.(google|gstatic|googleapis|ggpht).com)'),
)

class DefaultHanlder(web.RequestHandler):

    def prepare(self):
        # copy client ip from proxy header
        client_host = self.request.headers.get('X-Forward-For', '127.0.0.1')

        # add query string to url
        path = 'https://%s/%s' % (options.domain_google, self.request.path[1:])
        if self.request.query:
            path += '?%s' % self.request.query

        request = HTTPRequest(
            url=path,
            connect_timeout=5.0,
            request_timeout=10.0,
        )

        # setup cookie
        #request.headers.add('Set-Cookie', self.request.headers.get('Cookie', ''))
        for name in ('Accept-Language', 'Accept', 'X-Forward-For', 'User-Agent'):
            for item in self.request.headers.get_list(name):
                request.headers.add(name, item)

        request.headers['Connection'] = 'keep-alive'
        request.headers['Referer'] = options.domain

        self.client_request = request

    @gen.coroutine
    def get(self, path):
        client = AsyncHTTPClient()

        logger.info('fetching: %s', self.client_request.url)

        try:
            response = yield client.fetch(self.client_request)
        except HTTPError as e:
            self.set_status(e.code, e.response.reason)
            self.write(e.response.buffer.read())
            return

        # addition timeinfo
        for name,value in response.time_info.items():
            self.set_header('TIMEINFO-%s' % name, value)

        # response headers
        #for name,value in response.headers.items():
        #    self.set_header(name,value)

        for name in (
            'Content-Type',
            'X-Consumed-Content-Encoding',
            'X-Content-Type-Options',
            'Vary',
            'Alternate-Protocol',
            'Cache-Control',
            'Date',
            'Expires',
            'Last-Modified',
            'X-Xss-Protection',
            'Age',
            'Server'):
            self.set_header(name, response.headers.get(name, ''))

        # debug
        #print(response.headers.keys())

        #self.set_header('Set-Cookie', response.headers['Cookie'])
        self.set_status(response.code, response.reason)

        buf = response.buffer.read()
        try:
            buf = buf.decode()
            domain = r'https://%s/!\g<1>!' % options.domain
            for rule in rules:
                if not rule.search(buf) is None:
                    buf = rule.sub(domain, buf)
        except UnicodeDecodeError:
            pass

        self.write(buf)


class HostedHandler(DefaultHanlder):

    @gen.coroutine
    def get(self, host, path):
        req = self.client_request

        if host.endswith('.cn'):
            req.url = 'http://%s/%s' % (host, path)
        else:
            req.url = 'https://%s/%s' % (host, path)
        if self.request.query:
            req.url += '?%s' % self.request.query

        yield super().get(path)


def main():
    parse_command_line()
    app = web.Application([
        (r'/!([a-zA-Z-\.]+)!/(.*)', HostedHandler),
        (r'/(.*)', DefaultHanlder),
    ])
    app.listen(options.port, options.host)
    logger.info('simpleGoo listen on %s:%s', options.host, options.port)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == '__main__':
    main()
