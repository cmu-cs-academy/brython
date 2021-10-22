set -xe

DEST=../cs-academy/frontend/src/brython
LIB_DEST="$DEST/../../public/"

(cd scripts && pipenv run python3.10 make_dist.py)

rm -rf "$DEST"
mkdir "$DEST"
cp -r www/src/brython.js www/src/brython_stdlib.js setup "$DEST"
cp -r www/src/builtins_docstrings.js www/src/libs www/src/Lib "$LIB_DEST"

git log -n 1 --pretty=format:"%H" > $DEST/git-sha.txt

# Remove files that we don't need
rm -rf "$DEST/setup/data" "$LIB_DEST/Lib/test" "$DEST/setup/changelog.txt" "$DEST/setup/README.rst" \
  "$LIB_DEST/Lib/.bundle-ignore" "$LIB_DEST/Lib/email/architecture.rst" \
  "$LIB_DEST/Lib/importlib" "$LIB_DEST/Lib/pkgutil.py" "$LIB_DEST/Lib/imp.py" "$LIB_DEST/Lib/_imp.py" \
  "$LIB_DEST/Lib/_frozen_importlib.py" "$LIB_DEST/Lib/site-packages/foobar"
