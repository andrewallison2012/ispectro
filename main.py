

import sys
import io
from PyQt5 import uic
import numpy as np
import pyqtgraph as pg
import datetime as dt
import queue as Queue
import serial
from PyQt5.QtCore import pyqtSignal
import pandas as pd
from PyQt5 import QtCore, QtWidgets
import configparser
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
sys.path.append(".")
import cole_model as cm
import time
import traceback, sys

config = configparser.ConfigParser()
config.read("config.ini")
serial_settings = config['SERIAL_SETTINGS']
data_path = config['DATA_PATH']
device_settings = config['DEVICE_SETTINGS']

config = configparser.ConfigParser()

port_name = str(serial_settings['port_name'])
baud_rate = int(serial_settings['baud_rate'])

qtcreator_file = "ispectro_xml.ui"  # Enter file here, this is generated with qt creator or desinger
Ui_MainWindow, QtBaseClass = uic.loadUiType(qtcreator_file)
pg.setConfigOptions(antialias=True)

class WorkerSignals(QObject):
    '''
    Defines the signals available from a running worker thread.

    Supported signals are:

    finished
        No data

    error
        tuple (exctype, value, traceback.format_exc() )

    result
        object data returned from processing, anything

    progress
        int indicating % progress

    '''
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)
    progress = pyqtSignal(int)


class Worker(QRunnable):
    '''
    Worker thread

    Inherits from QRunnable to handler worker thread setup, signals and wrap-up.

    :param callback: The function callback to run on this worker thread. Supplied args and
                     kwargs will be passed through to the runner.
    :type callback: function
    :param args: Arguments to pass to the callback function
    :param kwargs: Keywords to pass to the callback function

    '''

    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()

        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

        # Add the callback to our kwargs
        self.kwargs['progress_callback'] = self.signals.progress

    @pyqtSlot()
    def run(self):
        '''
        Initialise the runner function with passed args, kwargs.
        '''

        # Retrieve args/kwargs here; and fire processing using them
        try:
            result = self.fn(*self.args, **self.kwargs)
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)  # Return the result of the processing
        finally:
            self.signals.finished.emit()  # Done


class SerialThread(QtCore.QThread):
    my_signal = pyqtSignal()
    my_connection_success = pyqtSignal()
    my_connection_failure = pyqtSignal()
    my_connection_ended = pyqtSignal()
    data_set_signal = pyqtSignal()
    my_general_signal = pyqtSignal()

    def __init__(self, port_name, buad_rate):
        QtCore.QThread.__init__(self)
        np.set_printoptions(formatter={'float': lambda x: "{0:0.1f}".format(x)})
        self.port_name = port_name
        self.buad_rate = buad_rate
        self.transmit = Queue.Queue()
        self.serial_running = True
        self.np_data = np.array([0, 1, 2, 3, 4, 5, 6, 7, 8])
        self.data_set = np.array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9])
        self.calibration_resistor = 100
        self.calibration_resistor_2 = 100
        self.selected_rfb = 1
        self.my_general_signal.emit()

    def write_data(self, data_string):
        data = data_string.encode('utf-8')
        self.serial_connection.write(data)

    def find_angle(self, real, imaginary):
        pi = np.pi
        phase = 0
        theta = 0

        # phase calibration with arctangent function accounting for changes in quadrant
        if real != 0 and imaginary != 0:
            # positive and positive
            if real > 0 and imaginary > 0:  # 1st, per page 21 in AD5933 data sheet
                theta = np.arctan(imaginary / real)
                phase = (theta * 180) / pi
            # negative and positive
            if real < 0 and imaginary > 0:  # 2nd, per page 21 in AD5933 data sheet
                theta = pi + np.arctan(imaginary / real)
                phase = (theta * 180) / pi
            # negative and negative
            if real < 0 and imaginary < 0:  # 3rd, per page 21 in AD5933 data sheet
                theta = pi + np.arctan(imaginary / real)
                phase = (theta * 180) / pi
            # positive and negative
            if real > 0 and imaginary < 0:  # 4th, per page 21 in AD5933 data sheet
                theta = (2 * pi) + np.arctan(imaginary / real)
                phase = (theta * 180) / pi

        # handle arctan function if 'real' aka 'x' component is zero
        if real == 0:
            if real == 0 and imaginary > 0:  # 1st, per page 21 in AD5933 data sheet
                theta = pi / 2
                phase = (theta * 180) / pi
                print('1 and 2')
            if real == 0 and imaginary < 0:  # 4th, per page 21 in AD5933 data sheet
                theta = (3 * pi) / 2
                phase = (theta * 180) / pi
                print('3 and 4')

        # handle arctan function if 'imaginary' aka 'y' component is zero
        if imaginary == 0:
            if real > 0 and imaginary == 0:  # 1st, per page 21 in AD5933 data sheet
                theta = 0
                phase = (theta * 180) / pi
                print('1 and 4')
            if real < 0 and imaginary == 0:  # 4th, per page 21 in AD5933 data sheet
                theta = pi
                phase = (theta * 180) / pi
                print('2 and 3')
        return theta

    def set_calibration(self, value):
        self.calibration_resistor = value

    def set_calibration_2(self, value):
        self.calibration_resistor_2 = value

    def sef_rfb(self, value):
        if value == 0:
            rfb = 0
        elif value == 1:
            rfb = 20000
        elif value == 2:
            rfb = 200
        elif value == 3:
            rfb = 300
        elif value == 4:
            rfb = 430
        elif value == 5:
            rfb = 510
        elif value == 6:
            rfb = 620
        elif value == 7:
            rfb = 700
        elif value == 8:
            rfb = 1000
        else:
            rfb = 1
        self.selected_rfb = rfb

    def impedance(self,real_output,imaginary_output):
        R_z = real_output
        X_z = imaginary_output
        Z = np.sqrt((real_output ** 2) + (imaginary_output ** 2))
        Y = 1/Z
        return Z,Y,R_z,X_z

    def calibration(self,calibration_measurement, rfb, calibration_resistor, measurement_magnitude_Z, measurement_magnitude_Y):
        M = 1/calibration_measurement
        R_fb = rfb
        Z_calibration = calibration_resistor
        Y_standard = 1 / Z_calibration
        C = M / (R_fb * Y_standard)
        Z = (C * R_fb) / measurement_magnitude_Z
        Y = (C * R_fb * measurement_magnitude_Y)
        return C,Z,Y

    def data_processing(self, frequency, real_unknown, imaginary_unknown, real_cal, imaginary_cal, real_cal2, imaginary_cal2, temperature, status):
        Z_unkown, Y_unkown, real_unknown, imaginary_unknown = self.impedance(real_unknown,imaginary_unknown)
        Z_cal, Y_cal, real_cal, imaginary_cal = self.impedance(real_cal, imaginary_cal)
        Z_cal2, Y_cal2, real_cal2, imaginary_cal2 = self.impedance(real_cal2, imaginary_cal2)

        calibration_phase = (self.find_angle(real_cal, imaginary_cal) + self.find_angle(real_cal2, imaginary_cal2)) / 2
        unknown_raw_phase = self.find_angle(real_unknown, imaginary_unknown)
        unknown_calibrated_phase = calibration_phase - unknown_raw_phase
        theta = unknown_calibrated_phase

        C_1,Z_1,Y_1 = self.calibration(Y_cal, self.selected_rfb, self.calibration_resistor, Z_unkown, Y_unkown)
        C_2,Z_2,Y_2 = self.calibration(Y_cal, self.selected_rfb, self.calibration_resistor, Z_unkown, Y_unkown)

        Z = (Z_1 + Z_2) / 2
        Y = (Y_1 + Y_2) / 2
        C = (C_1 + C_2) / 2

        theta_degrees = theta * 180/np.pi
        gain_factor = C
        impedance = Z
        z_real = impedance * np.cos(theta)
        z_imaginary = impedance * np.sin(theta)

        self.data_set = np.vstack((self.data_set, np.array([frequency, impedance, z_real, z_imaginary, real_cal2, imaginary_cal2, theta_degrees, gain_factor, temperature, status])))
        self.data_set_signal.emit()
        return self.data_set

    def end_serial_connection(self):
        self.serial_connection.close()
        self.serial_connection = None
        self.my_connection_ended.emit()

    def run(self):
        self.np_data = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9])
        try:
            self.serial_connection = serial.Serial(self.port_name, self.buad_rate, timeout=3)
            self.my_connection_success.emit()
            self.serial_running = True
        except:
            # self.serial_running = True
            self.serial_connection = None
        if not self.serial_connection:
            print('could not open port')
            self.my_connection_failure.emit()
            self.serial_running = False

        while self.serial_running:
            self.raw_data = bytearray(9 * 4)
            self.serial_connection.readinto(self.raw_data)
            line = np.frombuffer(bytes(self.raw_data), dtype='<f4')
            last_line = self.np_data[-1]
            if (np.array_equal(last_line, line) == False) and (line[8] == 1.0):
                self.np_data = np.vstack((self.np_data, line))
                self.data_processing(frequency=line[0], real_unknown=line[1], imaginary_unknown=line[2], real_cal=line[3], imaginary_cal=line[4], real_cal2=line[5], imaginary_cal2=line[6], temperature=line[7], status=line[8])
                self.my_signal.emit()

        if self.serial_connection:
            self.serial_connection.close()
            print('self.serial_connection.close()')
            self.serial_connection = False


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        QtWidgets.QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)

        self.setupUi(self)
        self.threadpool = QThreadPool()
        self.connect()

        self.all_runs = np.array([[0, 1, 2, 3, 4, 5, 6, 7, 8]])

        self.current_sweep = 1
        self.percent_complete = 0
        self.total_colors_fixed_frequency_scale = 160000
        self.sweep_count = self.sweep_count_spinBox.value()
        self.total_steps = self.number_of_steps_spinBox_4.value()
        self.subject_id_lineEdit.setText(f"{data_path['custom']}")
        self.lineEdit_data_file_name.setText(f"no data file")

        self.raw_frequency = 0
        self.raw_real_unknown = 0
        self.raw_imaginary_unknown = 0
        self.raw_real_cal = 0
        self.raw_imaginary_cal = 0
        self.raw_real_cal2 = 0
        self.raw_imaginary_cal2 = 0
        self.raw_temp = 0
        self.raw_status = 0

        self.frequency = 0
        self.impedance = 0
        self.z_real = 0
        self.z_imaginary = 0
        self.real_cal2 = 0
        self.imaginary_cal2 = 0
        self.theta = 0
        self.gain_factor = 0
        self.temperature = 0
        self.status = 0

        self.start_frequency = self.start_freq_spinBox.value()
        self.step_size = self.step_size_spinBox.value()
        self.step_count = self.number_of_steps_spinBox_4.value()
        self.sweep_range = (self.step_size * self.step_count) - self.step_size
        self.end_frequency = self.start_frequency + self.sweep_range

        # temp_graphicsView
        self.temp_graphicsView.setBackground('w')
        self.temp_graphicsView.setDownsampling(mode='peak')
        self.temp_graphicsView.setClipToView(True)
        self.temp_graphicsView.showGrid(x=True, y=True)
        # self.temp_graphicsView.hideAxis('bottom')
        self.temp_graphicsView.setLabel('left', text='Temp (C)')
        self.temp_graphicsView.setLabel('bottom', text='Frequency (kHz)')

        # plot1_graphicsView
        self.plot1_graphicsView.setBackground('w')
        self.plot1_graphicsView.setDownsampling(mode='peak')
        self.plot1_graphicsView.setClipToView(True)
        self.plot1_graphicsView.showGrid(x=True, y=True)
        self.plot1_graphicsView.setTitle(title="Z impedance")
        self.plot1_graphicsView.setLabel('left', text='X reactance (ohms)')
        self.plot1_graphicsView.setLabel('bottom', text='R resistance (ohms)')
        self.plot2_graphicsView.setBackground('w')
        self.plot2_graphicsView.setTitle(title="Raw Data")
        self.plot2_graphicsView.showGrid(x=True, y=True)
        self.plot2_graphicsView.setLabel('left', text='Value')
        self.plot2_graphicsView.setLabel('bottom', text='Frequency (Hz)')
        self.input_plot.setBackground('w')
        self.input_plot.hideAxis('bottom')
        self.pw = self.input_plot
        self.p1 = self.pw.plotItem
        self.p1.setLabels(left='Excitation (V)')
        self.p2 = pg.ViewBox()
        self.p1.showAxis('right')
        self.p1.scene().addItem(self.p2)
        self.p1.getAxis('right').linkToView(self.p2)
        self.p2.setXLink(self.p1)
        self.p1.getAxis('right').setLabel('Response (I)', color='#ff0000')
        self.raw_plot.setBackground('w')
        self.raw_plot.setTitle(title="Impedance")
        self.raw_plot.showGrid(x=True, y=True)
        self.raw_plot.setLabel('left', text='Z Magnitude')
        self.raw_plot.setLabel('bottom', text='Frequency (kHz)')
        self.raw_plot.addLegend()

        self.start_QPushButton.clicked.connect(self.start_sweep)
        self.stop_QPushButton.clicked.connect(self.stop_sweep)
        self.connect_pushButton.clicked.connect(self.connect)
        self.disconnect_pushButton.clicked.connect(self.disconnect)
        self.save_data_button.clicked.connect(self.save_data)
        self.command_line.returnPressed.connect(self.issue_command)
        self.measure_1_comboBox_1.setCurrentIndex(int(device_settings['measure_1_comboBox_1']))
        self.measure_2_comboBox_1.setCurrentIndex(int(device_settings['measure_2_comboBox_1']))
        self.measure_3_comboBox_1.setCurrentIndex(int(device_settings['measure_3_comboBox_1']))
        self.gain_resistor_comboBox.setCurrentIndex(int(device_settings['ADG1608_GAIN']))
        self.fbr_comboBox.setCurrentIndex(int(device_settings['ADG1608_RFB']))
        self.number_of_steps_spinBox_4.setProperty("value", float(device_settings['number_of_steps']))
        self.step_size_spinBox.setProperty("value", int(device_settings['step_size']))
        self.settling_time_spinBox.setProperty("value", int(device_settings['SWEEP_DELAY']))
        self.pga_comboBox.setCurrentIndex(int(device_settings['PGA']))
        self.output_voltage_comboBox.setCurrentIndex(int(device_settings['VOLTAGE']))
        self.cal_resistor_doubleSpinBox.setProperty("value", float(device_settings['cal_resistor']))
        self.cal_resistor_doubleSpinBox_2.setProperty("value", float(device_settings['cal_resistor2']))
        self.start_freq_spinBox.setProperty("value", int(device_settings['START_FREQUENCY']))
        self.serial_port_QLineEdit.setText(str(serial_settings['port_name']))
        self.sweep_text()
        self.start_freq_spinBox.valueChanged['int'].connect(self.sweep_text)
        self.step_size_spinBox.valueChanged['int'].connect(self.sweep_text)
        self.number_of_steps_spinBox_4.valueChanged['int'].connect(self.sweep_text)
        self.settling_time_spinBox.valueChanged['int'].connect(self.sweep_text)
        self.start_QPushButton.setEnabled(False)
        self.start_QPushButton.show()
        self.stop_QPushButton.setEnabled(False)
        self.stop_QPushButton.hide()
        self.groupBox_2.setEnabled(False)

        self.max_frequency = (self.start_freq_spinBox.value() + (self.step_size_spinBox.value() * self.number_of_steps_spinBox_4.value()))
        self.current_frequency = self.start_freq_spinBox.value()
        self.current_step = ((self.start_freq_spinBox.value() - self.start_freq_spinBox.value()) / self.step_size_spinBox.value()) + 1
        self.percent_complete = (self.current_step / self.number_of_steps_spinBox_4.value()) * 100
        self.progressBar.setValue(int(self.percent_complete))
        self.current_color_fixed_frequency_scale = self.start_freq_spinBox.value()
        self.progressBar.setProperty("value", 0)

        # view
        self.view = self.plot1_graphicsView
        self.s3 = pg.ScatterPlotItem()
        self.view.addItem(self.s3)
        legend = pg.LegendItem((80, 60), offset=(0, 20))
        legend.setParentItem(self.view.graphicsItem())
        legend.addItem(self.s3, 'Meas. 1 Calibrated (Gain Factor and Phase)')

        # view2
        self.view2 = self.temp_graphicsView
        self.s2 = pg.ScatterPlotItem()
        self.view2.addItem(self.s2)

        # view3
        self.view3 = self.plot2_graphicsView
        self.sp1 = pg.ScatterPlotItem()
        self.sp2 = pg.ScatterPlotItem()
        self.sp3 = pg.ScatterPlotItem()
        self.sp4 = pg.ScatterPlotItem()
        self.sp5 = pg.ScatterPlotItem()
        self.sp6 = pg.ScatterPlotItem()
        self.view3.addItem(self.sp1)
        self.view3.addItem(self.sp2)
        self.view3.addItem(self.sp3)
        self.view3.addItem(self.sp4)
        self.view3.addItem(self.sp5)
        self.view3.addItem(self.sp6)
        legend = pg.LegendItem((80, 60), offset=(0, 20))
        legend.setParentItem(self.view3.graphicsItem())
        legend.addItem(self.sp1, 'Meas. 1 R')
        legend.addItem(self.sp2, 'Meas. 1 X')
        legend.addItem(self.sp3, 'Meas. 2 R')
        legend.addItem(self.sp4, 'Meas. 2 X')
        legend.addItem(self.sp5, 'Meas. 3 R')
        legend.addItem(self.sp6, 'Meas. 3 X')

        # view4
        self.view4 = self.raw_plot
        self.s4 = pg.PlotCurveItem()
        self.s5 = pg.PlotCurveItem()
        self.s6 = pg.PlotCurveItem()
        self.view4.addItem(self.s4)
        self.view4.addItem(self.s5)
        self.view4.addItem(self.s6)
        self.s4.setData(size=5, pen=(255, 0, 0))
        self.s5.setData(size=5, pen=(0, 255, 0))
        self.s6.setData(size=5, pen=(0, 0, 255))
        legend = pg.LegendItem((80, 60), offset=(0, 20))
        legend.setParentItem(self.view4.graphicsItem())
        legend.addItem(self.s4, 'Meas. 1 Unk')
        legend.addItem(self.s5, 'Meas. 2 Cal1')
        legend.addItem(self.s6, 'Meas. 3 Cal2')

        # self.cycles_per_nano_second = ((self.start_freq_spinBox.value()) / 1000)
        # self.cycles_per_nano_second_radians = self.cycles_per_nano_second * np.pi * 2
        # self.linspace_data = np.linspace(0, self.cycles_per_nano_second_radians, 100000)
        # self.sin_data = np.sin(self.linspace_data)
        # # response signal
        # self.cycles_per_nano_second_output = ((self.start_freq_spinBox.value()) / 1000)
        # self.cycles_per_nano_second_radians_output = self.cycles_per_nano_second_output * np.pi * 2
        # self.linspace_data_output = np.linspace(0, self.cycles_per_nano_second_radians_output, 100000)
        # self.sin_data_output = np.sin(self.linspace_data_output + 0) / 1


        print("Multithreading with maximum %d threads" % self.threadpool.maxThreadCount())
        # self.pushButton_new.pressed.connect(self.oh_no)

        self.serial_thread.my_signal.connect(lambda: self.np_data_updater())
        self.serial_thread.my_signal.connect(lambda: self.view_and_view2_thread())
        self.serial_thread.my_signal.connect(lambda: self.view3_thread())
        self.serial_thread.my_signal.connect(lambda: self.view4_thread())
        self.clear_all_data.clicked.connect(self.clear_plots)
        self.cole_model_button.clicked.connect(self.regression)

    def regression(self):
        try:
            self.ColeModel= cm.generate_regression(self.csv_file_path)
            self.ColeModel.start()
        except:
            self.update_status('press save or enter a valid csv file with z_real and z_imaginary as headers')


    def progress_fn(self, n):
        print("%d%% done" % n)

    def execute_this_fn(self, progress_callback):
        for n in range(0, 5):
            time.sleep(1)
            progress_callback.emit(n * 100 / 4)

        return "Done."

    def print_output(self, s):
        print(s)

    def thread_complete(self):
        pass
        # print("THREAD COMPLETE!")

    def oh_no(self):
        # Pass the function to execute
        worker = Worker(self.execute_this_fn)  # Any other args, kwargs are passed to the run function
        # worker.signals.result.connect(self.print_output)
        # worker.signals.finished.connect(self.thread_complete)
        worker.signals.progress.connect(self.progress_fn)
        # Execute
        self.threadpool.start(worker)

    def clear_all_multi(self):
        worker = Worker(self.clear_plots)
        worker.signals.progress.connect(self.progress_fn)
        self.threadpool.start(worker)

    # def sin_graph_thread(self):
    #     # Pass the function to execute
    #     worker = Worker(self.generate_sin_graph)  # Any other args, kwargs are passed to the run function
    #     worker.signals.result.connect(self.updateViews)
    #     worker.signals.finished.connect(self.thread_complete)
    #     worker.signals.progress.connect(self.progress_fn)
    #     # Execute
    #     self.threadpool.start(worker)

    def np_data_updater(self):
        # Pass the function to execute
        worker = Worker(self.set_current_data)  # Any other args, kwargs are passed to the run function
        worker.signals.result.connect(self.update_status)
        worker.signals.progress.connect(self.progress_fn)
        self.threadpool.start(worker)

    def view_and_view2_thread(self):
        # Pass the function to execute
        worker = Worker(self.update_view_and_view2)  # Any other args, kwargs are passed to the run function
        worker.signals.progress.connect(self.progress_fn)
        self.threadpool.start(worker)

    def view3_thread(self):
        worker = Worker(self.update_view3)  # Any other args, kwargs are passed to the run function
        worker.signals.progress.connect(self.progress_fn)
        self.threadpool.start(worker)

    def view4_thread(self):
        worker = Worker(self.update_view4)  # Any other args, kwargs are passed to the run function
        worker.signals.progress.connect(self.progress_fn)
        self.threadpool.start(worker)

    def recurring_timer(self):
        self.counter += 1
        self.l.setText("Counter: %d" % self.counter)

###############################
###############################
    # def generate_sin_graph(self, progress_callback):
    #     # exciation signal
    #     self.cycles_per_nano_second = ((self.serial_thread.np_data[-1:, 0]) / 10000)
    #     self.cycles_per_nano_second_radians = self.cycles_per_nano_second * np.pi * 2
    #     self.linspace_data = np.linspace(0, self.cycles_per_nano_second_radians, 100000)
    #     self.sin_data = np.sin(self.linspace_data)
    #     # response signal
    #     self.cycles_per_nano_second_output = ((self.serial_thread.np_data[-1:, 0]) / 10000)
    #     self.cycles_per_nano_second_radians_output = self.cycles_per_nano_second_output * np.pi * 2
    #     self.linspace_data_output = np.linspace(0, self.cycles_per_nano_second_radians_output, 100000)
    #     self.sin_data_output = np.sin(self.linspace_data_output + self.serial_thread.data_set[-1:, 6]) / self.serial_thread.data_set[-1:, 1]
    #
    #     self.updateViews()
    #     self.p1.vb.sigResized.connect(self.updateViews)
    #     return "Done."
    #
    # ## Handle view resizing
    # def updateViews(self):
    #     self.p1.clear()
    #     self.p2.clear()
    #     ## view has resized; update auxiliary views to match
    #
    #     self.p2.setGeometry(self.p1.vb.sceneBoundingRect())
    #     ## need to re-update linked axes since this was called
    #     ## incorrectly while views had different shapes.
    #     ## (probably this should be handled in ViewBox.resizeEvent)
    #     self.p2.linkedViewChanged(self.p1.vb, self.p2.XAxis)
    #     self.p1.plot(self.sin_data.flatten(), pen=(0, 0, 0))
    #     self.p2.addItem(pg.PlotCurveItem(self.sin_data_output.flatten(), pen=(255, 0, 0)))

    def sweep_text(self):
        self.start_frequency = self.start_freq_spinBox.value() / 1000
        self.step_size = self.step_size_spinBox.value() / 1000
        self.step_count = self.number_of_steps_spinBox_4.value()
        self.sweep_range = (self.step_size * self.step_count) - self.step_size
        self.end_frequency = self.start_frequency + self.sweep_range
        self.sweep_output.setText(f'{self.start_frequency} kHz to {self.end_frequency} kHz\n[{self.step_count} steps of {self.step_size} kHz]')

    def write_serial_and_update_status(self, f_sting_with_variable):
        for command in f_sting_with_variable:
            self.serial_thread.write_data(command)
            self.update_status(command)

    def apply_settings(self, ADG774_STATE, ADG774_STATE2, ADG774_STATE3, ADG1608_RC, ADG1608_RC2, ADG1608_RC3):
        self.write_serial_and_update_status(
        [f"<ADG1608_RC,{ADG1608_RC}>",
        f"<ADG1608_RC2,{ADG1608_RC2}>",
        f"<ADG1608_RC3,{ADG1608_RC3}>",
        f"<ADG1608_GAIN,{str(self.gain_resistor_comboBox.currentIndex())}>",
        f"<ADG1608_RFB,{str(self.fbr_comboBox.currentIndex())}>",
        f"<NUMBER_OF_INCREMENTS,{str(self.number_of_steps_spinBox_4.value())}>",
        f"<INCREMENT_FREQUENCY,0,{str(self.step_size_spinBox.value())}>",
        f"<SWEEP_DELAY,{str(self.settling_time_spinBox.value())}>",
        f"<PGA,{str(self.pga_comboBox.currentIndex())}>",
        f"<VOLTAGE,{str(self.output_voltage_comboBox.currentIndex())}>",
        f"<START_FREQUENCY,0,{str(self.start_freq_spinBox.value())}>",
        f"<ADG774_STATE,{ADG774_STATE}>",
        f"<ADG774_STATE2,{ADG774_STATE2}>",
        f"<ADG774_STATE3,{ADG774_STATE3}>"])

        self.serial_thread.set_calibration(self.cal_resistor_doubleSpinBox.value())
        self.update_status(f"Cal Resistor,{str(self.cal_resistor_doubleSpinBox.value())}")

        self.serial_thread.set_calibration_2(self.cal_resistor_doubleSpinBox_2.value())
        self.update_status(f"Cal Resistor 2,{str(self.cal_resistor_doubleSpinBox_2.value())}")

        self.serial_thread.sef_rfb(int(self.fbr_comboBox.currentIndex()))
        self.update_status(f"sef_rfb,{int(self.fbr_comboBox.currentIndex())}")

    def write(self, text):  # Handle sys.stdout.write: update display
        self.text_update.emit(text)  # Send signal to synchronise call with main thread

    def data_set(self):
        self.last_run = np.array([[0,1,2,3,4,5,6,7,8]])
        self.last_run = np.delete(self.serial_thread.np_data, 0, axis=0)
        self.all_runs = np.append(self.last_run, self.serial_thread.np_data, axis=0)
        self.serial_thread.np_data = np.array([[0,1,2,3,4,5,6,7,8]])

    def start_sweep(self):
        self.last_run = np.array([[0, 1, 2, 3, 4, 5, 6, 7, 8]])
        self.current_sweep = 1
        self.sweep_count = self.sweep_count_spinBox.value()

        ADG1608_RC = str(self.measure_1_comboBox_1.currentIndex())
        ADG1608_RC2 = str(self.measure_2_comboBox_1.currentIndex())
        ADG1608_RC3 = str(self.measure_3_comboBox_1.currentIndex())

        ADG774_STATE = str(2)
        ADG774_STATE2 = str(2)
        ADG774_STATE3 = str(2)

        if self.measure_1_comboBox_1.currentIndex() == 0:
            ADG774_STATE = 1
            ADG1608_RC = 0

        if self.measure_2_comboBox_1.currentIndex() == 0:
            ADG774_STATE2 = 1
            ADG1608_RC2 = 0

        if self.measure_3_comboBox_1.currentIndex() == 0:
            ADG774_STATE3 = 1
            ADG1608_RC3 = 0

        try:
            self.update_status(f"\n--- Configuring Device ---\n")
            self.apply_settings(ADG774_STATE, ADG774_STATE2, ADG774_STATE3, ADG1608_RC, ADG1608_RC2, ADG1608_RC3)
            self.update_status(f"\n--- Sweep {self.current_sweep} of {self.sweep_count} Starting ---\n")
            self.serial_thread.write_data('<RUN>')
            self.update_status(f"<RUN> \n")
            self.data_set()
            self.start_QPushButton.setEnabled(False)
            self.start_QPushButton.hide()
            self.stop_QPushButton.setEnabled(True)
            self.stop_QPushButton.show()
            self.disconnect_pushButton.setEnabled(False)
            self.progressBar.setProperty("value", 0)

        except:
            self.update_status(f"Please Connect Device Using Port Settings")

    def issue_command(self):
        self.serial_thread.write_data(f"{str(self.command_line.text())}")
        self.update_status(f"{str(self.command_line.text())}")
        self.data_set()

    def clear_plots_button(self):
        self.serial_thread.my_signal.connect(self.clear_all_multi)

    def clear_plots(self, progress_callback):
        # self.view.clear()
        self.s3.clear()
        # self.view2.clear()
        self.s2.clear()
        # self.view3.clear()
        self.sp1.clear()
        self.sp2.clear()
        self.sp3.clear()
        self.sp4.clear()
        self.sp5.clear()
        self.sp6.clear()
        # self.view4.clear()
        self.s4.clear()
        self.s5.clear()
        self.s6.clear()
        self.p1.clear()
        self.p2.clear()
        return "Done."

    def stop_sweep(self):
        date_stamp = dt.datetime.now().strftime('%Y-%m-%d_%H:%M:%S')
        try:
            self.serial_thread.write_data('<STOP>')
            self.update_status("<STOP>")
            self.update_status("\n--- Sweep Aborted ---\n")
            self.start_QPushButton.setEnabled(True)
            self.start_QPushButton.show()
            self.stop_QPushButton.setEnabled(False)
            self.stop_QPushButton.hide()
            self.disconnect_pushButton.setEnabled(True)
        except:
            self.update_status("No Sweep to Abort")

    def write_config(self):
        if not config.has_section("SERIAL_SETTINGS"):
            config.add_section("SERIAL_SETTINGS")
            config.set("SERIAL_SETTINGS", "port_name", f"{self.serial_port_QLineEdit.text()}")
            config.set("SERIAL_SETTINGS", "baud_rate", f"{baud_rate}")

        if not config.has_section("DATA_PATH"):
            config.add_section("DATA_PATH")
            config.set("DATA_PATH", "default", f"{sys.path[0]}/data")
            config.set("DATA_PATH", "custom", self.subject_id_lineEdit.text())

        if not config.has_section("DEVICE_SETTINGS"):
            config.add_section("DEVICE_SETTINGS")

            config.set("DEVICE_SETTINGS", "measure_1_comboBox_1", f"{self.measure_1_comboBox_1.currentIndex()}")
            config.set("DEVICE_SETTINGS", "measure_2_comboBox_1", f"{self.measure_2_comboBox_1.currentIndex()}")
            config.set("DEVICE_SETTINGS", "measure_3_comboBox_1", f"{self.measure_3_comboBox_1.currentIndex()}")
            config.set("DEVICE_SETTINGS", "ADG1608_GAIN", f"{self.gain_resistor_comboBox.currentIndex()}")
            config.set("DEVICE_SETTINGS", "ADG1608_RFB", f"{self.fbr_comboBox.currentIndex()}")
            config.set("DEVICE_SETTINGS", "number_of_steps", f"{self.number_of_steps_spinBox_4.value()}")
            config.set("DEVICE_SETTINGS", "step_size", f"{self.step_size_spinBox.value()}")
            config.set("DEVICE_SETTINGS", "SWEEP_DELAY", f"{self.settling_time_spinBox.value()}")
            config.set("DEVICE_SETTINGS", "PGA", f"{self.pga_comboBox.currentIndex()}")
            config.set("DEVICE_SETTINGS", "VOLTAGE", f"{self.output_voltage_comboBox.currentIndex()}")
            config.set("DEVICE_SETTINGS", "cal_resistor", f"{self.cal_resistor_doubleSpinBox.value()}")
            config.set("DEVICE_SETTINGS", "cal_resistor2", f"{self.cal_resistor_doubleSpinBox_2.value()}")
            config.set("DEVICE_SETTINGS", "START_FREQUENCY", f"{self.start_freq_spinBox.value()}")

        with open("config.ini", 'w') as configfile:
            config.write(configfile)

    def save_data(self):
        self.write_config()

        self.subject_id_lineEdit.setText(data_path['custom'])
        date_stamp = dt.datetime.now().strftime('%Y-%m-%d_%H:%M:%S')
        dataframe = pd.DataFrame(self.raw_data)
        dataframe.columns = ['frequency', 'real_unknown', 'imaginary_unknown', 'real_cal', 'imaginary_cal', 'real_cal2', 'imaginary_cal2', 'temperature', 'status']
        pd.DataFrame.to_csv(dataframe, f"{self.subject_id_lineEdit.text()}/data-{date_stamp}.csv")
        self.update_status(f"Data Saved to: {self.subject_id_lineEdit.text()}/data-{date_stamp}.csv")

        self.serial_thread.data_set = np.delete(self.serial_thread.data_set, (1), axis=0)
        dataframe = pd.DataFrame(self.calibrated_data)
        dataframe.columns = ['frequency', 'impedance', 'z_real', 'z_imaginary', 'real_cal2', 'imaginary_cal2', 'theta', 'gain_factor', 'Temperature', 'Status']
        pd.DataFrame.to_csv(dataframe, f"{self.subject_id_lineEdit.text()}/calibrated-data-{date_stamp}.csv")
        self.update_status(f"Data Saved to: {self.subject_id_lineEdit.text()}/calibrated-data-{date_stamp}.csv")
        self.lineEdit_data_file_name.setText(f"{self.subject_id_lineEdit.text()}/calibrated-data-{date_stamp}.csv")

        self.csv_file_path = self.lineEdit_data_file_name.text()

    def connect(self):
        self.serial_thread = SerialThread(port_name, baud_rate)
        self.serial_thread.start()
        try:
            self.raw_data = self.serial_thread.np_data
            self.calibrated_data = self.serial_thread.data_set
        except:
            pass
        self.serial_thread.serial_running == True
        self.serial_thread.my_signal.connect(self.update)
        self.serial_thread.my_connection_success.connect(self.successful_conection)
        self.serial_thread.my_connection_failure.connect(self.failed_conection)
        self.serial_thread.my_connection_ended.connect(self.ended_conection)

    def disconnect(self):
        self.serial_thread.end_serial_connection()
        self.serial_thread.serial_running = False
        self.connect_pushButton.setEnabled(True)
        self.disconnect_pushButton.setEnabled(False)
        self.serial_port_QLineEdit.setEnabled(True)
        self.groupBox_2.setEnabled(False)
        self.start_QPushButton.setEnabled(False)

    def successful_conection(self):
        self.update_status(f'Connected with:\n{port_name}')
        self.connect_pushButton.setEnabled(False)
        self.disconnect_pushButton.setEnabled(True)
        self.serial_port_QLineEdit.setEnabled(False)
        self.groupBox_2.setEnabled(True)
        self.start_QPushButton.setEnabled(True)

    def failed_conection(self):
        self.update_status(f'Failed to connect with:\n{port_name}')

    def ended_conection(self):
        self.update_status(f'Connection closed:\n{port_name}')

    def closeEvent(self, event):
        self.write_config()
        try:
            self.disconnect()
        except:
            print('no connections to close')

    def update_status(self, text):
        self.bottom_textBrowser.append(text)
        self.sweep_control()

    def update_calibrated_data_view(self, text):
        self.calibrated_data_textBrowser.clear()
        self.calibrated_data_textBrowser.append(text)

    def update_raw_data_view(self, text):
        self.raw_data_textBrowser.clear()
        self.raw_data_textBrowser.append(text)

    def get_val(self, a_np_array):
        bio = io.BytesIO()
        np.savetxt(bio, a_np_array, fmt="%.3f")
        mystr = bio.getvalue().decode('latin1')
        return mystr

    def get_precision_val(self, a_np_array):
        bio = io.BytesIO()
        np.savetxt(bio, a_np_array)
        mystr = bio.getvalue().decode('latin1')
        return mystr

    def set_current_data(self, progress_callback):
        # entire array
        self.raw_data = self.serial_thread.np_data
        # serial_thread np_data (last row value)
        self.raw_frequency = self.raw_data[-1:, 0]
        self.raw_real_unknown = self.raw_data[-1:, 1]
        self.raw_imaginary_unknown = self.raw_data[-1:, 2]
        self.raw_real_cal = self.raw_data[-1:, 3]
        self.raw_imaginary_cal = self.raw_data[-1:, 4]
        self.raw_real_cal2 = self.raw_data[-1:, 5]
        self.raw_imaginary_cal2 = self.raw_data[-1:, 6]
        self.raw_temp = self.raw_data[-1:, 7]
        self.raw_status = self.raw_data[-1:, 8]

        # entire array
        self.calibrated_data = self.serial_thread.data_set
        # serial_thread data_set (last row value)
        self.frequency = self.calibrated_data[-1:, 0]
        self.impedance = self.calibrated_data[-1:, 1]
        self.z_real = self.calibrated_data[-1:, 2]
        self.z_imaginary = self.calibrated_data[-1:, 3]
        self.real_cal2 = self.calibrated_data[-1:, 4]
        self.imaginary_cal2 = self.calibrated_data[-1:, 5]
        self.theta = self.calibrated_data[-1:, 6]
        self.gain_factor = self.calibrated_data[-1:, 7]
        self.temperature = self.calibrated_data[-1:, 8]
        self.status = self.calibrated_data[-1:, 9]

        # derived values
        self.max_frequency = self.end_frequency
        self.current_frequency = self.frequency
        self.current_step = int(((self.frequency - self.start_freq_spinBox.value()) / self.step_size_spinBox.value()) + 1)
        self.total_steps = self.step_count
        self.percent_complete = (self.current_step / self.step_count) * 100
        self.progressBar.setValue(int(self.percent_complete))
        self.current_color_fixed_frequency_scale = self.frequency
        text = f'Frequency (kHz): {self.get_val(self.frequency / 1000)}Impedance (ohms): {self.get_val(self.impedance)}Phase (degree[s]): {self.get_val(self.theta)}Gain Factor: {self.get_precision_val(self.gain_factor)}'
        return text

    def update_view_and_view2(self, progress_callback):
        global spots2, spots3
        spots2 = []
        spots3 = []
        for i in range(np.alen(self.serial_thread.data_set[1:, ])):
            spots3.append({'pos': (self.z_real, self.z_imaginary), 'brush': pg.intColor(self.current_color_fixed_frequency_scale, self.total_colors_fixed_frequency_scale), 'pen': pg.mkPen(None), 'size': 5})
            spots2.append({'pos': (self.frequency / 1000, self.temperature), 'brush': pg.intColor(self.current_color_fixed_frequency_scale, self.total_colors_fixed_frequency_scale), 'pen': pg.mkPen(None), 'size': 5})
        self.s3.addPoints(spots3)
        self.s2.addPoints(spots2)

    def update_view3(self, progress_callback):
        self.sp1.addPoints(x=self.raw_frequency, y=self.raw_real_unknown, brush=(255, 0, 0), size=5, symbol='o', pen=(0, 0, 0, 0))
        self.sp2.addPoints(x=self.raw_frequency, y=self.raw_imaginary_unknown, brush=(255, 100, 100), size=6, symbol='x', pen=(0, 0, 0, 0))
        self.sp3.addPoints(x=self.raw_frequency, y=self.raw_real_cal, brush=(0, 255, 0), size=5, symbol='o', pen=(0, 0, 0, 0))
        self.sp4.addPoints(x=self.raw_frequency, y=self.raw_imaginary_cal, brush=(100, 255, 100), size=6, symbol='x', pen=(0, 0, 0, 0))
        self.sp5.addPoints(x=self.raw_frequency, y=self.raw_real_cal2, brush=(0, 0, 255), size=5, symbol='o', pen=(0, 0, 0, 0))
        self.sp6.addPoints(x=self.raw_frequency, y=self.raw_imaginary_cal2, brush=(100, 100, 255), size=6, symbol='x', pen=(0, 0, 0, 0))

    def update_view4(self, progress_callback):
        self.s4.setData(x=self.raw_data[:, 0] / 1000, y=np.sqrt((self.raw_data[:, 1] ** 2) + (self.raw_data[:, 2] ** 2)), size=5, pen=(255, 0, 0))
        self.s5.setData(x=self.raw_data[:, 0] / 1000, y=np.sqrt((self.raw_data[:, 3] ** 2) + (self.raw_data[:, 4] ** 2)), size=5, pen=(0, 255, 0))
        self.s6.setData(x=self.raw_data[:, 0] / 1000, y=np.sqrt((self.raw_data[:, 5] ** 2) + (self.raw_data[:, 6] ** 2)), size=5, pen=(0, 0, 255))

    def sweep_control(self):
        print(f'if ({self.current_step} == {self.total_steps}) and {self.current_frequency} != 0:')
        print(f'if ({self.current_step == self.total_steps}) and {self.current_frequency != 0}:')
        if (self.current_step == self.total_steps) and self.current_frequency != 0:
            self.current_step = 0
            self.serial_thread.write_data('<STOP>')
            self.update_status(f"<STOP> \n")
            self.update_status(f"--- Sweep {self.current_sweep} of {self.sweep_count} Completed ---")
            self.progressBar.setValue(100)
            self.start_QPushButton.setEnabled(True)
            self.start_QPushButton.show()
            self.stop_QPushButton.setEnabled(False)
            self.stop_QPushButton.hide()
            self.disconnect_pushButton.setEnabled(True)
            self.data_set()
            if self.current_sweep != self.sweep_count:
                self.current_sweep = self.current_sweep + 1
                self.update_status(f" ")
                self.update_status(f"--- Sweep {self.current_sweep} of {self.sweep_count} Starting ---")
                self.update_status(f" ")
                self.serial_thread.write_data('<RUN>')
                self.update_status(f"<RUN> \n")
                self.start_QPushButton.setEnabled(False)
                self.start_QPushButton.hide()
                self.stop_QPushButton.setEnabled(True)
                self.disconnect_pushButton.setEnabled(False)
                self.stop_QPushButton.show()
                self.progressBar.setProperty("value", 0)
                self.data_set()
            if self.current_sweep == self.sweep_count + 1:
                self.progressBar.setValue(100)
                self.serial_thread.write_data('<STOP>')
                self.update_status(f"<STOP> \n")
                self.start_QPushButton.setEnabled(True)
                self.start_QPushButton.show()
                self.stop_QPushButton.setEnabled(False)
                self.stop_QPushButton.hide()
                self.disconnect_pushButton.setEnabled(True)
                self.data_set()

    def update(self):
        pass
        # self.bottom_textBrowser_2.append(np.array2string(self.raw_data[:]))
        # self.update_calibrated_data_view(self.get_val(self.calibrated_data[:]))
        # self.update_raw_data_view(self.get_val(self.raw_data[:]))

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
