# step 1: make env
python -m venv env
source env/bin/activate
pip install -r requirements.txt
# step 2: create database
comment http part in main.py file
uncomment database part in main.py file
and run main.py
# step 3: run http server
uncomment http part in main.py file
comment database part in main.py file
and run main.py
# step 4: test API
use postman to test API: