#!/bin/bash
#This script creates a python venv and installs all the dependencies in order for the host to run wsgi.py
#Run it by typing source venv.sh

cd
python3 -m venv wsgi-tester
. wsgi-tester/bin/activate
pip install redis flask gunicorn