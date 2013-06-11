#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import json

import pytest
from selenium.webdriver.common.proxy import Proxy
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium import selenium
from selenium import webdriver


class NoProxy(object):
    def add_to_capabilities(self, caps):
        pass


def proxy_from_options(options):
    if options.proxy_host and options.proxy_port:
        proxy_str = '%(proxy_host)s:%(proxy_port)s' % vars(options)
        proxy = Proxy()
        proxy.ssl_proxy = proxy.http_proxy = proxy_str
        return proxy
    else:
        return NoProxy()


def make_driver(item, *k):
    options = item.config.option
    capabilities = json.loads(options.capabilities)
    proxy = proxy_from_options(options)
    proxy.add_to_capabilities(capabilities)
    return start_webdriver_client(options, capabilities)


def start_webdriver_client(options, capabilities):
    specific_setup = '%s_driver' % options.driver.lower()
    make_webdriver = globals().get(specific_setup, generic_driver)
    return make_webdriver(options, capabilities)


def generic_driver(options, capabilities):
    return getattr(webdriver, options.driver)()


def opera_driver(options, capabilities):
    capabilities.update(webdriver.DesiredCapabilities.OPERA)
    return webdriver.Opera(
        executable_path=options.opera_path,
        desired_capabilities=capabilities)


def remote_driver(options, capabilities):
    if not options.browser_name:
        raise pytest.UsageError('--browsername must be specified'
                                ' when using remote selenium.')

    if not options.platform:
        raise pytest.UsageError('--platform must be specified'
                                ' when using remote selenium.')

    capabilities.update(getattr(webdriver.DesiredCapabilities,
                                options.browser_name.upper()))
    if json.loads(options.chrome_options) or options.extension_paths:
        capabilities = create_chrome_options(options).to_capabilities()
    if options.browser_name.upper() == 'FIREFOX':
        profile = create_firefox_profile(options)
    if options.browser_version:
        capabilities['version'] = options.browser_version
    capabilities['platform'] = options.platform.upper()
    executor = 'http://%s:%s/wd/hub' % (options.host, options.port)
    try:
        return webdriver.Remote(
            command_executor=executor,
            desired_capabilities=capabilities or None,
            browser_profile=profile)
    except AttributeError:
        valid_browsers = [
            attr for attr in dir(webdriver.DesiredCapabilities)
            if not attr.startswith('__')
        ]
        raise AttributeError(
            "Invalid browser name: '%s'. Valid options are: %s" %
            (self.browser_name, ', '.join(valid_browsers)))


def chrome_driver(options, capabilities):
    chrome_options = create_chrome_options(options)
    extra = {}
    if options.chrome_path:
        extra['executable_path'] = options.chrome_path
    return webdriver.Chrome(
        chrome_options=chrome_options,
        desired_capabilities=capabilities or None,
        **extra)


def firefox_driver(options, capabilities):
    if options.firefox_path:
        binary = FirefoxBinary(options.firefox_path)
    else:
        binary = None
    profile = create_firefox_profile(options)
    return webdriver.Firefox(
        firefox_binary=binary,
        firefox_profile=profile,
        capabilities=capabilities or None)


def create_firefox_profile(options):
    profile = webdriver.FirefoxProfile(options.profile_path)
    for k, v in json.loads(options.firefox_preferences or '{}').items():
        profile.set_preference(k, v)
    profile.assume_untrusted_cert_issuer = options.assume_untrusted
    profile.update_preferences()
    for extension in options.extension_paths:
        profile.add_extension(extension)
    return profile


def create_chrome_options(pytest_options):
    options_from_json = json.loads(pytest_options.chrome_options)
    options = webdriver.ChromeOptions()

    if 'arguments' in options_from_json:
        for args_ in options_from_json['arguments']:
            options.add_argument(args_)

    if 'binary_location' in options_from_json:
        options.binary_location = options_from_json['binary_location']

    for extension in pytest_options.extension_paths:
        options.add_extension(extension)

    return options
