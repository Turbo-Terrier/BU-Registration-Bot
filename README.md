## Installation

### Prerequisites

* Python3
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

`pyarmor gen --enable-jit --assert-call --assert-import --restrict --platform windows.x86_64 --platform linux.x86_64 --platform linux.aarch64 --platform linux.armv7 --platform darwin.x86_64 -O obfdist --pack dist/main.exe ./`
