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


@pytest.fixture(scope='session', autouse=True)
def webserver(request):
    webserver = SimpleWebServer()
    webserver.start()
    request.addfinalizer(webserver.stop)
    return webserver


