#!/bin/bash

if [ -d "env" ]; then
	rm -rf env
fi
virtualenv env

source env/bin/activate
pip install -r requirements.txt
