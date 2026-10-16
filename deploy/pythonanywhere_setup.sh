#!/bin/bash
# Run in a PythonAnywhere Bash console:   bash deploy/pythonanywhere_setup.sh
# (first: git clone https://github.com/Abdullahshahid984/internmatch.git && cd internmatch)
set -e
cd "$(dirname "$0")/.."
python3 -m venv ~/.venv-im
source ~/.venv-im/bin/activate
pip install --quiet -r requirements.txt
echo
echo "Done. Your secret key (copy it into the WSGI file as SECRET_KEY):"
python -c "import secrets; print(secrets.token_hex(32))"
echo
echo "Project folder : $(pwd)"
echo "Virtualenv     : $HOME/.venv-im"
echo "Next: Web tab -> Add a new web app -> Manual configuration, then follow docs/DEPLOYMENT.md step 5 onwards."
