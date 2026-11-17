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
    'f"{x:3\n':
        ('SyntaxError', "f-string: expecting '}', or format specs", 1),
    'if 1:\n        x = 1\n\ty = 2\n':
        None,
    "x = b'\\x]0'\n":
        ('SyntaxError', ["(unicode error) 'unicodeescape' codec can't decode bytes in position 0-1: truncated \\xXX escape"], 1),
    "x = f'(1):.3g}'\n":
        ('SyntaxError', 'invalid syntax', 1),
    "x = f'{z:=5'\n":
        ('SyntaxError', 'unterminated f-string literal (detected at line 1)', 1),
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
