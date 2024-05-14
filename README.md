# rsp_air
Just having fun with RaspberryPi and ENS160

## INSTALL
After git clone install requirements

``pip install -r ./requirements.txt``

## RUN

``main.py``is the file to run.

To start it just after the boot add this line in **crontab**
``@reboot	nohup bash -c 'python /absolute/project/path/main.py' &``
