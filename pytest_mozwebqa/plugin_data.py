import pytest

def pytest_addoption(parser):

    group = parser.getgroup('credentials', 'credentials')
    group._addoption("--credentials",
                     action="store",
                     dest='credentials_file',
                     metavar='path',
                     help="location of yaml file containing user credentials.")
    group._addoption('--saucelabs',
                     action='store',
                     dest='sauce_labs_credentials_file',
                     metavar='path',
                     help='credendials file containing sauce labs username and api key.')



def read(filename):
    stream = file(filename, 'r')
    import yaml
    return yaml.safe_load(stream)

def maybe_read(filename):
    if filename is not None:
        return read(filename)


@pytest.fixture(scope='session')
def mozwebqa_credentials(request):
    return maybe_read(request.config.option.credentials_file)


@pytest.fixture(scope='session')
def mozwebqa_saucelab_credentials(request):
    return maybe_read(request.config.option.sauce_labs_credentials_file)
