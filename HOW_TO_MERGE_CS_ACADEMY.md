```
git fetch --all

git checkout -b next
git merge brython-dev/master
```

Then resolve merge conflicts:


Delete these files:

* www/src/brython.js
* www/src/brython_stdlib.js
* www/src/stdlib_paths.js
* www/src/version_info.js


Run tests:

* run before_script lines from .travis.yml (using python3.8)
* run `./node_modules/.bin/testem -t www/tests/qunit/run_tests.html`, then open link it prints on browser of your choice


In cs-academy:

* Checkout a new branch off of master

Back in brython:

* Run `./copy_to_af.sh`

In cs-academy:

* Eyeball the changes that were made, especially new files that were added.
* Run "Build CMU Graphics" in the gui window
* Run "Test Animation Framework" in the Tests tab of gui window


