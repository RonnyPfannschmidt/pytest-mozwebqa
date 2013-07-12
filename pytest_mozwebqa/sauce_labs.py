#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import httplib
import json

import pytest
from py.xml import html
from selenium import webdriver


def split_class_and_test_names(nodeid):
    names = nodeid.split("::")
    names[0] = names[0].replace("/", '.')
    names = [x.replace(".py", "") for x in names if x != "()"]
    classnames = names[:-1]
    classname = ".".join(classnames)
    name = names[-1]
    return (classname, name)


def make_driver(item, credentials):
    test_id = '.'.join(split_class_and_test_names(item.nodeid))
    options = item.config.option
    keywords = item.keywords

    browser_name = options.browser_name
    browser_version = options.browser_version
    platform = options.platform
    build = options.build


    tags = item.config.getini('sauce_labs_tags')
    from _pytest.mark import MarkInfo
    tags.extend(mark.name for mark in keywords.values()
                if isinstance(mark, MarkInfo))
    capabilities = {
        'build': build or None,
        'name': test_id,
        'tags': tags,
        'public': 'private' not in keywords,
        'restricted-public-info': 'public' not in keywords,
        'platform': platform,
        'browserName': browser_name,
    }

    if browser_version:
        capabilities['version'] = browser_version
    if options.capabilities:
        capabilities.update(json.loads(options.capabilities))
    return start_webdriver_client(credentials, capabilities)


def start_webdriver_client(credentials, capabilities):
    if not credentials['username']:
        raise pytest.UsageError('username must be specified in the sauce labs credentials file.')

    if not credentials['api-key']:
        raise pytest.UsageError('api-key must be specified in the sauce labs credentials file.')

    executor = 'http://%s:%s@ondemand.saucelabs.com:80/wd/hub' % (
        credentials['username'],
        credentials['api-key'])
    return webdriver.Remote(
        command_executor=executor,
        desired_capabilities=capabilities)


class Job(object):

    def __init__(self, session_id):
        self.session_id = session_id

    @property
    def url(self):
        return 'http://saucelabs.com/jobs/%s' % self.session_id

    @property
    def video_html(self):
        flash_vars = 'config={\
            "clip":{\
                "url":"https%%3A//saucelabs.com/jobs/%(session_id)s/video.flv",\
                "provider":"streamer",\
                "autoPlay":false,\
                "autoBuffering":true},\
            "plugins":{\
                "streamer":{\
                    "url":"https://saucelabs.com/flowplayer/flowplayer.pseudostreaming-3.2.5.swf"},\
                "controls":{\
                    "mute":false,\
                    "volume":false,\
                    "backgroundColor":"rgba(0, 0, 0, 0.7)"}},\
            "playerId":"player%(session_id)s",\
            "playlist":[{\
                "url":"https%%3A//saucelabs.com/jobs/%(session_id)s/video.flv",\
                "provider":"streamer",\
                "autoPlay":false,\
                "autoBuffering":true}]}' % {'session_id': self.session_id}

        return html.div(html.object(
            html.param(value='true', name='allowfullscreen'),
            html.param(value='always', name='allowscriptaccess'),
            html.param(value='high', name='quality'),
            html.param(value='true', name='cachebusting'),
            html.param(value='#000000', name='bgcolor'),
            html.param(
                value=flash_vars.replace(' ', ''),
                name='flashvars'),
                width='100%',
                height='100%',
                type='application/x-shockwave-flash',
                data='https://saucelabs.com/flowplayer/flowplayer-3.2.5.swf?0.2930636672245027',
                name='player_api',
                id='player_api'),
            id='player%s' % self.session_id,
            class_='video')

    def send_result(self, result, credentials):
        try:
            basic_authentication = (
                '%s:%s' % (credentials['username'],
                           credentials['api-key'])).encode('base64')[:-1]
            connection = httplib.HTTPConnection('saucelabs.com')
            connection.request(
                'PUT',
                '/rest/v1/%s/jobs/%s' % (credentials['username'], self.session_id),
                json.dumps(result),
                headers={'Authorization': 'Basic %s' % basic_authentication,
                         'Content-Type': 'text/json'})
            connection.getresponse()
        except:
            pass
