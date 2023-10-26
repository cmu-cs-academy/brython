import os
import builtins

dest_dir = os.path.join(os.path.dirname(os.getcwd()), "www", "src")

with open(os.path.join(dest_dir, 'py_flags.js'), 'w', encoding='utf-8') as out:

    out.write('(function($B){\n' +
              '$B.builtin_class_flags = {\n')
    flags = {}

    def add_flag(flag, attr):
        if flag in flags:
            flags[flag].add(attr)
        else:
            flags[flag] = set([attr])

    for attr in dir(builtins):
        if attr == '__loader__':
            continue
        obj = getattr(builtins, attr)
        if hasattr(obj, '__flags__'):
            #if not (obj.__flags__ & TPFLAGS['BASETYPE']):
            add_flag(obj.__flags__, attr)


    out.write('    builtins: {\n')
    for flag in flags:
        out.write(f"        {flag}: {list(flags[flag])}," + '\n')
    out.write('    },\n    types: {\n')
    flags = {}
    import types
    for attr in dir(types):
        obj = getattr(types, attr)
        if (hasattr(obj, '__module__')
                and obj.__module__ == 'builtins'
                and hasattr(obj, '__flags__')):
            add_flag(obj.__flags__, obj.__name__)

    for flag in flags:
        out.write(f"        {flag}: {list(flags[flag])}," + '\n')
    out.write('    }\n}\n})(__BRYTHON__)')
