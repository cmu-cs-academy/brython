# Merging a new upstream Brython release into the CS Academy fork

Read [CS_ACADEMY_FORK.md](CS_ACADEMY_FORK.md) first: it lists every
difference between the fork and upstream, and why each exists.

## Merge

```
git remote add brython-dev https://github.com/brython-dev/brython.git  # once
git fetch brython-dev --tags

git checkout -b merge-<version>
git merge <tag>          # merge a tagged release, e.g. 3.14.0
```

Resolve the conflicts. For files that changed a lot upstream, it is usually
easiest to take upstream's version (`git checkout --theirs <file>`) and reapply
the fork's changes listed in CS_ACADEMY_FORK.md. Drop the fork changes that
upstream has made too, and update CS_ACADEMY_FORK.md.

Delete the generated files that the merge brings back:

* www/src/brython.js
* www/src/brython_stdlib.js
* www/src/stdlib_paths.js
* www/src/version_info.js

Consider cherry-picking upstream bug fixes made after the release
(`git log <tag>..brython-dev/master`). Use `git cherry-pick -x`, and don't
commit the generated files that these commits usually include.

## Test

`./build_and_run.sh` builds brython.js with Python 3.<minor version of
Brython> (through `uv`) and runs the tests of www/tests in headless Chromium.
You need Playwright: `pip install playwright && playwright install chromium`
(build_and_run.sh uses `uv run --with playwright`). Run a single test module
with `./build_and_run.sh test_list.py`.

A few modules are expected to fail (see `KNOWN_FAILURES` in
scripts/run_browser_tests.py). Failures in core features (lists, sets,
strings, exceptions / tracebacks, Javascript objects) must be investigated.
`www/tests/test_cs_academy.py` tests the features of the fork.

Also compare the speed with the previous version on code similar to student
programs (classes, attribute access, loops, floats).

## Copy to cs-academy

In cs-academy, check out a new branch off of main. Then in brython, run
`./copy_to_af.sh`. In cs-academy:

* Eyeball the changes, especially new files.
* Consider running `git diff -G 'import' HEAD -- . :^frontend/src/brython/brython.js :^frontend/src/brython/brython_stdlib.js :^frontend/src/cmu-graphics-brython.js` to check for added imports.
* The modules bundled with cmu_graphics are listed in `CS_ACADEMY_MODULES` in
  buildCmuGraphics in build.py. Modules that are not bundled are downloaded
  synchronously at runtime when they are imported. To see which modules are
  imported, load the page and look at `Object.keys(__BRYTHON__.imported)`, or
  at the requests for `/Lib/` and `/libs/` in the network tab. If a module is
  missing from the list, py2js may fail to load during the content build
  (backend/scripts/py2js/py2js.py).
* Run `python build.py cmu-graphics`.
* Run the tests: "Test autograder" and "Test animation framework" in the
  Tests tab of gui.py, the Playwright tests in integration-tests, and a
  content build (the solutions are compiled with the new Brython).
* Check that backend/compile_brython.js still works with the new brython.js
  under Node.
