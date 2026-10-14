# Differences between the CS Academy fork and upstream Brython

This fork is based on the **3.14.0** release of
[brython-dev/brython](https://github.com/brython-dev/brython), plus a few
bug fixes cherry-picked from later upstream commits. This document lists
every intentional difference from upstream and why it exists. Please keep it
up to date when you change the fork, and check it when merging a new upstream
release (see [HOW_TO_MERGE_CS_ACADEMY.md](HOW_TO_MERGE_CS_ACADEMY.md)).

To see the full diff with upstream:

    git diff 3.14.0 HEAD -- www/src setup scripts

Changes in the Brython source code are marked with a `CS Academy` comment, so
`git grep -n "CS Academy"` finds most of them.

Why 3.14.0 and not a later 3.14.x: 3.14.1 (May 2026) was the first release
after a rewrite of Brython's object model (upstream branch `tp_methods_2025`:
objects have `ob_type` instead of `__class__`, CPython-style type slots,
`$B.RAISE`, ...). Almost every patch in this fork and much of
`cmu-graphics.js` depends on the old object model, and in a benchmark of
CS Academy-like code 3.14.3 was slower than 3.14.0 for class instances and
float arithmetic. Moving to the new object model should be a project of its
own.

## 1. Javascript <-> Python conversions

cmu_graphics passes values between Python and Javascript all the time, and
relies on the conversions that Brython did before version 3.12. Upstream has
changed them since; the fork keeps the old ones.

| Value | Upstream | Fork |
|---|---|---|
| Javascript `null` received by Python | `javascript.NULL` | `None` |
| Python `None` passed to Javascript | the Brython `None` object | `null` |
| Javascript array received by Python (`jsobj2pyobj`) | the array itself, an instance of `javascript.Array` (not a subclass of `list`) | a new Python `list` whose items are converted. An array created from a Python list by `pyobj2jsobj` gives back the original list. Arrays that contain themselves are supported. |
| Javascript array without `__class__` seen by Python (e.g. values of `dict(jsobj)`) | `javascript.Array` | `list` (`get_class` sets `__class__` as a non-enumerable property) |

- Files: `www/src/js_objects.js` (`jsobj2pyobj`, `js_array_to_list`,
  `pyobj2jsobj`), `www/src/py_utils.js` (`$B.get_class`).
- Examples of code that depends on this: `jsTranslationObj2PyDict` and
  `Line.__getattr__` in cmu_graphics.py (`isinstance(..., list)`), and every
  dict with `None` values sent to the page with `sendJSEvent` (the browser
  can't clone the Brython `None` object in `postMessage`).
- Trade-off: changing a list received from Javascript doesn't change the
  Javascript array. cmu_graphics never does this.
- `www/src/Lib/browser/local_storage.py` accepts `None` as well as
  `javascript.NULL` from `getItem()`.
- Upstream tests that check the upstream behavior are adapted or disabled
  (marked `CS Academy`) in `www/tests/test_jsobjects.py` and
  `www/tests/issues.py`.

Javascript functions reached by attribute access (e.g. `window.f` or
`_cg.angleTo`) are wrapped so that their arguments are converted to Javascript
(as upstream). But a Javascript function **returned by a call** to a
Javascript function is returned as is, as before 3.12 (upstream wraps it too):
Python then calls it with Brython objects (`None`, Brython floats, lists...)
and keyword arguments as `{$kw: ...}`. cmu-graphics.js relies on this: the
`...Bry()` functions (`jsSetWithTypeCheckBry()`, `jsInitShapeBry()`...) and
`jsDrawRect()` etc. return functions that expect Brython values, for instance
`brythonColorToJsColor()` compares the value with `_b_.None`.

Keyword arguments in a call to a Javascript function from Python are passed
as the Brython object `{$kw: [{name: value, ...}]}` (the last argument), as
before 3.12; upstream raises `TypeError`. `drawRect()` etc. in cmu-graphics.js
(MVC programs) read them this way.

`pyobj2jsobj` also returns Python ints and strs (Javascript numbers and
strings) immediately, before the class checks. This is only for speed.

## 2. Hooks used by cmu_graphics

- **`__js_getattribute__` / `__js_setattribute__`**
  (`www/src/py_builtin_functions.js`, `$B.$getattr` and `$B.$setattr`).
  A Javascript object can handle Python attribute access itself by defining
  these methods. cmu-graphics.js uses this for the `app` object
  (`class AppWrapper`), whose `__class__` is a fake class that also defines
  `__js_getattribute__`. The hooks are checked only when the object has no
  `__class__`, or its class has no `__getattribute__` / `__setattr__`. Checking
  them at the start of `$B.$getattr` made attribute access on class instances
  about 9% slower.
- **`$B.EventTarget` and the `open()` event**
  (`www/src/py_builtin_functions.js`). `open()` dispatches a
  `function-call` event with `detail.function == '_b_.open'`. cmu-graphics.js
  uses it to disable copying from the shell when a program opens a file.
- **`$B.calculate_suggestions`** (`www/src/py_exceptions.js`). The function
  that computes "Did you mean ...?" suggestions is exposed so that
  cmu_graphics.py can replace it with a Python function, which filters out
  translated names. The callers accept `None`, `null` or `undefined` for "no
  suggestion". Suggestions for a `NameError` also search the builtins (e.g.
  `Flase` -> `False`), like CPython does.
- **Importing Javascript functions from a Python module**
  (`www/src/py_import.js`, `$B.$import_from`). For `from module import name`
  and `from module import *` with `__all__`, upstream replaces a Javascript
  function wrapper by the raw function (fix for issue 2395). Calling the raw
  function from Python passes Brython objects (eg floats) unconverted, so
  `getPointInDir`, `angleTo`, `distance` etc. imported from cmu_graphics
  received `NaN`. The fork unwraps only wrappers around Python functions, which
  is the case of issue 2395.
- **Translated `repr()` of booleans** (`www/src/py_int.js`). `repr(True)` is
  `Verdadero` / `Wahr` when `$B.cmuGraphicsLanguage` is `es` / `de`.
- **`brython_path` option** (`www/src/py2js.js`, `$B.parse_options`).
  `brython({brython_path: '/'})` sets the URL used to import the standard
  library. cmu-graphics.js runs Brython in a web worker whose script is not in
  the directory that holds `Lib/` and `libs/`.

## 3. Lockdown of student programs

When cmu-graphics.js sets `$B.lockdown`:

- `import browser`, `import cmu_graphics`, and `from cmu_graphics import window`
  raise `ModuleNotFoundError` (`www/src/py_import.js`, `$B.$__import__`).
- `eval()` / `exec()` of a string that contains `__import__` raises an
  exception (`www/src/py_builtin_functions.js`, `eval`).

Because student programs can't import `browser`, standard library modules that
student programs import must not import it either: see `time` below.

## 4. Code generated by `python_to_js`

Solutions are compiled to Javascript on the server (backend/compile_brython.js)
or in another page (backend/scripts/py2js), then run in the cmu_graphics web
worker.

- `from_py()` (`www/src/brython_builtins.js`) uses a random name
  (`$python_to_js` + random number) as file name **and module name**, as
  Brython did before 3.12. Upstream uses a file name based on the page URL and
  the `script_id` as module name. With the upstream names, all the solutions
  run in the cmu_graphics worker (compiled with the same `script_id`,
  `__main_soln__`) shared one namespace: names defined by one solution (e.g.
  `onKeyPress`) were still defined when the next solution ran. A consequence:
  `__name__` in the generated code is the random name, not the `script_id`.
- The code generated for a module (`www/src/ast_to_js.js`,
  `Module.prototype.to_js`) registers the module in `$B.imported` and
  `$B.url2name` if it isn't there yet, i.e. if the code was compiled in
  another Brython instance.

## 5. Other runtime changes

- `$B.language` defaults to `'en'` when the browser gives no language
  (`www/src/brython_builtins.js`).
- When importing a module, an HTML response is treated as a 404
  (`www/src/py_import.js`, `$download_module`). The CS Academy server returns
  `index.html` for unknown URLs.
- `isinstance('a', object)` is `True` (`www/src/py_builtin_functions.js`,
  `$B.$isinstance`). Upstream returns `False`.
- `str(b'a', 5)` and `str(b'a', 'utf-8', 5)` raise `TypeError`
  (`www/src/py_string.js`). Upstream accepts them.
- `del globals()[name]` (`www/src/py_utils.js`, `$B.$delitem`, and
  `dict.__contains__` in `www/src/py_dict.js`): upstream replaces the name by a
  property that raises `NameError` when it is read (issue #2423), but the
  property stayed enumerable, so `name in globals()` and iterating on
  `globals()` raised `NameError`, and a name set again after being deleted could
  not be changed. `setupMvc()` in cmu_graphics deletes names from the globals
  of MVC programs, then `registerGlobals(globals())` iterates on them.
- `frame.f_builtins` (`www/src/py_exceptions.js`) falls back to the
  builtins module when the globals have no `__builtins__` (the globals of
  student programs in cmu_graphics). The traceback module of CPython 3.14
  reads it to make suggestions, so `traceback.format_exc()` failed for every
  `NameError` in student programs.
- `trace_from_stack()` (`www/src/py_exceptions.js`): resetting `src` for each
  frame is backported from 3.14.3 (upstream 3.14.0 crashed with a Javascript
  error for `exec()` frames), and two error paths that looped forever now move
  to the next frame (still a bug upstream).

## 6. Standard library (`www/src/Lib`)

cmu_graphics imports `random`, `traceback`, `linecache`, `math` and `sys`.
These modules and their imports are bundled in cmu-graphics-brython.js (see
`CS_ACADEMY_MODULES` in the cs-academy repository's build.py). Any other
module would be downloaded synchronously at runtime, so the fork keeps the
imports of these modules small.

- **random.py**: doesn't import `os` or `_collections_abc`. `SystemRandom` is
  commented out (it needs `os.urandom`). `sample()` checks for builtin
  sequence types instead of `_Sequence`. `warnings` is imported only when
  `_warn` is called: importing `warnings` runs `_py_warnings._setup_defaults()`,
  which imports `re` and `enum`.
- **time.py**: doesn't import `browser` (not allowed in student programs,
  see Lockdown). `time.sleep()` raises an exception with a CS Academy message.
- **traceback.py** (CPython 3.14 version):
  - Only `itertools`, `linecache` and `sys` are imported at the top level.
    `contextlib.suppress`, `textwrap.indent` / `dedent`, and
    `collections.namedtuple` (`_Anchors`) are replaced by small local versions.
    `_colorize` (which imports `dataclasses` and `typing`) is replaced by a stub
    that never adds colors. Other imports happen where they are used.
  - `__notes__` are shown if they are a list or tuple (instead of any
    `collections.abc.Sequence`).
  - `_find_keyword_typos()` (suggestions for misspelled keywords in a
    `SyntaxError`, new in 3.14) is disabled: it imports `tokenize`, `difflib`
    and `codeop`.
  - Line numbers: `_walk_tb_with_full_positions()` uses `tb_lineno` when the
    position given by `tb_lasti` is on another line. Brython doesn't update
    `tb_lasti` for every instruction, so frames above the one that raised the
    exception could show the line of an earlier statement. This is still a bug
    upstream.
- **linecache.py**: same as upstream. (Earlier versions of the fork modified
  it; cmu_graphics.py now replaces `linecache.updatecache`.)
- **_operator.py**: `index()` says `'float' object cannot be interpreted as an
  integer` (like CPython) instead of `'<class 'float'>' object ...`. Students
  see it when they pass a float to `randrange()`, which raises `TypeError`
  since Python 3.12 (it only warned in 3.10 and 3.11).
- **subprocess.py**: catches `ImportError` as well as `ModuleNotFoundError`
  when importing `msvcrt`.

## 7. Upstream fixes cherry-picked after 3.14.0

These commits come from upstream master between 3.14.0 and the merge of the
`tp_methods_2025` branch, so they apply to the old object model. They are
recorded with "(cherry picked from commit ...)".

| Upstream commit | Fix |
|---|---|
| f78ff4604 | `delattr` bug; restores `www/tests/test_classes.py` |
| a8e72a540 | `del C.attr` didn't delete class attributes |
| 18bd18f59 | #2614: `__init__` with unexpected keyword arguments |
| b7e6aa53d | #2632: "SEQ is not iterable" in Firefox 145+ when importing modules that use decorators (`enum`, `re`, `random`...) |
| 45d6ae26b | #2636 / #2637: `json.loads('')` raised a Javascript error |
| d43e28a60 | #2658: comparison of ints and floats (`10**20 == 1e20`) |
| 89ff14cfc | #2659: `str.__doc__` |
| adfc348ea | #2661: `int('-')` and `int('+')` returned 0 (adapted: `$B.RAISE` doesn't exist in 3.14.0) |

Known upstream bugs that are not fixed in the fork: `round(2.675, 2)`
returns `2.68` (CPython: `2.67`), `float('inf') > 10**400` is `False`,
`float('1e500')` raises `ValueError`, `hash(-1)` is `-1`.

## 8. Build, tests and tooling

- Generated files are not committed: `www/src/brython.js`,
  `brython_stdlib.js`, `stdlib_paths.js`, `version_info.js` etc. (see
  `.gitignore`). Build them with `scripts/make_dist.py` (requires Python 3.14).
- **setup/brython**: `python -m brython make_modules` builds
  `brython_modules.js` from the comma-separated list of modules in the
  environment variable `CS_ACADEMY_MODULES` instead of inspecting the
  application. It searches `brython_stdlib.js` from `..` and the user modules
  in `../..` (it is run from `frontend/src/brython/setup` in cs-academy). The
  output is deterministic: sorted modules, `$timestamp` set to 0, and no
  `VFS_timestamp` line.
- **copy_to_af.sh** builds Brython and copies it to the cs-academy repository.
  `Lib` and `libs` are replaced, so that modules removed from Brython are
  removed from cs-academy too.
- **Tests**: `scripts/run_browser_tests.py` runs the modules of `www/tests` in
  headless Chromium with Playwright, plus a web worker test for
  `python_to_js` (`www/tests/web_worker_tests.js`). Upstream removed the QUnit
  page that the fork used to run with testem. `build_and_run.sh` builds and
  runs the tests; GitHub Actions (`.github/workflows/ci.yml`) runs them on pull
  requests. `test_import.py`, `dom.py`, `test_webcomponent.py` and
  `test_web_worker.py` are expected to fail because they need the page setup of
  upstream's `www/tests/index.html`.
- `www/tests/test_cs_academy.py` tests the features of this document.
- Other test changes: tests for fork-specific fixes added to `issues.py`,
  `test_math.py`, `test_strings.py`, `test_classes.py`, `test_numbers.py`,
  `test_set.py`, `test_exceptions.py`, `test_suite.py`. In
  `test_exceptions.py`, the frames expected for an exception in a list
  comprehension no longer include `<listcomp>` (PEP 709, Python 3.12).
  `test_secrets.py` is not run (`SystemRandom` is not available).

## 9. Fork changes dropped when merging 3.14.0

For reference, these older fork changes are gone because upstream fixed the
same issues or the code no longer exists:

- Syntax error fixes in the legacy parser in `py2js.js` (upstream now uses
  the PEG parser; the tests for issues 2071, 2232, 2303 and 2304 still pass).
- Fixes now in upstream: `float.__int__` and `float()` error messages,
  `int('')`, `hash()` returning a non-int, `set.pop()` with arguments, `type()`
  of big ints, augmented `/=` returning a float, empty `str.isalpha()` /
  `isalnum()`, `math` functions with non-numbers, `tb.py` suggestions,
  `NameError` suggestions in `$B.name_error`, the Javascript class check in
  `JSObj.__getattribute__`, the `datetime.now()` workaround.
- Workarounds for old browsers (Safari 10: `Object.values`), `$B` in exception
  factories (`be_factory` no longer exists), the `t0` timing variable in
  `py_dict.js`.
