#!/bin/sh
export FLASK_APP=./GrantBridge/Api.py
pipenv run flask --debug run -h 0.0.0.0