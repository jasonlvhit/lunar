#!/bin/sh
#python3 -m unittest discover tests
cd tests
python -m unittest discover
#py.test --cov-report term-missing tests --cov lunar
