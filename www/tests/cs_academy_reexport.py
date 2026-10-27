# Used by test_cs_academy.py: a module that exports a Javascript function, like
# cmu_graphics exports functions of cmu-graphics.js
from browser import window

window.eval("window.cs_academy_add = function(a, b){ return a + b }")
js_add = window.cs_academy_add

def py_func():
    return 'py'

__all__ = ['js_add', 'py_func']
