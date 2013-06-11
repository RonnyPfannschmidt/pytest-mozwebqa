#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import cgi
import datetime
import os

import pkg_resources
import py
import time
from base64 import decodestring as decode_b64


from py.xml import html
from py.xml import raw

import sauce_labs


class HTMLReport(object):

    def __init__(self, config):
        logfile = os.path.expanduser(os.path.expandvars(config.option.webqa_report_path))
        self.logfile = py.path.local(logfile)
        self._debug_path = 'debug'
        self.config = config
        self.test_logs = []
        self.counts = dict.fromkeys(
            'error failed passed skipped xfailed xpassed'.split(),
            0
        )
        self.resources = ('style.css', 'jquery.js', 'main.js')

    def _debug_paths(self, testclass, testmethod):
        root_path = self.logfile.dirpath().join(self._debug_path)
        test_parts = testclass.replace('.', '_'), testmethod
        full_path = root_path.join(*test_parts)
        full_path.ensure(dir=True)
        relative_link = os.path.join(self._debug_path, *test_parts)
        return (relative_link, full_path)

    def _appendrow(self, result, report):
        self.counts[result.lower()] += 1

        testclass, testmethod = sauce_labs.split_class_and_test_names(report.nodeid)
        time = getattr(report, 'duration', 0.0)

        links = {}

        def add_link(text, link):
            links[text] = link

        def add_file(name, filename, content=None):
            if content is not None:
                with full_path.join(filename).open('wb') as fp:
                    fp.write(content)
            add_link(name, os.path.join(relative_link, filename))

        debug = getattr(report, 'debug', {})
        # we only use the last item of the list in values
        debug = dict((k, v[-1]) for k, v in debug.items() if v)
        if debug:
            (relative_link, full_path) = self._debug_paths(testclass, testmethod)

            if 'screenshots' in debug:
                add_file('Screenshot', 'screenshot.png',
                        decode_b64(debug['screenshots']))

            if 'html' in debug:
                add_file('HTML', 'html.txt', debug['html'])

            # Log may contain passwords, etc so we only capture it for tests marked as public
            if 'logs' in debug:
                if 'public' in report.keywords:
                    add_file('Log','log.txt', debug['logs'])
                else:
                    add_link('Log not public', '#')

            if 'urls' in debug:
                add_link('Failing URL', debug['urls'])

        if self.config.option.sauce_labs_credentials_file and hasattr(report, 'session_id'):
            self.sauce_labs_job = sauce_labs.Job(report.session_id)

        if hasattr(self, 'sauce_labs_job'):
            add_link('Sauce Labs Job', self.sauce_labs_job.url)

        links_html = []
        for name, path in links.items():
            links_html.append(html.a(name, href=path))
            links_html.append(' ')

        additional_html = []

        if not 'Passed' in result:

            if hasattr(self, 'sauce_labs_job'):
                additional_html.append(self.sauce_labs_job.video_html)

            if 'Screenshot' in links:
                additional_html.append(
                    html.div(
                        html.a(html.img(src=links['Screenshot']),
                               href=links['Screenshot']),
                        class_='screenshot'))

            if report.longrepr:
                log = html.div(class_='log')
                for line in str(report.longrepr).splitlines():
                    separator = line.startswith('_ ' * 10)
                    if separator:
                        log.append(line[:80])
                    else:
                        exception = line.startswith("E   ")
                        if exception:
                            log.append(html.span(raw(cgi.escape(line)),
                                                 class_='error'))
                        else:
                            log.append(raw(cgi.escape(line)))
                    log.append(html.br())
                additional_html.append(log)

        self.test_logs.append(html.tr([
            html.td(result, class_='col-result'),
            html.td(testclass, class_='col-class'),
            html.td(testmethod, class_='col-name'),
            html.td(round(time), class_='col-duration'),
            html.td(links_html, class_='col-links'),
            html.td(additional_html, class_='debug')], class_=result.lower() + ' results-table-row'))

    def _make_report_dir(self):
        logdir = self.logfile.dirpath()
        logdir.ensure(dir=True)
        # copy across the static resources
        for resfile in self.resources:
            res = py.path.local(
                pkg_resources.resource_filename(
                    __name__, os.path.join('resources', resfile),
                ))
            res.copy(target=logdir.join(resfile))
        return logdir

    def append_pass(self, report):
        self._appendrow('Passed', report)

    def append_failure(self, report):
        if "xfail" in report.keywords:
            self._appendrow('XPassed', report)
        else:
            self._appendrow('Failed', report)

    def append_error(self, report):
        self._appendrow('Error', report)

    def append_skipped(self, report):
        if "xfail" in report.keywords:
            self._appendrow('XFailed', report)
        else:
            self._appendrow('Skipped', report)

    def pytest_runtest_logreport(self, report):
        if report.passed:
            if report.when == 'call':
                self.append_pass(report)
        elif report.failed:
            if report.when != "call":
                self.append_error(report)
            else:
                self.append_failure(report)
        elif report.skipped:
            self.append_skipped(report)

    def pytest_sessionstart(self, session):
        self.suite_start_time = time.time()

    def pytest_sessionfinish(self, session, exitstatus, __multicall__):
        self._make_report_dir()
        logfile = py.std.codecs.open(str(self.logfile), 'w', encoding='utf-8')

        suite_stop_time = time.time()
        suite_time_delta = suite_stop_time - self.suite_start_time
        numtests = sum(self.counts.values())

        option = self.config.option

        server = option.sauce_labs_credentials_file and \
                 'Sauce Labs' or 'http://%s:%s' % (option.host, option.port)
        browser = '%s %s on %s' % (str(option.browser_name).title(),
                                   option.browser_version,
                                   str(option.platform).title())
        generated = datetime.datetime.now()
        configuration = {
            'Base URL': option.base_url,
            'Build': option.build,
            'Driver': option.driver,
            'Firefox Path': option.firefox_path,
            'Google Chrome Path': option.chrome_path,
            'Selenium Server': server,
            'Browser': browser,
            'Timeout': option.webqatimeout,
            'Credentials': option.credentials_file,
            'Sauce Labs Credentials': option.sauce_labs_credentials_file}

        import pytest_mozwebqa
        doc = html.html(
            html.head(
                html.meta(charset='utf-8'),
                html.title('Test Report'),
                html.link(rel='stylesheet', href='style.css'),
                html.script(src='jquery.js'),
                html.script(src='main.js')),
            html.body(
                html.p('Report generated on %s at %s by pytest-mozwebqa %s' % (
                    generated.strftime('%d-%b-%Y'),
                    generated.strftime('%H:%M:%S'),
                    pytest_mozwebqa.__version__)),
                html.h2('Configuration'),
                html.table(
                    [html.tr(html.td(k), html.td(v)) for k, v in sorted(configuration.items()) if v],
                    id='configuration'),
                html.h2('Summary'),
                html.p(
                    '%i tests ran in %i seconds.' % (numtests, suite_time_delta),
                    html.br(),
                    html.span('%(passed)i passed' % self.counts, class_='passed'), ', ',
                    html.span('%(skipped)i skipped' % self.counts, class_='skipped'), ', ',
                    html.span('%(failed)i failed' % self.counts, class_='failed'), ', ',
                    html.span('%(error)i errors' % self.counts, class_='error'), '.',
                    html.br(),
                    html.span('%(xpassed)i expected failures' % self.counts, class_='skipped'), ', ',
                    html.span('%(xfailed)i unexpected passes' % self.counts, class_='failed'), '.'),
                html.h2('Results'),
                html.table([
                    html.thead(html.tr([
                        html.th('Result', class_='sortable', col='result'),
                        html.th('Class', class_='sortable', col='class'),
                        html.th('Name', class_='sortable', col='name'),
                        html.th('Duration', class_='sortable numeric', col='duration'),
                        html.th('Links')]), id='results-table-head'),
                    html.tbody(self.test_logs, id='results-table-body')], id='results-table')))

        logfile.write('<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">' + doc.unicode(indent=2))
        logfile.close()
