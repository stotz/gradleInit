#!/usr/bin/env bash

echo \#\#\# run: ./gradleInit.py --version
./gradleInit.py --version
for test in test_*.py
do
    echo \#\#\# run: $test
    ./$test
done

version=$(./gradleInit.py -v | sed 's/gradleInit v/0/;s/\./0/g')
echo \#\#\# run: gradleInit init --interactive with app: myDemoApp$version
gradleInit init --interactive  <<EOF
myDemoApp$version
2

0.0.3
3
8.14.2
2025-11-18
21
EOF

cd myDemoApp$version || exit 1
./gradlew clean build test run
cd ..
rm -rf myDemoApp$version
