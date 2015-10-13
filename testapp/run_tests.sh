#!/bin/bash

if [ ! -d "env" ]; then
	./init.sh
fi

source env/bin/activate
./manage.py test
