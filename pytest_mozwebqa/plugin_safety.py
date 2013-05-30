import pytest
import requests
import re


def pytest_addoption(parser):
    group = parser.getgroup('safety', 'safety')
    group._addoption('--sensitiveurl',
                     action='store',
                     dest='sensitive_url',
                     default='mozilla\.(com|org)',
                     metavar='str',
                     help='regular expression for identifying sensitive urls.'
                          ' (default: %default)')
    group._addoption('--destructive',
                     action='store_true',
                     dest='run_destructive',
                     default=False,
                     help='include destructive tests (tests not explicitly marked as \'nondestructive\'). (default: %default)')



def pytest_configure(config):
    if hasattr(config, 'slaveinput'):
        return # xdist slave
    config.addinivalue_line(
        'markers', 'nondestructive: mark the test as nondestructive. ' \
        'Tests are assumed to be destructive unless this marker is ' \
        'present. This reduces the risk of running destructive tests ' \
        'accidentally.')
    if not config.option.run_destructive:
        if config.option.markexpr:
            config.option.markexpr = 'nondestructive and (%s)' % config.option.markexpr
        else:
            config.option.markexpr = 'nondestructive'


@pytest.fixture
def _sensitive_skiping(request, selenium_base_url):
    if request.config.option.skip_url_check:
        return

    item = request.node
    r = requests.get(selenium_base_url, verify=False)
    urls = [h.url for h in r.history] + [r.url]
    def search(url):
        return re.search(request.config.option.sensitive_url, url)
    matches = map(search, urls)
    sensitive = any(matches)


    destructive = 'nondestructive' not in item.keywords
    if sensitive and destructive:
        first_match = next(x for x in matches if x)
        pytest.skip('This test is destructive and the target URL is ' \
                     'considered a sensitive environment. If this test is ' \
                     'not destructive, add the \'nondestructive\' marker to ' \
                     'it. Sensitive URL: %s' % first_match.string)

