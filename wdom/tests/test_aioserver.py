#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import asyncio

import aiohttp

from wdom.log import configure_logger
from wdom.tests.util import TestCase, sync
from wdom.document import Document
from wdom.aioserver import get_app, start_server, stop_server


def setup_module():
    configure_logger(logging.DEBUG)


class TestServer(TestCase):
    def setUp(self):
        with self.assertLogs('wdom.aioserver', 'INFO'):
            self.server = start_server(self.get_app(), port=0)
        self.port = self.server.sockets[-1].getsockname()[1]
        self.addr = 'http://localhost:{}'.format(self.port)

    def get_app(self):
        self.doc = Document()
        self.app = get_app(self.doc)
        return self.app

    def tearDown(self):
        with self.assertLogs('wdom.aioserver', 'INFO'):
            stop_server(self.server)

    async def fetch(self, url:str):
        if not url.startswith('/'):
            url = '/' + url
        loop = asyncio.get_event_loop()
        with aiohttp.ClientSession(loop=loop) as session:
            with self.assertLogs('wdom.aioserver', 'INFO'):
                async with session.get(self.addr + url) as response:
                    assert response.status == 200
                    content = await response.read()
        return content.decode('utf-8')

    @sync
    async def test_mainpage(self):
        content = await self.fetch('/')
        self.assertMatch(
            r'<!DOCTYPE html><html id="\d+">\s*<head id="\d+">\s*'
            r'.*<meta .*<title id="\d+">\s*W-DOM\s*</title>.*'
            r'</head>\s*<body.*>.*<script.*>.*</script>.*'
            r'</body>\s*</html>'
            r'', content
        )