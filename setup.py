from setuptools import setup

setup(
    name='pytest-mozwebqa',
    version='1.1',
    description='Mozilla WebQA plugin for py.test.',
    author='Dave Hunt',
    author_email='dhunt@mozilla.com',
    url='https://github.com/davehunt/pytest-mozwebqa',
    packages=['pytest_mozwebqa'],
    package_data={
        'pytest_mozwebqa': [
            'resources/style.css',
            'resources/main.js',
            'resources/jquery.js']},
    install_requires=[
        'pytest>=2.2.4',
        'selenium>=2.26.0',
        'pyyaml',
        'requests',
    ],
    entry_points={
        'pytest11': [
            'mozwebqa = pytest_mozwebqa.pytest_mozwebqa',
            'mozwebqa_safety = pytest_mozwebqa.plugin_safety',
            'mozwebqa_reporting = pytest_mozwebqa.plugin_reporting',
            'mozwebqa_credentials = pytest_mozwebqa.plugin_data',
        ]},
    license='Mozilla Public License 2.0 (MPL 2.0)',
    keywords='py.test pytest selenium saucelabs mozwebqa webqa qa mozilla',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)',
        'Operating System :: POSIX',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: MacOS :: MacOS X',
        'Topic :: Software Development :: Quality Assurance',
        'Topic :: Software Development :: Testing',
        'Topic :: Utilities',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7'])
