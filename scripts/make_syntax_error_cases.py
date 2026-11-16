"""Write www/tests/syntax_error_cases.py (CS Academy fork).

For each program in SOURCES, record the syntax error that CPython gives
(type, message, line). www/tests/test_syntax_errors.py checks that Brython
gives the same. To add a case, add it to SOURCES and run with the Python
version of Brython's release:

    uv run --no-project --python 3.14 python scripts/make_syntax_error_cases.py
"""

import os
import pprint
import sys

# (source, mode); mode is 'exec' if omitted
SOURCES = [
    # Indentation
    "x = 1\n    y = 2\nz = 3\nw = 4\n",
    "def f():\n    a = 1\n        b = 2\n    return a\nprint(f())\n",
    "for i in range(3):\n    print(i)\n      print(i)\nx = 1\n",
    "  x = 1\ny = 2\n",
    " x\n",
    "a\n b\n",
    " \u00b4\n",
    " $\n",
    " x \u00b4\n",
    "x = 1\n y ?\n",
    "if True:\nx = 1\nz = 3\n",
    "if True:\n    x = 1\n  y = 2\nz = 3\n",
    "class A:\n    def f(self):\n        pass\n   x = 1\n",
    "def f(x):\n    print(x)\n\n if 1==1:\n    pass\nelse:\n    topPoint=260\nf(topPoint)\n",
    "def f(x):\n    print(x)\n\n        if 1==1:\n    pass\nelse:\n    topPoint=260\nf(topPoint)\n",
    "x = 1\n    y = (2,\n",
    "x = 1\n    y = 2)\n",
    "x = 1\n    y = 2\nz = 3)\n",
    "if True:\nx = 1\ny = 2)\n",
    "if True:\n    x = 1\n  y = 2\nz = 3)\n",
    # CPython test_traceback.test_bad_indentation
    " print(2)",
    # CPython test_code_module.test_indentation_error
    (" 1", "single"),
    # CPython test_syntax: test_unexpected_indent, test_no_indent,
    # test_bad_outdent
    "foo()\n bar()\n",
    "if 1:\nfoo()",
    "if 1:\n  foo()\n bar()",

    # Brackets. CPython test_syntax.test_error_parenthesis
    "(1 + 2", "[1 + 2", "{1 + 2",
    "a = ( 1, 2, 3\nb=3", "a = [ 1, 2, 3\nb=3", "a = { 1, 2, 3\nb=3",
    ")1 + 2", "]1 + 2", "}1 + 2",
    'func(\n    a=["unclosed], # Need a quote in this comment: "\n    b=2,\n)\n',
    "match y:\n case e(e=v,v,",
    # Brackets with another error before them
    "a b\nx = 1)\n",
    "a b\nx = (1, 2]\n",
    "a b\nx = (1,\n",
    "a b\ny = 2\nz = 3\nprint('x'\n",
    "a b\nprint('x')\n)\n",
    "if x\n    y = 1)\n",
    "if x\n    y = (1, 2]\n",
    "if x\n    y = (1,\n",
    "for x in range(3)\n    print(x))\n",
    "for x in range(3)\n    print(x\n",
    "class A:\n    def f(self)\n        return (1,\n",
    "def f(:\n    pass\nx = 1\n",
    "def f(:\n    pass\nx = 1)\n",
    "x = (1,\ny = 2 +\n",
    "a = (1,\nb c\n",
    "print('a'\nprint('b')\n",
    "x = [1, 2\n",
    "x = 1)\ny = 2\n",
    "x = (1, 2]\ny = 3\n",
    "x = {'a': 1\ny = 2\nz = 3\n",
    "g(1)\nx))\n",
    # f-strings
    "f'{x)}'\n",
    "a b\nf'{x)}'\n",
    "a b\nf'{a]'\n",
    "f'{a b}'\n",
    "f'{a'\nx = (\n",

    # Other errors
    "a b\nx = 1\ny = 2\n",
    "x = 1 +\ny = 2\n",
    "x = 1 +\n",
    "if x\n    y = 1\nz = 2\n",
    "print(1 2)",
    "x = 1\nsun/centerY = 1",
    "if (boat=-10):\n    pass",
    "import",
    "def f():\n    if 1:\n        pass\n    else (x >= 200):\n        pass",
    "def f():\n    return pass",
    "def f():\n    return global x",
    "y = 1 if True else",
    "x: 1, 2",

    # CPython test_exceptions.testSyntaxErrorOffset (str sources)
    'def fact(x):\n\treturn x!\n',
    '1 +\n',
    'def spam():\n  print(1)\n print(2)',
    'Python = "Python" +',
    'Python = "\u1e54\xfd\u0163\u0125\xf2\xf1" +',
    'x = "a',
    'lambda x: x = 2',
    'f{a + b + c}',
    '[file for str(file) in []\n]',
    'a = \xab hello \xbb \xab world \xbb',
    '[\nfile\nfor str(file)\nin\n[]\n]',
    '[file for\n str(file) in []]',
    "ages = {'Alice'=22, 'Bob'=23}",
    'match ...:\n    case {**rest, "key": value}:\n        ...',
    '[a b c d e f]',
    'for x yfff:',
    'f(a for a in b, c)',
    'f(a for a in b if a, c)',
    'f(a, b for b in c)',
    'f(a, b for b in c, d)',
    'class foo:return 1',
    'def f():\n  continue',
    'def f():\n  break',
    'try:\n  pass\nexcept:\n  pass\nexcept ValueError:\n  pass',
    'try:\n  pass\nexcept*:\n  pass',
    'try:\n  pass\nexcept*:\n  pass\nexcept* ValueError:\n  pass',
    '(0x+1)',
    'x = 0xI',
    '0010 + 2',
    'x = 32e-+4',
    'x = 0o9',
    '\u03b1 = 0xI',
    'pass\npass\npass\n(1+)\npass\npass\npass',
    '(1+)',
    '[interesting\nfoo()\n',
    "f'''\n            {\n            (123_a)\n            }'''",
    'f\'\'\'\n            {\n            f"""\n            {\n            (123_a)\n'
        '            }\n            """\n            }\'\'\'',
    'f"""\n\n\n            {\n            6\n            0="""',
    'x = [(yield i) for i in range(3)]',
    'def f():\n  from _ import *',
    'def f(x, x):\n  pass',
    '{i for i in range(5) if (j := 0) for j in range(5)}',
    'def f(x):\n  nonlocal x',
    'def f(x):\n  x = 1\n  global x',
    'nonlocal x',
    'def f():\n  global x\n  nonlocal x',
    'from __future__ import doesnt_exist',
    'from __future__ import braces',
    'x=1\nfrom __future__ import division',
    'foo(1=2)',
    'def f():\n  x, y: int',
    '[*x for x in xs]',
    'foo(x for x in range(10), 100)',
    'for 1 in []: pass',
    '(yield i) = 2',
    'def f(*):\n  pass',
]


def cpython_error(src, mode):
    try:
        compile(src, '<string>', mode)
    except SyntaxError as exc:
        return (type(exc).__name__, exc.msg, exc.lineno)
    return None


def main():
    cases = []
    for item in SOURCES:
        src, mode = item if isinstance(item, tuple) else (item, 'exec')
        cases.append((src, mode, cpython_error(src, mode)))
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..',
                        'www', 'tests', 'syntax_error_cases.py')
    with open(path, 'w', encoding='utf-8') as out:
        out.write(
            '# Generated by scripts/make_syntax_error_cases.py with Python '
            f'{sys.version.split()[0]}. Do not edit.\n'
            '# (source, mode, (type, message, line) of the syntax error that '
            'CPython gives, or None)\n'
            'CASES = ' + pprint.pformat(cases, width=79) + '\n')
    print(f'{len(cases)} cases written to {os.path.normpath(path)}')


if __name__ == '__main__':
    main()
