(cd scripts && python3.10 make_doc.py)
(cd scripts && python3.10 make_dist.py)
npx testem -t www/tests/qunit/run_tests.html
