```
git fetch --all

git checkout -b next
git merge brython-dev/master
```

Then resolve merge conflicts:


Delete these files:

* www/src/brython.js
* www/src/brython_standard_parser.js
* www/src/brython_stdlib.js
* www/src/stdlib_paths.js
* www/src/version_info.js


Run tests:

* run before_script lines from .travis.yml
* run `npx testem -t www/tests/run_tests.html`, then open link it prints on browser of your choice


In cs-academy:

* Checkout a new branch off of master

Back in brython:

* Run `./copy_to_af.sh`

In cs-academy:

* Eyeball the changes that were made, especially new files that were added.
* Consider running `git diff -G 'import' HEAD -- . :^frontend/src/brython/brython.js :^frontend/src/brython/brython_stdlib.js :^frontend/src/cmu-graphics-brython.js` to specifically check for added imports.
* Add any modules that are needed to load cmu_graphics to the list in buildCmuGraphics in build.py. If a module is missing here, it will cause py2js to fail to load when the content build is running. If py2js fails to load (you'll see an error in the content build), you can uncomment `chrome_options.add_argument("--headless")` in py2js.py so that you can see what caused it to fail to load.
* Run "python build.py cmu-graphics" from the cs-academy folder
* Run "Test Animation Framework" in the Tests tab of gui window
