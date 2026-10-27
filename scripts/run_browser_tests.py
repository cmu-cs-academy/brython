"""Run the test modules of www/tests in a headless browser (CS Academy fork).

Upstream Brython no longer has an automated test runner, so this script
replaces the QUnit / testem page that we used to run. It serves www/, opens
www/tests/cs_academy_tests.html in headless Chromium with Playwright, and
runs each test module listed by brython_test_utils one at a time.

Usage (after running make_dist.py):

    pip install playwright && playwright install chromium
    python scripts/run_browser_tests.py [test_module.py ...]

The exit code is 1 if a test fails. The modules in KNOWN_FAILURES need a
page setup that this runner doesn't provide: they are run one top-level
statement at a time, and the exit code is 1 unless the statements that fail
are exactly the ones listed, with the same errors. The modules in
ASYNC_TESTS also fail unless the page prints the given line in time.
"""

import functools
import http.server
import json
import os
import socketserver
import sys
import threading
import time

from playwright.sync_api import sync_playwright

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'www')

# module -> {(first line of a top-level statement, last line of its error)}
KNOWN_FAILURES = {
    # Needs files served from /plugins
    'test_import.py': {
        ('load_plugin("/plugins/plugin.py")', 'FileNotFoundError: /plugins/plugin.py'),
    },
    # Need elements and scripts of upstream's www/tests/index.html
    'dom.py': {
        ('Foo = window.get_constructor().new', "AttributeError: 'function' object has no attribute 'new'"),
        ("assert Foo().foo == 'hi'", "NameError: name 'Foo' is not defined"),
        ('Constructor = window.base_class.extend().new', "AttributeError: 'function' object has no attribute 'new'"),
        ("assert Constructor().name == 'base'", "NameError: name 'Constructor' is not defined"),
        ("assert Constructor().extra == 'extra'", "NameError: name 'Constructor' is not defined"),
        ('assert "yellow" in element.classList', 'AssertionError'),
        ('assert len(element.classList) == 2', 'AssertionError'),
        ("elt = document['elt_with_dataset']", "KeyError: 'elt_with_dataset'"),
        ('dataset = elt.dataset', "NameError: name 'elt' is not defined"),
        ('assert dataset[\'value\'] == "coucou"', "NameError: name 'dataset' is not defined"),
        ('assert getattr(dataset, \'value\') == "coucou"', "NameError: name 'dataset' is not defined"),
        ("assert 'value' in dataset", "NameError: name 'dataset' is not defined"),
        ("assert elt.getAttribute('absent') is None", "NameError: name 'elt' is not defined"),
        ('try:', "NameError: name 'dataset' is not defined"),
        ("assert_raises(AttributeError, getattr, dataset, 'absent')", "NameError: name 'dataset' is not defined"),
        ("assert 'absent' not in dataset", "NameError: name 'dataset' is not defined"),
        ('dataset.toto = "tutu"', "NameError: name 'dataset' is not defined"),
        ("assert dataset.toto == 'tutu'", "NameError: name 'dataset' is not defined"),
        ("assert dataset.to_dict() == {'value': 'coucou', 'toto': 'tutu'}", "NameError: name 'dataset' is not defined"),
        ('target = document["test_closest_2495"]', "KeyError: 'test_closest_2495'"),
        ("assert target.closest('.test') is document['test_2495']", "NameError: name 'target' is not defined"),
    },
    'test_webcomponent.py': {
        ("assert class2082 == ['DemoComponent']", 'AssertionError'),
        ("assert t2169 == ['init2169']", 'AssertionError'),
        ("assert ann == [('x', str)], ann", 'AssertionError: []'),
        ('assert icon.className == "demo icon f7-icons"', "AttributeError: 'NoneType' object has no attribute 'className'"),
        ('icon.className = "TEST"', "AttributeError: type object 'NoneType' has no attribute 'className'"),
        ('assert icon.className == "TEST"', "AttributeError: 'NoneType' object has no attribute 'className'"),
    },
}

# module -> line printed in the console when its asynchronous tests are done.
# A failed assertion raises in an event handler, and the line is not printed.
ASYNC_TESTS = {
    'test_web_worker.py': 'all tests ok',
}
ASYNC_TIMEOUT = 20


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def handle(self):
        try:
            super().handle()
        except (BrokenPipeError, ConnectionResetError):
            pass


def check_known(test, errors):
    """Compare the statement failures of a module in KNOWN_FAILURES with the
    expected ones. Return (status, message)."""
    expected = KNOWN_FAILURES[test]
    found = {(stmt, error) for _, stmt, error, _ in errors}
    report = []
    for line, stmt, error, tb in errors:
        if (stmt, error) not in expected:
            report.append(f'New failure at line {line}:\n'
                          f'    {(stmt, error)!r},\n{tb}')
    if errors and errors[0][0] == 0:
        # the module didn't compile: no statement was run
        return 'FAIL', '\n'.join(report)
    for stmt, error in sorted(expected - found):
        report.append(f'Expected failure did not happen, remove it from '
                      f'KNOWN_FAILURES:\n    {(stmt, error)!r},')
    return ('FAIL', '\n'.join(report)) if report else ('KNOWN-FAIL', '')


def wait_for_line(page, line):
    deadline = time.monotonic() + ASYNC_TIMEOUT
    while line not in page.console_lines:
        if time.monotonic() > deadline:
            return False
        page.wait_for_timeout(100)
    return True


def main():
    only = sys.argv[1:]
    socketserver.TCPServer.allow_reuse_address = True
    httpd = socketserver.ThreadingTCPServer(
        ('127.0.0.1', 0), functools.partial(QuietHandler, directory=ROOT))
    port = httpd.server_address[1]
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    url = f'http://127.0.0.1:{port}/tests/cs_academy_tests.html'

    failures = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        def fresh_page():
            page = browser.new_page()
            page.console_lines = []
            page.on('console',
                    lambda message: page.console_lines.append(
                        message.text.strip()))
            page.on('dialog', lambda dialog: dialog.dismiss())
            page.set_default_timeout(120000)
            page.goto(url)
            page.wait_for_function('window.harness_ready === true')
            return page

        page = fresh_page()
        tests = only or page.evaluate('list_tests()')
        for test in tests:
            page.console_lines.clear()
            try:
                if test in KNOWN_FAILURES:
                    ms, errors = page.evaluate(
                        f'run_statements({json.dumps(test)})')
                    status, msg = check_known(test, errors)
                    last_line = (f'{len(errors)} known statement failure(s)'
                                 if status == 'KNOWN-FAIL'
                                 else 'statement failures changed')
                else:
                    state, ms, msg = page.evaluate(
                        f'run_one({json.dumps(test)})')
                    status = 'PASS' if state else 'FAIL'
                    last_line = (msg.strip().splitlines()[-1]
                                 if msg.strip() else '')
                    if state and test in ASYNC_TESTS:
                        if not wait_for_line(page, ASYNC_TESTS[test]):
                            status = 'FAIL'
                            msg = last_line = (
                                f'{ASYNC_TESTS[test]!r} not printed after '
                                f'{ASYNC_TIMEOUT}s')
            except Exception as exc:
                # the page crashed or timed out: report and start a new page
                status, ms, msg = 'FAIL', -1, str(exc).splitlines()[0]
                last_line = msg
                page.close()
                page = fresh_page()
            print(f'{status:10} {test:32} {ms:6}ms {last_line[:120]}',
                  flush=True)
            if status == 'FAIL':
                failures.append((test, msg))

        if not only:
            result = page.evaluate('run_web_worker_test()')
            print(f"{'PASS' if result == 'ok' else 'FAIL':10} "
                  f"{'web_worker_tests.js':32} {result}")
            if result != 'ok':
                failures.append(('web_worker_tests.js', result))
        browser.close()
    httpd.shutdown()

    for test, msg in failures:
        print(f'\n===== {test}\n{msg}')
    print(f'\n{len(failures)} failure(s)')
    sys.exit(1 if failures else 0)


if __name__ == '__main__':
    main()
