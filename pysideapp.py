import sys
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtSerialPort import *
from ui_mainwindow import Ui_mainWindow
from itertools import count, islice


class OtherThread(QObject):
    result = pyqtSignal(int)

    def __init__(self, parent=None, **kwargs):
        super().__init__(parent, **kwargs)

    @pyqtSlot()
    def start(self): print("Thread started")

    @pyqtSlot(int)
    def main_thread_function(self, n):
        """main thread function"""
        primes = (n for n in count(2) if all(n % d for d in range(2, n)))
        self.result.emit(list(islice(primes, 0, n))[-1])

class SerialThread(QObject):
    result = pyqtSignal()
    def __init__(self, parent=None, **kwargs):
        super().__init__(parent, **kwargs)


    @pyqtSlot()
    def start(self): print("Thread started")

    @pyqtSlot(str)
    def main_thread_function(self, port):
        """main thread function"""
        self.serial = QSerialPort(self)
        self.serial.setPortName(port)
        self.serial.open(QIODevice.ReadWrite)
        self.serial.setBaudRate(38400)

        print('connected')


        self.result.emit()


class MainWindow(QMainWindow, Ui_mainWindow):
    request_signal = pyqtSignal(str)

    def __init__(self, parent=None, **kwargs):
        super(MainWindow, self).__init__(parent, **kwargs)
        QMainWindow.__init__(self)
        Ui_mainWindow.__init__(self)
        self.setupUi(self)

        # Thread Management
        self.thread = QThread()
        self.serial_connection = SerialThread(result=self.display)
        self.request_signal.connect(self.serial_connection.main_thread_function)
        self.thread.started.connect(self.serial_connection.start)
        self.serial_connection.moveToThread(self.thread)
        qApp.aboutToQuit.connect(self.thread.quit)
        self.thread.start()

        # UI initial values
        self.serial_port_path, self.serial_port_name = self.get_port()
        self.serial_port_QLineEdit.setText(self.serial_port_path)

        self.connect_pushButton.clicked.connect(self.start_thread)

    def get_port(self):
        availablePorts = QSerialPortInfo.availablePorts()
        port = [(availablePorts[i].systemLocation(), availablePorts[i].portName()) for i in range(len(availablePorts)) if "Arduino" in availablePorts[i].description()][0]
        port_path, port_name = port
        return port_path, port_name

    @pyqtSlot()
    def start_thread(self):
        """called when a button is clicked"""
        try:
            port = self.serial_port_name
        except:
            return
        self.request_signal.emit(port)

    @pyqtSlot()
    def display(self):
        """called when thread returns"""
        pass


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())