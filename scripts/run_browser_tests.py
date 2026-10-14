"""Run the test modules of www/tests in a headless browser (CS Academy fork).

Upstream Brython no longer has an automated test runner, so this script
replaces the QUnit / testem page that we used to run. It serves www/, opens
www/tests/cs_academy_tests.html in headless Chromium with Playwright, and
runs each test module listed by brython_test_utils one at a time.

Usage (after running make_dist.py):

    pip install playwright && playwright install chromium
    python scripts/run_browser_tests.py [test_module.py ...]

The exit code is 1 if a test fails, except for the modules in
KNOWN_FAILURES, which need a page setup that this runner doesn't provide.
"""

import functools
import http.server
import json
import os
import socketserver
import sys
import threading

from playwright.sync_api import sync_playwright

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'www')

KNOWN_FAILURES = {
    # Needs files served from /plugins
    'test_import.py',
    # Need elements and scripts of upstream's www/tests/index.html
    'dom.py',
    'test_webcomponent.py',
    'test_web_worker.py',
}


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def handle(self):
        try:
            super().handle()
        except (BrokenPipeError, ConnectionResetError):
            pass


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
            page.on('dialog', lambda dialog: dialog.dismiss())
            page.set_default_timeout(120000)
            page.goto(url)
            page.wait_for_function('window.harness_ready === true')
            return page

        page = fresh_page()
        tests = only or page.evaluate('list_tests()')
        for test in tests:
            try:
                state, ms, msg = page.evaluate(
                    f'run_one({json.dumps(test)})')
            except Exception as exc:
                # the page crashed or timed out: report and start a new page
                state, ms, msg = 0, -1, str(exc).splitlines()[0]
                page.close()
                page = fresh_page()
            last_line = msg.strip().splitlines()[-1] if msg.strip() else ''
            status = 'PASS' if state else (
                'KNOWN-FAIL' if test in KNOWN_FAILURES else 'FAIL')
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
