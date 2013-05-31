#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import py
import re
import pytest
import ConfigParser

import requests

import credentials
from . import plugin_safety


__version__ = '1.1'





def pytest_sessionstart(session):
    option = session.config.option

    # configure session proxies
    if hasattr(session.config, 'browsermob_session_proxy'):
        option.proxy_host = option.bmp_host
        option.proxy_port = session.config.browsermob_session_proxy.port

    zap = getattr(session.config, 'zap', None)
    if zap is not None:
        if option.proxy_host and option.proxy_port:
            zap.core.set_option_proxy_chain_name(option.proxy_host)
            zap.core.set_option_proxy_chain_port(option.proxy_port)
        option.proxy_host = option.zap_host
        option.proxy_port = option.zap_port


@pytest.fixture(scope='session')
def selenium_base_url(request):
    url = (request.config.option.base_url or
           request.config.getini('selenium_base_url'))
    if not url:
        raise pytest.UsageError('--baseurl must be specified.')
    return url


@pytest.fixture(scope='session', autouse=True)
def _verify_base_url(request):
    option = request.config.option
    if option.base_url and not option.skip_url_check:
        r = requests.get(option.base_url, verify=False)
        if r.status_code not in (200, 401):
            raise pytest.UsageError(
                'Base URL did not return status code 200 or 401. '
                '(URL: %s, Response: %s)' % (option.base_url, r.status_code))


def pytest_runtest_setup(item):
    option = item.config.option
    item.debug = {
        'urls': [],
        'screenshots': [],
        'html': [],
        'logs': [],
        'network_traffic': []}
    TestSetup.base_url = option.base_url

    # configure test proxies
    if hasattr(item.config, 'browsermob_test_proxy'):
        option.proxy_host = item.config.option.bmp_host
        option.proxy_port = item.config.browsermob_test_proxy.port

    if option.sauce_labs_credentials_file:
        item.sauce_labs_credentials = credentials.read(option.sauce_labs_credentials_file)
    else:
        item.sauce_labs_credentials = None


    if option.credentials_file:
        TestSetup.credentials = credentials.read(option.credentials_file)


#FIXME: needs autouse till test setup/teardown is cleaned up
@pytest.fixture
def selenium_client(request, _sensitive_skiping):
    item = request.node
    test_id = '.'.join(split_class_and_test_names(item.nodeid))
    if item.sauce_labs_credentials is not None:
        from sauce_labs import Client
        TestSetup.selenium_client = Client(
            test_id,
            item.config.option,
            item.keywords,
            item.sauce_labs_credentials)
    else:
        from selenium_client import Client
        TestSetup.selenium_client = Client(
            test_id,
            item.config.option)
    item._webdriver = TestSetup.selenium_client.start()
    TestSetup.selenium = TestSetup.selenium_client.selenium
    TestSetup.timeout = TestSetup.selenium_client.timeout
    TestSetup.default_implicit_wait = TestSetup.selenium_client.default_implicit_wait
    request.addfinalizer(TestSetup.selenium_client.stop)
    #XXX: return value?


def pytest_runtest_makereport(__multicall__, item, call):
    report = __multicall__.execute()
    if report.when == 'call':
        webdriver = getattr(item, '_webdriver', None)
        if webdriver is not None:
            report.session_id = webdriver.session_id
            if (
                    report.skipped and 'xfail' in report.keywords or
                    report.failed and 'xfail' not in report.keywords):
                url = webdriver.current_url
                item.debug['urls'].append(url)
                screenshot = webdriver.get_screenshot_as_base64()
                item.debug['screenshots'].append(screenshot)
                html = webdriver.page_source
                item.debug['html'].append(html)
                report.sections.append(('pytest-mozwebqa', _debug_summary(item.debug)))
            report.debug = item.debug
            if hasattr(item, 'sauce_labs_credentials') and report.session_id:
                result = {'passed': report.passed or (report.failed and 'xfail' in report.keywords)}
                import sauce_labs
                sauce_labs.Job(report.session_id).send_result(
                    result,
                    item.sauce_labs_credentials)
    return report


@pytest.fixture
def mozwebqa(request, selenium_client):
    return TestSetup(request)


def pytest_addoption(parser):

    parser.addini('selenium_base_url', 'base url for the selenium web tests')

    group = parser.getgroup('selenium', 'selenium')
    group._addoption('--baseurl',
                     action='store',
                     dest='base_url',
                     default=None,
                     metavar='url',
                     help='base url for the application under test.')
    group._addoption('--skipurlcheck',
                     action='store_true',
                     dest='skip_url_check',
                     default=False,
                     help='skip the base url and sensitivity checks. (default: %default)')
    group._addoption('--host',
                     action='store',
                     default='localhost',
                     metavar='str',
                     help='host that selenium server is listening on. (default: %default)')
    group._addoption('--port',
                     action='store',
                     type='int',
                     default=4444,
                     metavar='num',
                     help='port that selenium server is listening on. (default: %default)')
    group._addoption('--driver',
                     action='store',
                     dest='driver',
                     default='Remote',
                     metavar='str',
                     help='webdriver implementation. (default: %default)')
    group._addoption('--capabilities',
                     action='store',
                     dest='capabilities',
                     metavar='str',
                     help='json string of additional capabilties to set (webdriver).')
    group._addoption('--chromepath',
                     action='store',
                     dest='chrome_path',
                     metavar='path',
                     help='path to the google chrome driver executable.')
    group._addoption('--firefoxpath',
                     action='store',
                     dest='firefox_path',
                     metavar='path',
                     help='path to the target firefox binary.')
    group._addoption('--firefoxpref',
                     action='store',
                     dest='firefox_preferences',
                     metavar='str',
                     help='json string of firefox preferences to set (webdriver).')
    group._addoption('--profilepath',
                     action='store',
                     dest='profile_path',
                     metavar='str',
                     help='path to the firefox profile to use (webdriver).')
    group._addoption('--extension',
                     action='append',
                     dest='extension_paths',
                     metavar='str',
                     help='path to browser extension to install (webdriver).')
    group._addoption('--chromeopts',
                     action='store',
                     dest='chrome_options',
                     metavar='str',
                     help='json string of google chrome options to set (webdriver).')
    group._addoption('--operapath',
                     action='store',
                     dest='opera_path',
                     metavar='path',
                     help='path to the opera driver.')
    group._addoption('--browsername',
                     action='store',
                     dest='browser_name',
                     metavar='str',
                     help='target browser name (webdriver).')
    group._addoption('--browserver',
                     action='store',
                     dest='browser_version',
                     metavar='str',
                     help='target browser version (webdriver).')
    group._addoption('--platform',
                     action='store',
                     metavar='str',
                     help='target platform (webdriver).')
    group._addoption('--webqatimeout',
                     action='store',
                     type='int',
                     default=60,
                     metavar='num',
                     help='timeout (in seconds) for page loads, etc. (default: %default)')
    group._addoption('--build',
                     action='store',
                     dest='build',
                     metavar='str',
                     help='build identifier (for continuous integration).')
    group._addoption('--untrusted',
                     action='store_true',
                     dest='assume_untrusted',
                     default=False,
                     help='assume that all certificate issuers are untrusted. (default: %default)')
    group._addoption('--proxyhost',
                     action='store',
                     dest='proxy_host',
                     metavar='str',
                     help='use a proxy running on this host.')
    group._addoption('--proxyport',
                     action='store',
                     dest='proxy_port',
                     metavar='int',
                     help='use a proxy running on this port.')

    group = parser.getgroup('credentials', 'credentials')
    group._addoption("--credentials",
                     action="store",
                     dest='credentials_file',
                     metavar='path',
                     help="location of yaml file containing user credentials.")
    group._addoption('--saucelabs',
                     action='store',
                     dest='sauce_labs_credentials_file',
                     metavar='path',
                     help='credendials file containing sauce labs username and api key.')



def split_class_and_test_names(nodeid):
    names = nodeid.split("::")
    names[0] = names[0].replace("/", '.')
    names = [x.replace(".py", "") for x in names if x != "()"]
    classnames = names[:-1]
    classname = ".".join(classnames)
    name = names[-1]
    return (classname, name)


def _debug_summary(debug):
    summary = []
    if debug['urls']:
        summary.append('Failing URL: %s' % debug['urls'][-1])
    return '\n'.join(summary)


class TestSetup:
    '''
        This class is just used for monkey patching
    '''
    def __init__(self, request):
        self.request = request
