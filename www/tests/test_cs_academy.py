"""Tests for the features of the CS Academy fork of Brython.

See CS_ACADEMY_FORK.md at the root of the repository.
"""
from browser import window
import javascript
from tester import assert_raises

# Javascript objects that emulate Python objects with __js_getattribute__
# and __js_setattribute__, like the "app" object of cmu_graphics (class
# AppWrapper in cmu-graphics.js)
window.eval("""
window.make_app_like = function(){
    var store = new Map([['width', 400]])
    var obj = {
        __class__: {
            __name__: 'App',
            $infos: {__name__: 'App'},
            __mro__: [],
            __js_getattribute__: function(attr, _default){
                if(attr === '__str__' || attr === '__repr__'){
                    return () => '<App object>'
                }
                if(['__eq__', '__ne__', '__lt__', '__le__', '__gt__',
                        '__ge__'].includes(attr)){
                    return () => __BRYTHON__.builtins.NotImplemented
                }
            }
        },
        __js_getattribute__: function(attr, _default){
            var res = store.get(attr)
            if(res === undefined){
                if(_default !== undefined){
                    return _default
                }
                throw __BRYTHON__.attr_error(attr, this)
            }
            return res
        },
        __js_setattribute__: function(attr, value){
            store.set(attr, value)
        }
    }
    return obj
}
""")

app = window.make_app_like()
assert app.width == 400
app.x = 5
assert app.x == 5
app.x += 1
assert app.x == 6
assert getattr(app, 'missing', 'default') == 'default'
assert_raises(AttributeError, getattr, app, 'missing')
assert str(app) == '<App object>'
assert repr(app) == '<App object>'
assert app != 3

def f():
    # attribute access in a function, with the same names as an instance
    class A:
        def __init__(self):
            self.width = 10
    a = A()
    return a.width + app.width
assert f() == 410

# None <-> null, Javascript arrays <-> lists
window.eval("""
window.cs_js_null = function(){ return null }
window.cs_js_is_null = function(x){ return x === null }
window.cs_js_array = function(){ return [1, 2.5, null, [3]] }
window.cs_js_obj = {keys: ['a', 'b'], es: {a: ['aa']}, n: null}
""")
assert window.cs_js_null() is None
assert window.cs_js_is_null(None)
arr = window.cs_js_array()
assert type(arr) is list
assert arr == [1, 2.5, None, [3]]
assert isinstance(arr[1], float)
assert isinstance(arr[3], list)
d = dict(window.cs_js_obj)
assert isinstance(d['keys'], list)
assert list(d['keys']) == ['a', 'b']
assert window.cs_js_obj.n is None

# a Python list that goes to Javascript and comes back is the same list
window.eval("window.cs_identity = function(x){ return x }")
t = [1, 2]
assert window.cs_identity(t) is t

# isinstance(str, object)
assert isinstance('a', object)
assert not isinstance('a', int)

# bool repr is translated in the language of cmu_graphics
saved = getattr(__BRYTHON__, 'cmuGraphicsLanguage', None)
__BRYTHON__.cmuGraphicsLanguage = 'es'
assert repr(True) == 'Verdadero'
__BRYTHON__.cmuGraphicsLanguage = 'en'
assert repr(True) == 'True'
__BRYTHON__.cmuGraphicsLanguage = saved

# lockdown: imports of browser and of the "window" in cmu_graphics, and
# eval of __import__, are not allowed
__BRYTHON__.lockdown = True
try:
    assert_raises(ModuleNotFoundError, exec, 'import browser')
    assert_raises(Exception, eval, "__import__('browser')")
finally:
    __BRYTHON__.lockdown = False

# time.sleep is not allowed
import time
assert_raises(Exception, time.sleep, 1)

# python_to_js output can be run in another Brython instance, where the
# module has not been registered
js = __BRYTHON__.python_to_js('y = 2 + 3', 'cs_academy_test_module')
for key in list(window.Object.keys(__BRYTHON__.imported)):
    if key.startswith('$python_to_js'):
        __BRYTHON__.imported[key] = javascript.UNDEFINED
ns = window.eval(js)
assert ns.y == 5

# each program compiled by python_to_js has its own namespace, even if the
# script ids are the same
js1 = __BRYTHON__.python_to_js('z1 = 1', 'cs_academy_same_id')
js2 = __BRYTHON__.python_to_js("ok = 'z1' not in globals()", 'cs_academy_same_id')
window.eval(js1)
assert window.eval(js2).ok

# a Javascript function exported by a Python module and imported with
# "from module import *" still converts its arguments (upstream unwraps it,
# cf. issue 2395)
ns = {}
exec('from cs_academy_reexport import *\nresult = js_add(1.5, 2.25)\npy = py_func()', ns)
assert ns['result'] == 3.75, ns['result']
assert ns['py'] == 'py'
from cs_academy_reexport import js_add
assert js_add(0.5, 0.25) == 0.75

# deleting a name from globals() (done by setupMvc in cmu_graphics)
src = """
x = 1
y = 2
def f():
    return x
del globals()['x']
assert 'x' not in globals()
assert 'y' in globals()
assert [k for k in globals() if k in ('x', 'y')] == ['y']
assert 'x' not in dict(globals().items())
try:
    f()
    raise AssertionError('should have raised NameError')
except NameError:
    pass
x = 2
x = 3
assert f() == 3
assert 'x' in globals()
"""
exec(src, {})
window.eval(__BRYTHON__.python_to_js(src, 'cs_academy_del_globals'))

# keyword arguments passed to a Javascript function are received as the
# Brython object {$kw: [...]} (used by drawRect() etc. in cmu-graphics.js)
window.eval("""window.cs_make_draw = function(){
    return function(){
        var args = Array.from(arguments), kw = {}
        var last = args[args.length - 1]
        if(last && last.$kw){
            kw = args.pop().$kw[0]
        }
        return args.length + ':' + Object.keys(kw).join(',')
    }
}""")
draw = window.cs_make_draw()
assert draw(1, 2.5, fill='red', border=None) == '2:fill,border'
assert draw(1) == '1:'

# a Javascript function returned by a Javascript function call receives the
# Brython objects, not converted (cmu-graphics.js: jsSetWithTypeCheckBry()...)
window.eval("""window.cs_make_checker = function(){
    return function(value){
        return value === __BRYTHON__.builtins.None ? 'None' : typeof value
    }
}""")
checker = window.cs_make_checker()
assert checker(None) == 'None'
assert checker(1.5) == 'object'  # a Brython float

# traceback.format_exc() for a NameError in code run by exec() with globals
# that have no __builtins__ (student programs in cmu_graphics)
import traceback
g = {}
exec("""
import traceback
try:
    undefined_name
except NameError:
    tb = traceback.format_exc()
""", g)
assert "NameError: name 'undefined_name' is not defined" in g['tb'], g['tb']
ns = {'__name__': '__main__'}
ns2 = dict(ns)
exec("def f():\n    return undefined_name2\n", ns2)
try:
    ns2['f']()
except NameError:
    assert 'undefined_name2' in traceback.format_exc()

print('passed all tests...')
