#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest

pytestmark = pytestmark = [pytest.mark.skip_selenium,
                           pytest.mark.nondestructive]


def testNonDestructiveTestsRunByDefault(testdir, webserver):
    file_test = testdir.makepyfile("""
        import pytest
        @pytest.mark.nondestructive
        def test_selenium():
            assert True
    """)
    reprec = testdir.inline_run(file_test)
    passed, skipped, failed = reprec.listoutcomes()
    assert len(passed) == 1


def testDestructiveTestsRunWhenForced(testdir, webserver):
    file_test = testdir.makepyfile("""
        import pytest
        def test_selenium():
            assert True
    """)
    reprec = testdir.inline_run('--destructive', file_test)
    passed, skipped, failed = reprec.listoutcomes()
    assert len(passed) == 1


def testBothDestructiveAndNonDestructiveTestsRunWhenForced(testdir, webserver):
    file_test = testdir.makepyfile("""
        import pytest
        @pytest.mark.nondestructive
        def test_selenium1():
            assert True
        def test_selenium2():
            assert True
    """)
    reprec = testdir.inline_run('--destructive', file_test)
    passed, skipped, failed = reprec.listoutcomes()
    assert len(passed) == 2


def testSkipDestructiveTestsIfForcedAndRunningAgainstSensitiveURL(testdir, webserver):
    file_test = testdir.makepyfile("""
        import pytest
        def test_selenium(mozwebqa):
            assert True
    """)
    reprec = testdir.inline_run('--baseurl=http://localhost:%s' % webserver.port,
                                '--sensitiveurl=localhost',
                                '--destructive',
                                file_test)
    passed, skipped, failed = reprec.listoutcomes()
    assert len(skipped) == 1
