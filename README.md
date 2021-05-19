# Ispectro
Opensource software for an Impedance Spectroscopy (BIS) Device based on Arduino.

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