# Build brython.js and brython_stdlib.js, then run the tests in www/tests in
# headless Chromium. Requires uv; the test runner requires Playwright
# (pip install playwright && playwright install chromium).
set -e
mkdir -p setup/brython/data
(cd scripts && uv run --no-project --python 3.14 python make_dist.py)
uv run --no-project --python 3.14 --with playwright python scripts/run_browser_tests.py "$@"
