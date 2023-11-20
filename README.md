## Installation

### Prerequisites

* A support version of Python3:
  * Python 3.7
  * Python 3.8
  * Python 3.9
  * Python 3.10
  * Python 3.11
* Google Chrome

### Installation Steps

The basic steps for installation are as follows. Please note, on some systems, additional configuration may be needed.

#### Windows
`cd Drive:\path\to\folder`

`py -m venv env`

`.\env\Scripts\activate`

`pip3 install -r .\requirements.txt`

#### Linux
`cd /path/to/folder`

`python3 -m venv env`

`source env/bin/activate`

`pip3 install -r ./requirements.txt`

### Usage

```pyinstaller -F main.py```

`pyarmor gen --enable-jit --assert-call --assert-import --restrict --platform windows.x86_64 --platform linux.x86_64 --platform linux.aarch64 --platform linux.armv7 --platform darwin.x86_64 main.py ./`
python3.7 -m pyarmor.cli gen --enable-jit --assert-call --assert-import --restrict --platform windows.x86_64 --platform linux.x86_64 --platform linux.aarch64 --platform linux.armv7 --platform darwin.x86_64 -O py3.7-dist main.py ./core
python3.8 -m pyarmor.cli gen --enable-jit --assert-call --assert-import --restrict --platform windows.x86_64 --platform linux.x86_64 --platform linux.aarch64 --platform linux.armv7 --platform darwin.x86_64 -O py3.8-dist main.py ./core
python3.9 -m pyarmor.cli gen --enable-jit --assert-call --assert-import --restrict --platform windows.x86_64 --platform linux.x86_64 --platform linux.aarch64 --platform linux.armv7 --platform darwin.x86_64 -O py3.9-dist main.py ./core
python3.10 -m pyarmor.cli gen --enable-jit --assert-call --assert-import --restrict --platform windows.x86_64 --platform linux.x86_64 --platform linux.aarch64 --platform linux.armv7 --platform darwin.x86_64 -O py3.10-dist main.py ./core
python3.11 -m pyarmor.cli gen --enable-jit --assert-call --assert-import --restrict --platform windows.x86_64 --platform linux.x86_64 --platform linux.aarch64 --platform linux.armv7 --platform darwin.x86_64 -O py3.11-dist main.py ./core

python3.11 -m pyarmor.cli.merge -O dist py3.7-dist py3.8-dist py3.9-dist 
