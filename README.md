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