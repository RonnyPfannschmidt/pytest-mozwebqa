#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import pytest

pytestmark = pytestmark = [pytest.mark.skip_selenium,
                           pytest.mark.nondestructive]

failure_files = ('screenshot.png', 'html.txt')


def assert_has_debug_files(root):
    path = root.join('debug')
    # debug subtree is test_id/test_name
    # and only one exists in the tests here
    path = path.listdir()[0].listdir()[0]
    for file in failure_files:
        assert path.join(file).check(file=True)


def testDebugOnFail(testdir):
    file_test = testdir.makepyfile("""
        import pytest
        @pytest.mark.nondestructive
        def test_debug(webtext):
            assert webtext != u'Success!'
    """)
    testdir.quick_qa(file_test, failed=1)
    assert_has_debug_files(testdir.tmpdir)

def testDebugOnXFail(testdir, webserver):
    file_test = testdir.makepyfile("""
        import pytest
        @pytest.mark.xfail
        @pytest.mark.nondestructive
        def test_debug(webtext):
            assert webtext != u'Success!'
    """)
    reprec = testdir.quick_qa(file_test, skipped=1)
    assert_has_debug_files(testdir.tmpdir)


def testNoDebugOnPass(testdir,tmpdir, webserver):
    file_test = testdir.makepyfile("""
        import pytest
        @pytest.mark.nondestructive
        def test_debug(webtext):
            assert webtext == u'Success!'
    """)
    testdir.quick_qa(file_test, passed=1)
    assert not tmpdir.join('debug').check()


def testNoDebugOnXPass(testdir, tmpdir, webserver):
    file_test = testdir.makepyfile("""
        import pytest
        @pytest.mark.xfail
        @pytest.mark.nondestructive
        def test_debug(webtext):
            assert webtext == 'Success!'
    """)
    testdir.quick_qa(file_test, failed=1)
    assert not tmpdir.join('debug').check()


def testNoDebugOnSkip(testdir, tmpdir):
    file_test = testdir.makepyfile("""
        import pytest
        @pytest.mark.skipif('True')
        @pytest.mark.nondestructive
        def test_debug(webtext):
            assert webtext == 'Success!'
    """)
    reprec = testdir.quick_qa(file_test, skipped=1)
    assert not tmpdir.join('debug').check()


def testDebugWithReportSubdirectory(testdir):
    file_test = testdir.makepyfile("""
        import pytest
        @pytest.mark.nondestructive
        def test_debug(webtext):
            assert webtext != 'Success!'
    """)
    report_subdirectory = 'report'
    reprec = testdir.quick_qa(
        '--webqareport=%s/result.html' % report_subdirectory,
        file_test,
        failed=1)
    assert_has_debug_files(testdir.tmpdir.join(report_subdirectory))


