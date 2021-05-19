# Ispectro
Open-source software for an Impedance Spectroscopy (BIS) Device based on Arduino.

To in a venv install:
```
pip install -r requirements.txt 
```

To run:
```
python main.py
```

Qt5 Designer file:
```
ispectro_xml.ui
```

Persistent Settings:
```
config.ini
```

Generate pyQt5 Ui_MainWindow and QtBaseClass classes for python
```
pyuic5 -x ispectro_xml.ui -o ispectro_xml.py
```

Arduino Code for BIS Device
```
firmware.ino
```

KiCad Schematics for Device:
```
impedance_777/impedance_777_r1.pro
```


![alt text](https://github.com/andrewallison2012/ispectro/blob/master/main_screen.png?raw=true)
![alt text](https://github.com/andrewallison2012/ispectro/blob/master/cole_screen.png?raw=true)


> Software and firmware for an Impedance Spectroscopy (BIS) Device based on ATMEGA2560 (Arduino) and AD5933
>
> Copyright (C) 2021  Andrew Allison
>
> This program is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
>
> This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License for more details.
>
> You should have received a copy of the GNU Affero General Public License along with this program.  If not, see <http://www.gnu.org/licenses/>.



[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)