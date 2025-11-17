#!/usr/bin/env bash

for test in test_*.py
do
    echo \#\#\# run: $test
    ./$test
done
