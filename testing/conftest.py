#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest
import requests
from webserver import SimpleWebServer

pytest_plugins = 'pytester'


def pytest_configure(config):
    host = config.option.host
    port = config.option.port
    try:
        res = requests.get('http://%s:%s' % (host, port))
    except:
        raise pytest.UsageError('need a running selenium-standalone')

@pytest.fixture
def webserver_baseurl(webserver):
    return '--baseurl=http://localhost:%s' % webserver.port

#XXX: fix name after pytest plugin ordering is fixed
@pytest.fixture(autouse=True)
def _testdir(request, webserver_baseurl, monkeypatch):
    item = request.node
    if 'testdir' not in item.funcargnames:
        return

    testdir = request.getfuncargvalue('testdir')

    
    testdir.makepyfile(conftest="""
        import pytest
        @pytest.fixture
        def webtext(mozwebqa):
            mozwebqa.selenium.get(mozwebqa.base_url)
            s = mozwebqa.selenium
            return s.find_element_by_tag_name('h1').text
        """)

    def inline_runqa(*k, **kw):
        return testdir.inline_run(
            webserver_baseurl,
            '--driver=firefox',
            '--webqareport=result.html',
            *k, **kw)
    testdir.inline_runqa = inline_runqa
    def quick_qa(*k, **kw):
        reprec = inline_runqa(*k)
        outcomes = reprec.listoutcomes()
        names = ('passed', 'skipped', 'failed')
        for name, val in zip(names, outcomes):
            wantlen = kw.get(name)
            if wantlen is not None:
                assert len(val) == wantlen, name

    testdir.quick_qa = quick_qa
    return testdir

@pytest.fixture(scope='session', autouse=True)
def webserver(request):
    webserver = SimpleWebServer()
    webserver.start()
    request.addfinalizer(webserver.stop)
    return webserver


