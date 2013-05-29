#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest

pytestmark = pytestmark = [pytest.mark.skip_selenium,
                           pytest.mark.nondestructive]


def testWebDriverWithDefaultTimeout(testdir, webserver):
    file_test = testdir.makepyfile("""
        import pytest
        @pytest.mark.nondestructive
        def test_timeout(mozwebqa):
            assert mozwebqa.timeout == 60
    """)
    testdir.quick_qa(file_test, passed=1)


def testWebDriverWithCustomTimeout(testdir, webserver):
    file_test = testdir.makepyfile("""
        import pytest
        @pytest.mark.nondestructive
        def test_timeout(mozwebqa):
            assert mozwebqa.timeout == 30
    """)
    testdir.quick_qa('--webqatimeout=30', file_test, passed=1)
