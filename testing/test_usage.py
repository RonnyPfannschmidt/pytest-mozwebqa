#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from functools import partial
import pytest

pytestmark = pytestmark = [pytest.mark.skip_selenium,
                           pytest.mark.nondestructive]


@pytest.fixture
def file_test(testdir):
    return testdir.makepyfile("""
        import pytest
        @pytest.mark.nondestructive
        def test_selenium(mozwebqa):
            assert True
    """)


def runtest_one_failure_with_output(testdir, *k, **kw):
    reprec = testdir.inline_run('--tb=short', *k, **kw)
    passed, skipped, failed = reprec.listoutcomes()
    assert len(failed) == 1
    out = failed[0].longrepr.reprcrash.message
    return out


@pytest.fixture
def url_failtest(testdir, file_test, webserver_baseurl):
    return partial(runtest_one_failure_with_output, testdir, file_test, webserver_baseurl)


def testShouldFailWithoutBaseURL(testdir, file_test):
    out = runtest_one_failure_with_output(testdir, file_test)
    assert out == 'UsageError: --baseurl must be specified.'


def testShouldFailWithoutBrowserNameWhenUsingWebDriverAPI(url_failtest):
    out = url_failtest()
    assert out == 'UsageError: --browsername must be specified when using remote selenium.'


def testShouldFailWithoutPlatformWhenUsingWebDriverAPI(url_failtest):
    out = url_failtest('--browsername=firefox')
    assert out == 'UsageError: --platform must be specified when using remote selenium.'


def testShouldFailWithoutSauceLabsUser(testdir, url_failtest):
    sauce_labs_credentials = testdir.makefile('.yaml', sauce_labs="""
        api-key: api-key
    """)
    out = url_failtest('--saucelabs=%s' % sauce_labs_credentials)
    assert out == "KeyError: 'username'"


def testShouldFailWithoutSauceLabsKey(testdir, url_failtest):
    sauce_labs_credentials = testdir.makefile('.yaml', sauce_labs="""
        username: username
    """)
    out = url_failtest('--saucelabs=%s' % sauce_labs_credentials)
    assert out == "KeyError: 'api-key'"


def testShouldFailWithBlankSauceLabsUser(testdir, url_failtest):
    sauce_labs_credentials = testdir.makefile('.yaml', sauce_labs="""
        username:
        api-key: api-key
    """)
    out = url_failtest('--saucelabs=%s' % sauce_labs_credentials)
    assert out == 'UsageError: username must be specified in the sauce labs ' \
                  'credentials file.'


def testShouldFailWithBlankSauceLabsKey(testdir, url_failtest):
    sauce_labs_credentials = testdir.makefile('.yaml', sauce_labs="""
        username: username
        api-key:
    """)
    out = url_failtest('--saucelabs=%s' % sauce_labs_credentials)
    assert out == 'UsageError: api-key must be specified in the sauce labs ' \
                  'credentials file.'



@pytest.mark.chrome
def testShouldErrorThatItCantFindTheChromeBinary(url_failtest):
    out = url_failtest('--driver=chrome',
                       '--chromeopts={"binary_location":"foo"}')
    if 'ChromeDriver executable needs to be available in the path' in out:
        pytest.fail('You must have Chrome Driver installed on your path for this test to run correctly. '
                    'For further information see pytest-mozwebqa documentation.')
    assert 'Could not find Chrome binary at: foo' in out
