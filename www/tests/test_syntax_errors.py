# CS Academy: compare Brython's syntax errors (type, message, line) with
# CPython's, recorded in syntax_error_cases.py by
# scripts/make_syntax_error_cases.py.
#
# KNOWN_FAILURES maps a source to the error Brython gives today, when it is
# not CPython's. The test fails if Brython's error changes, for the better or
# the worse: update KNOWN_FAILURES (remove the source if Brython now gives
# CPython's error).

from syntax_error_cases import CASES

KNOWN_FAILURES = {
    'x = 1\n    y = (2,\n':
        ('SyntaxError', "'(' was never closed", 2),
    'x = 1\n    y = 2)\n':
        ('SyntaxError', "unmatched ')'", 2),
    'x = 1\n    y = 2\nz = 3)\n':
        ('SyntaxError', "unmatched ')'", 3),
    'func(\n    a=["unclosed], # Need a quote in this comment: "\n    b=2,\n)\n':
        ('SyntaxError', "closing parenthesis ')' does not match opening parenthesis '['", 4),
    'def f(:\n    pass\nx = 1\n':
        ('SyntaxError', "'(' was never closed", 1),
    'g(1)\nx))\n':
        ('SyntaxError', "closing parenthesis ')' does not match opening parenthesis ')'", 2),
    "f'{a b}'\n":
        ('SyntaxError', "f-string: expecting '=', or '!', or ':', or '}'", 1),
    "f'{a'\nx = (\n":
        ('SyntaxError', 'unterminated string literal (detected at line 1)', 1),
    '[a b c d e f]':
        ('SyntaxError', 'invalid syntax', 1),
    'try:\n  pass\nexcept:\n  pass\nexcept ValueError:\n  pass':
        None,
    '(0x+1)':
        ('not a SyntaxError', 'JavascriptError', None),
    'x = 0xI':
        ('SyntaxError', 'invalid decimal literal', 1),
    'x = 32e-+4':
        ('not a SyntaxError', 'JavascriptError', None),
    'x = 0o9':
        ('not a SyntaxError', 'JavascriptError', None),
    'α = 0xI':
        ('SyntaxError', 'invalid decimal literal', 1),
    "f'''\n            {\n            (123_a)\n            }'''":
        ('SyntaxError', 'invalid syntax. Perhaps you forgot a comma?', 3),
    'f\'\'\'\n            {\n            f"""\n            {\n            (123_a)\n            }\n            """\n            }\'\'\'':
        ('SyntaxError', 'invalid syntax. Perhaps you forgot a comma?', 5),
    'f"""\n\n\n            {\n            6\n            0="""':
        ('SyntaxError', "'{' was never closed", 4),
    'from __future__ import doesnt_exist':
        ('not a SyntaxError', 'JavascriptError', None),
    'from __future__ import braces':
        ('not a SyntaxError', 'JavascriptError', None),
    'x=1\nfrom __future__ import division':
        None,
}


def brython_error(src, mode):
    try:
        compile(src, '<string>', mode)
    except SyntaxError as exc:
        return (type(exc).__name__, exc.msg, exc.lineno)
    except Exception as exc:
        return ('not a SyntaxError', type(exc).__name__, None)
    return None


problems = []
for src, mode, expected in CASES:
    got = brython_error(src, mode)
    if src in KNOWN_FAILURES:
        if got != KNOWN_FAILURES[src]:
            problems.append(f'known failure changed: {src!r}\n'
                            f'    CPython: {expected!r}\n'
                            f'    before:  {KNOWN_FAILURES[src]!r}\n'
                            f'    now:     {got!r}')
    elif got != expected:
        problems.append(f'{src!r}\n'
                        f'    CPython: {expected!r}\n'
                        f'    Brython: {got!r}\n'
                        f'    KNOWN_FAILURE {src!r}: {got!r},')

sources = [src for src, mode, expected in CASES]
for src in KNOWN_FAILURES:
    if src not in sources:
        problems.append(f'not in syntax_error_cases.py: {src!r}')

assert not problems, '\n' + '\n'.join(problems)
