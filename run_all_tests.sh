#!/usr/bin/env bash

echo \#\#\# run: ./gradleInit.py --version
./gradleInit.py --version
for test in test_*.py
do
    echo \#\#\# run: $test
    ./$test
done