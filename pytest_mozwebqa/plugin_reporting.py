

def pytest_addoption(parser):
    group = parser.getgroup("terminal reporting")
    group.addoption('--webqareport',
                    dest='webqa_report_path',
                    metavar='path',
                    default='results/index.html',
                    help='create mozilla webqa custom report file'
                         ' at given path. (default: %default)')


def pytest_configure(config):
    if not hasattr(config, 'slaveinput'):

        if config.option.webqa_report_path:
            from .html_report import HTMLReport
            config._html = HTMLReport(config)
            config.pluginmanager.register(config._html)

def pytest_unconfigure(config):
    html = getattr(config, '_html', None)
    if html:
        del config._html
        config.pluginmanager.unregister(html)
