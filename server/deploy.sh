#!/bin/bash

set -ev

sudo su - main <<EOF
set -ev
source /home/main/experiment/venv/bin/activate
cd /home/main/experiment/tarification-solidaire-strasbourg/server
git pull
make install
make build
EOF

sudo systemctl restart plugin_python
sleep 2
sudo systemctl status plugin_python
