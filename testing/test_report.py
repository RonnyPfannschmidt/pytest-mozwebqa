#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import pytest

pytestmark = pytestmark = [pytest.mark.skip_selenium,
                           pytest.mark.nondestructive]

@pytest.mark.parametrize('reportpath', ['result.html', 'report/result.html'])
def testReport(testdir, reportpath):
    file_test = testdir.makepyfile("""
        import pytest
        @pytest.mark.nondestructive
        def test_report(webtext):
            assert webtext == 'Success!'
    """)
    testdir.quick_qa(
        '--webqareport=%s' % reportpath,
        file_test,
        passed=1)
    assert testdir.tmpdir.join(reportpath).check(file=1)
