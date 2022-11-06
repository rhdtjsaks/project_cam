# region [Import]
import signal, os, subprocess
import threading
import sys

from PyQt5 import uic
from PyQt5 import QtWidgets, QtPrintSupport, QtGui
from PyQt5.QtGui import QImage, QPixmap, QTransform
from PyQt5.QtCore import QThread, Qt, pyqtSignal, pyqtSlot, QCoreApplication
from PyQt5.QtPrintSupport import QPrinter
from PyQt5.QtWidgets import *
from PyQt5.QtWidgets import QDialog, QApplication, QFileDialog

from PyQt5.QtCore import *
from PyQt5.QtGui import *

app = QApplication(sys.argv)

import time
import cv2
import serial

from sh import gphoto2 as gp

import source_rc

from datetime import datetime

# 불러오기
_form_1 = uic.loadUiType("UI/form_1.ui")[0]
_form_2 = uic.loadUiType("UI/form_2.ui")[0]
_form_3 = uic.loadUiType("UI/form_3.ui")[0]
_form_4 = uic.loadUiType("UI/form_4.ui")[0]
# endregion

# region [Read_Worker]

# region [CRC]
crctab = [
    0x0000, 0xc0c1, 0xc181, 0x0140, 0xc301, 0x03c0, 0x0280, 0xc241,
    0xc601, 0x06c0, 0x0780, 0xc741, 0x0500, 0xc5c1, 0xc481, 0x0440,
    0xcc01, 0x0cc0, 0x0d80, 0xcd41, 0x0f00, 0xcfc1, 0xce81, 0x0e40,
    0x0a00, 0xcac1, 0xcb81, 0x0b40, 0xc901, 0x09c0, 0x0880, 0xc841,
    0xd801, 0x18c0, 0x1980, 0xd941, 0x1b00, 0xdbc1, 0xda81, 0x1a40,
    0x1e00, 0xdec1, 0xdf81, 0x1f40, 0xdd01, 0x1dc0, 0x1c80, 0xdc41,
    0x1400, 0xd4c1, 0xd581, 0x1540, 0xd701, 0x17c0, 0x1680, 0xd641,
    0xd201, 0x12c0, 0x1380, 0xd341, 0x1100, 0xd1c1, 0xd081, 0x1040,
    0xf001, 0x30c0, 0x3180, 0xf141, 0x3300, 0xf3c1, 0xf281, 0x3240,
    0x3600, 0xf6c1, 0xf781, 0x3740, 0xf501, 0x35c0, 0x3480, 0xf441,
    0x3c00, 0xfcc1, 0xfd81, 0x3d40, 0xff01, 0x3fc0, 0x3e80, 0xfe41,
    0xfa01, 0x3ac0, 0x3b80, 0xfb41, 0x3900, 0xf9c1, 0xf881, 0x3840,
    0x2800, 0xe8c1, 0xe981, 0x2940, 0xeb01, 0x2bc0, 0x2a80, 0xea41,
    0xee01, 0x2ec0, 0x2f80, 0xef41, 0x2d00, 0xedc1, 0xec81, 0x2c40,
    0xe401, 0x24c0, 0x2580, 0xe541, 0x2700, 0xe7c1, 0xe681, 0x2640,
    0x2200, 0xe2c1, 0xe381, 0x2340, 0xe101, 0x21c0, 0x2080, 0xe041,
    0xa001, 0x60c0, 0x6180, 0xa141, 0x6300, 0xa3c1, 0xa281, 0x6240,
    0x6600, 0xa6c1, 0xa781, 0x6740, 0xa501, 0x65c0, 0x6480, 0xa441,
    0x6c00, 0xacc1, 0xad81, 0x6d40, 0xaf01, 0x6fc0, 0x6e80, 0xae41,
    0xaa01, 0x6ac0, 0x6b80, 0xab41, 0x6900, 0xa9c1, 0xa881, 0x6840,
    0x7800, 0xb8c1, 0xb981, 0x7940, 0xbb01, 0x7bc0, 0x7a80, 0xba41,
    0xbe01, 0x7ec0, 0x7f80, 0xbf41, 0x7d00, 0xbdc1, 0xbc81, 0x7c40,
    0xb401, 0x74c0, 0x7580, 0xb541, 0x7700, 0xb7c1, 0xb681, 0x7640,
    0x7200, 0xb2c1, 0xb381, 0x7340, 0xb101, 0x71c0, 0x7080, 0xb041,
    0x5000, 0x90c1, 0x9181, 0x5140, 0x9301, 0x53c0, 0x5280, 0x9241,
    0x9601, 0x56c0, 0x5780, 0x9741, 0x5500, 0x95c1, 0x9481, 0x5440,
    0x9c01, 0x5cc0, 0x5d80, 0x9d41, 0x5f00, 0x9fc1, 0x9e81, 0x5e40,
    0x5a00, 0x9ac1, 0x9b81, 0x5b40, 0x9901, 0x59c0, 0x5880, 0x9841,
    0x8801, 0x48c0, 0x4980, 0x8941, 0x4b00, 0x8bc1, 0x8a81, 0x4a40,
    0x4e00, 0x8ec1, 0x8f81, 0x4f40, 0x8d01, 0x4dc0, 0x4c80, 0x8c41,
    0x4400, 0x84c1, 0x8581, 0x4540, 0x8701, 0x47c0, 0x4680, 0x8641,
    0x8201, 0x42c0, 0x4380, 0x8341, 0x4100, 0x81c1, 0x8081, 0x4040
]

def crc16(data):
    icrc = 0x00
    for datum in data:
        icrc = ((icrc >> 8) & 0xff) ^ crctab[(icrc & 0xff) ^ datum];

    return icrc
# endregion

class Read_Worker(QThread):
    def __init__(self, parent=None):
        super(Read_Worker, self).__init__(parent)
        self.isRun = False
        self.count = 0

    def run(self):
        try:
            while self.isRun:
                if self.count == 16:
                    self.count = 0
                if form_1.py_serial.readable():
                    for value in form_1.py_serial.read():
                        self.count += 1
                        # print(f'count: {self.count}, value: {value}')

                        if self.count == 11:
                            if value == 0:  # 거래 성공
                                print('거래 성공')

                                Read_Worker_Stop(form_1)

                                OpenCV_Worker_Start(form_2)
                                Timer_Worker_Start(form_2)
                                CapTure_Worker_Start(form_2)

                                form_2.label_form_2_0.setText('Ready')

                                widget.setCurrentIndex(widget.currentIndex() + 1)
                            if value == 255:  # 거래 실패
                                print('거래 실패')
                                form_1.widge_form_1_0.show()
                                form_1.widge_form_1_1.hide()
                                form_1.widge_form_1_2.hide()
                                Read_Worker_Stop(form_1)


        except Exception as ex:
            print(ex)

# region [Read_Worker]
class Write_Worker(QThread):
    def __init__(self, parent=None):
        super(Write_Worker, self).__init__(parent)
        self.isRun = False
        self.count = 0

    def run(self):
        try:
                self.count += 1

                if self.count == 256:
                    self.count = 1

                if form_1.printMoney == 5000:
                    cmd = [0x00, 0x0D, self.count, 0x20, 0x02, 0x30, 0x30, 0x30, 0x30, 0x35, 0x30, 0x30, 0x30, 0x03]
                elif form_1.printMoney == 5000 * 2:
                    cmd = [0x00, 0x0D, self.count, 0x20, 0x02, 0x30, 0x30, 0x30, 0x31, 0x30, 0x30, 0x30, 0x30, 0x03]
                elif form_1.printMoney == 5000 * 3:
                    cmd = [0x00, 0x0D, self.count, 0x20, 0x02, 0x30, 0x30, 0x30, 0x31, 0x35, 0x30, 0x30, 0x30, 0x03]
                elif form_1.printMoney == 5000 * 4:
                    cmd = [0x00, 0x0D, self.count, 0x20, 0x02, 0x30, 0x30, 0x30, 0x32, 0x30, 0x30, 0x30, 0x30, 0x03]
                elif form_1.printMoney == 5000 * 5:
                    cmd = [0x00, 0x0D, self.count, 0x20, 0x02, 0x30, 0x30, 0x30, 0x32, 0x35, 0x30, 0x30, 0x30, 0x03]
                elif form_1.printMoney == 5000 * 6:
                    cmd = [0x00, 0x0D, self.count, 0x20, 0x02, 0x30, 0x30, 0x30, 0x33, 0x30, 0x30, 0x30, 0x30, 0x03]
                elif form_1.printMoney == 5000 * 7:
                    cmd = [0x00, 0x0D, self.count, 0x20, 0x02, 0x30, 0x30, 0x30, 0x33, 0x35, 0x30, 0x30, 0x30, 0x03]
                elif form_1.printMoney == 5000 * 8:
                    cmd = [0x00, 0x0D, self.count, 0x20, 0x02, 0x30, 0x30, 0x30, 0x34, 0x30, 0x30, 0x30, 0x30, 0x03]
                elif form_1.printMoney == 5000 * 9:
                    cmd = [0x00, 0x0D, self.count, 0x20, 0x02, 0x30, 0x30, 0x30, 0x34, 0x35, 0x30, 0x30, 0x30, 0x03]
                elif form_1.printMoney == 5000 * 10:
                    cmd = [0x00, 0x0D, self.count, 0x20, 0x02, 0x30, 0x30, 0x30, 0x35, 0x30, 0x30, 0x30, 0x30, 0x03]

                res = crc16(cmd)
                cmd_list = [0x02] + cmd + [res >> 8, res & 0xff]
                values = bytearray(cmd_list)
                print ("Returning single value %d %02x %02x" %(res, res >> 8, res & 0xff))
                form_1.py_serial.write(values)

                Write_Worker_Stop(self.parent())
                Read_Worker_Start(self.parent())


        except Exception as ex:
            print(ex)
            
def Read_Worker_Start(self):
    if not self.read_worker.isRun:
        self.read_worker.isRun = True
        self.read_worker.start()

def Read_Worker_Stop(self):
    if self.read_worker.isRun:
        self.read_worker.isRun = False
        
def Write_Worker_Start(self):
    if not self.write_worker.isRun:
        self.write_worker.isRun = True
        self.write_worker.start()

def Write_Worker_Stop(self):
    if self.write_worker.isRun:
        self.write_worker.isRun = False
# endregion

# region [Evnet-QLabel-Click]
def clickable(widget):
    class Filter(QObject):
        clicked = pyqtSignal()  # pyside2 사용자는 pyqtSignal() -> Signal()로 변경

        def eventFilter(self, obj, event):
            if obj == widget:
                if event.type() == QEvent.MouseButtonRelease:
                    if obj.rect().contains(event.pos()):
                        self.clicked.emit()
                        # The developer can opt for .emit(obj) to get the object within the slot.
                        return True
            return False

    filter = Filter(widget)
    widget.installEventFilter(filter)
    return filter.clicked

def d_clickable(widget):
    class Filter(QObject):
        clicked = pyqtSignal()  # pyside2 사용자는 pyqtSignal() -> Signal()로 변경

        def eventFilter(self, obj, event):
            if obj == widget:
                if event.type() == QEvent.MouseButtonDblClick:
                    if obj.rect().contains(event.pos()):
                        self.clicked.emit()
                        # The developer can opt for .emit(obj) to get the object within the slot.
                        return True
            return False

    filter = Filter(widget)
    widget.installEventFilter(filter)
    return filter.clicked
# endregion

# region Kill
try:
    def killGphoto2Process():
        p = subprocess.Popen(['ps', '-A'], stdout=subprocess.PIPE)
        out, err = p.communicate()

        # Search for the process we want to kill
        for line in out.splitlines():
            if b'gvfsd-gphoto2' in line:
                # Kill that process!
                pid = int(line.split(None,1)[0])
                os.kill(pid, signal.SIGKILL)
                
    clearCommand = ["--folder", "/store_00020001/DCIM/100CANON", \
                    "--delete-all-files", "-R"]
    triggerCommand = ["--trigger-capture"]
    downloadCommand = ["--get-all-files"]

    clearCmd = "sudo modprobe v4l2loopback && pkill gphoto2"
    os.system(clearCmd)
    killGphoto2Process()
    gp(clearCommand)
except Exception as ex:
    print(ex)
# endregion

# region [Form_1]
class Form_1(QDialog, _form_1):
    def __init__(self):
        super(Form_1, self).__init__()
        self.setupUi(self)

        self.setStyleSheet("background-color: white;")

        self.inputPW = ''
        self.superFlag = False
        self.buttonFlag = False

        self.printCount = 2
        self.printMoney = 5000
        
        self.py_serial = serial.Serial(port='/dev/ttyUSB0', baudrate=1200, parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS)

        self.read_worker = Read_Worker(parent=self)
        self.write_worker = Write_Worker(parent=self)

        self.pushButton_form_1_Quit.setDisabled(True)

        self.pushButton_form_1_Quit.hide()
        self.lineEdit_form_1_Num.hide()
        self.pushButton_form_1_Num_9.hide()
        self.pushButton_form_1_Num_8.hide()
        self.pushButton_form_1_Num_7.hide()
        self.pushButton_form_1_Num_6.hide()
        self.pushButton_form_1_Num_5.hide()
        self.pushButton_form_1_Num_4.hide()
        self.pushButton_form_1_Num_3.hide()
        self.pushButton_form_1_Num_2.hide()
        self.pushButton_form_1_Num_1.hide()
        self.pushButton_form_1_Num_0.hide()
        self.pushButton_form_1_Num_Delete.hide()
        self.form_1_checkBox.hide()

        self.widge_form_1_1.hide()
        self.widge_form_1_2.hide()

        createPath_1 = '/home/test/Desktop/image_capture'
        if not os.path.exists(createPath_1):
            os.makedirs(createPath_1)

        now = datetime.now()
        createPath_2 = createPath_1 + '/' + str(now.date())
        if not os.path.exists(createPath_2):
            os.makedirs(createPath_2)

        self.pushButton_form_1_Quit.clicked.connect(self.quit)
        self.pushButton_form_1_Num_9.clicked.connect(self.pushButton_form_1_Num_Func)
        self.pushButton_form_1_Num_8.clicked.connect(self.pushButton_form_1_Num_Func)
        self.pushButton_form_1_Num_7.clicked.connect(self.pushButton_form_1_Num_Func)
        self.pushButton_form_1_Num_6.clicked.connect(self.pushButton_form_1_Num_Func)
        self.pushButton_form_1_Num_5.clicked.connect(self.pushButton_form_1_Num_Func)
        self.pushButton_form_1_Num_4.clicked.connect(self.pushButton_form_1_Num_Func)
        self.pushButton_form_1_Num_3.clicked.connect(self.pushButton_form_1_Num_Func)
        self.pushButton_form_1_Num_2.clicked.connect(self.pushButton_form_1_Num_Func)
        self.pushButton_form_1_Num_1.clicked.connect(self.pushButton_form_1_Num_Func)
        self.pushButton_form_1_Num_0.clicked.connect(self.pushButton_form_1_Num_Func)
        self.pushButton_form_1_Num_Delete.clicked.connect(self.pushButton_form_1_Num_Func)

        clickable(self.pushButton_form_1_Setting).connect(self.pushButton_form_1_Setting_Func)

        clickable(self.label_form_1_Start).connect(self.label_form_1_Start_Clicked)
        clickable(self.label_form_1_Select_0).connect(self.label_form_1_Select_0_Clicked)
        clickable(self.label_form_1_Select_2).connect(self.label_form_1_Select_2_Clicked)
        clickable(self.label_form_1_Select_4).connect(self.label_form_1_Select_4_Clicked)

    def label_form_1_Start_Clicked(self):
        self.printCount = 2
        self.printMoney = 5000
        self.widge_form_1_0.hide()
        self.widge_form_1_1.show()

    def label_form_1_Select_0_Clicked(self):
        self.printCount -= 2
        self.printMoney -= 5000

        if self.printCount < 2:
            self.printCount = 2
            self.printMoney = 5000

        self.label_form_1_Select_1.setText(str(self.printCount))
        self.label_form_1_Select_3.setText(str(self.printMoney))

    def label_form_1_Select_2_Clicked(self):
        self.printCount += 2
        self.printMoney += 5000

        if self.printCount > 10:
            self.printCount = 10
            self.printMoney = 50000

        self.label_form_1_Select_1.setText(str(self.printCount))
        self.label_form_1_Select_3.setText(str(self.printMoney))

    def label_form_1_Select_4_Clicked(self):
        self.label_form_1_Card.setText('카드를 투입구에 넣어주세요\n\n' + str(self.printMoney) + '원')

        self.widge_form_1_1.hide()
        self.widge_form_1_2.show()
        
        self.testFunc()

    def testFunc(self):
        if self.form_1_checkBox.isChecked() == True: # 관리자 모드
            OpenCV_Worker_Start(form_2)
            Timer_Worker_Start(form_2)
            CapTure_Worker_Start(form_2)
            
            form_2.label_form_2_0.setText('Ready')

            widget.setCurrentIndex(widget.currentIndex() + 1)
        else: # 일반 모드
            print('일반 모드')
            Write_Worker_Start(self)

    def pushButton_form_1_Setting_Func(self):
        if self.buttonFlag == True:
            self.pushButton_form_1_Quit.hide()
            self.lineEdit_form_1_Num.hide()
            self.pushButton_form_1_Num_9.hide()
            self.pushButton_form_1_Num_8.hide()
            self.pushButton_form_1_Num_7.hide()
            self.pushButton_form_1_Num_6.hide()
            self.pushButton_form_1_Num_5.hide()
            self.pushButton_form_1_Num_4.hide()
            self.pushButton_form_1_Num_3.hide()
            self.pushButton_form_1_Num_2.hide()
            self.pushButton_form_1_Num_1.hide()
            self.pushButton_form_1_Num_0.hide()
            self.pushButton_form_1_Num_Delete.hide()
            self.form_1_checkBox.hide()

            self.form_1_checkBox.setDisabled(True)
            self.pushButton_form_1_Quit.setDisabled(True)
            
            self.buttonFlag = False
        else:
            self.pushButton_form_1_Quit.show()
            self.lineEdit_form_1_Num.show()
            self.pushButton_form_1_Num_9.show()
            self.pushButton_form_1_Num_8.show()
            self.pushButton_form_1_Num_7.show()
            self.pushButton_form_1_Num_6.show()
            self.pushButton_form_1_Num_5.show()
            self.pushButton_form_1_Num_4.show()
            self.pushButton_form_1_Num_3.show()
            self.pushButton_form_1_Num_2.show()
            self.pushButton_form_1_Num_1.show()
            self.pushButton_form_1_Num_0.show()
            self.pushButton_form_1_Num_Delete.show()
            self.form_1_checkBox.show()
            
            self.buttonFlag = True

    def pushButton_form_1_Num_Func(self):
        widget = self.sender()
        t = widget.text()

        if t == 'Delete':
            self.inputPW = ''

        if len(self.inputPW) < 4 and t != 'Delete':
            self.inputPW = self.inputPW + t

        self.lineEdit_form_1_Num.setText(self.inputPW)

        if self.inputPW == '2582':
            self.inputPW = ''
            self.lineEdit_form_1_Num.setText(self.inputPW)

            self.form_1_checkBox.setDisabled(False)
            self.pushButton_form_1_Quit.setDisabled(False)
            
    def quit(self):
        sys.exit(0)
# endregion

# region [ Cap - Worker ... ]
def clearCam():
    clearCmd = "sudo modprobe v4l2loopback && pkill gphoto2"
    os.system(clearCmd)

def runCam():
    runCmd = "gphoto2 --stdout --capture-movie | ffmpeg -i - -vcodec rawvideo -pix_fmt yuv420p -threads 0 -f v4l2 /dev/video0"
    os.system(runCmd)

def CapTure_Worker_Start(self):
    if not self.capture_worker.isRun:
        self.capture_worker.isRun = True
        self.capture_worker.start()

def CapTure_Worker_Stop(self):
    if self.capture_worker.isRun:
        self.capture_worker.isRun = False

class CapTure_Worker(QThread):
    def __init__(self, parent=None):
        super(CapTure_Worker, self).__init__(parent)
        self.isRun = False

    def run(self):
        try:
            runCam()

        except Exception as ex:
            print(ex)

def OpenCV_Worker_Start(self):
    if not self.opencv_worker.isRun:
        self.opencv_worker.isRun = True
        self.opencv_worker.start()

def OpenCV_Worker_Stop(self):
    if self.opencv_worker.isRun:
        self.opencv_worker.isRun = False

class OpenCV_Worker(QThread):
    changePixmap = pyqtSignal(QImage)

    def __init__(self, parent=None):
        super(OpenCV_Worker, self).__init__(parent)
        self.isRun = False

    def run(self):
        try:
            time.sleep(10)
            cap = cv2.VideoCapture(0)  ## EOS Cam...
            while self.isRun:
                ret, frame = cap.read()

                if ret:
                    rgbImage = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    h, w, ch = rgbImage.shape
                    bytesPerLine = ch * w
                    convertToQtFormat = QImage(rgbImage.data, w, h, bytesPerLine, QImage.Format_RGB888)
                    transform = QtGui.QTransform().rotate(270)
                    p = convertToQtFormat.transformed(transform, Qt.SmoothTransformation).scaled(821, 1080, Qt.KeepAspectRatio)
                    
                    self.changePixmap.emit(p)
        except Exception as ex:
            print(ex)

            form_1.widge_form_1_0.show()
            form_1.widge_form_1_1.hide()
            form_1.widge_form_1_2.hide()
            widget.setCurrentIndex(widget.currentIndex() - 1)
# endregion

# region [ Timer - Worker ... ]
def Timer_Worker_Start(self):
    if not self.timer_worker.isRun:
        self.timer_worker.isRun = True
        self.timer_worker.start()

def Timer_Worker_Stop(self):
    if self.timer_worker.isRun:
        self.timer_worker.isRun = False

captureList = []
selected_captureList = [0, 0]

class Timer_Worker(QThread):
    def __init__(self, parent=None):
        super(Timer_Worker, self).__init__(parent)
        self.isRun = False
        self.Flag = False

    def run(self):
        try:
            while self.isRun:
                if self.parent().cnt == 10:
                    time.sleep(2)
                    
                if self.Flag == False:
                    self.Flag = True

                    form_2.widget_form_2_0.show()
                    time.sleep(3)
                    form_2.label_form_2_0.setText('Ready')
                    time.sleep(3)
                    form_2.label_form_2_0.setText('Action!')
                    time.sleep(3)
                    form_2.label_form_2_0.setText('Loading')

                    form_2.widget_form_2_0.hide()
                    form_2.widget_form_2_1.show()
                    
                    form_2.label_form_2_Timer.show()
                    form_2.label_form_2_Captrue_Num.show()

                time.sleep(1)

                self.parent().cnt -= 1
                self.parent().label_form_2_Timer.setText(str(self.parent().cnt))
                
                # DEBUG ...
                if self.parent().cnt == 0:
                    self.parent().cnt = 10

                    now = datetime.now()
                    current_time = now.strftime('%Y_%m_%d_%H_%M_%S')
                    savePath = '/home/test/Desktop/image_capture/' + str(now.date()) + '/' + current_time + '.jpg'

                    CapTure_Worker_Stop(self.parent())
                    clearCam()

                    gp(triggerCommand)
                    time.sleep(1)
                    gp(downloadCommand)
                    gp(clearCommand)

                    for filename in os.listdir("."):
                        if len(filename) < 13:
                            if filename.endswith(".JPG"):
                                os.rename(filename, (savePath))
                                print("Renamed the JPG")
                    captureList.append(savePath)

                    self.parent().capCount += 1
                    form_2.label_form_2_Captrue_Num.setText('6/' + str(self.parent().capCount))
                    
                    CapTure_Worker_Start(self.parent())

                    if self.parent().capCount == 6:
                        clearCam()
                        CapTure_Worker_Stop(self.parent())
                        OpenCV_Worker_Stop(self.parent())
                        Timer_Worker_Stop(self.parent())
                        
                        form_2.label_form_2_Timer.hide()
                        form_2.label_form_2_Captrue_Num.hide()
                        
                        form_2.widget_form_2_1.hide()
                        form_2.widget_form_2_0.show()
                        time.sleep(2)
                        form_2.label_form_2_0.setText('Loading.')
                        time.sleep(2)
                        form_2.label_form_2_0.setText('Loading..')
                        time.sleep(2)
                        form_2.label_form_2_0.setText('Loading...')
                        time.sleep(2)
                        form_2.label_form_2_0.setText('Loading....')

                        self.Flag = False
                        self.parent().cnt = 10
                        self.parent().capCount = 0

                        form_2.label_0.clear()
                        form_2.label_form_2_Timer.setText(str(self.parent().cnt))
                        form_2.label_form_2_Captrue_Num.setText('6/' + str(self.parent().capCount))

                        form_3.setImageList()
                        form_2.widget_form_2_0.hide()
                        
                        widget.setCurrentIndex(widget.currentIndex() + 1)

        except Exception as ex:
            print(ex)
            
            CapTure_Worker_Stop(self.parent())
            OpenCV_Worker_Stop(self.parent())
            Timer_Worker_Stop(self.parent())
            
            form_2.label_0.clear()
            form_2.label_form_2_Timer.setText('10')
            form_2.label_form_2_Captrue_Num.setText('6/0')

            form_1.widge_form_1_0.show()
            form_1.widge_form_1_1.hide()
            form_1.widge_form_1_2.hide()
            widget.setCurrentIndex(widget.currentIndex() - 1)
# endregion

# region [Form_2]
class Form_2(QDialog, _form_2):
    def __init__(self):
        super(Form_2, self).__init__()
        self.setupUi(self)

        self.setStyleSheet("background-color: white;")

        self.capCount = 0
        self.cnt = 10

        self.widget_form_2_1.hide()

        self.label_0 = QLabel(self)
        self.verticalLayout_form_2_Cam.addWidget(self.label_0)

        self.capture_worker = CapTure_Worker(parent=self)
        self.opencv_worker = OpenCV_Worker(parent=self)
        self.timer_worker = Timer_Worker(parent=self)
        self.opencv_worker.changePixmap.connect(self.setImage)

    @pyqtSlot(QImage)
    def setImage(self, image):
        self.label_0.setPixmap(QPixmap.fromImage(image))
# endregion

# region [Form_3]
class Form_3(QDialog, _form_3):
    capImage_0 = pyqtSignal(QImage)
    capImage_1 = pyqtSignal(QImage)
    capImage_2 = pyqtSignal(QImage)
    capImage_3 = pyqtSignal(QImage)
    capImage_4 = pyqtSignal(QImage)
    capImage_5 = pyqtSignal(QImage)
    
    capImage_6 = pyqtSignal(QImage)
    capImage_7 = pyqtSignal(QImage)
    capImage_8 = pyqtSignal(QImage)
    capImage_9 = pyqtSignal(QImage)

    def __init__(self):
        super(Form_3, self).__init__()
        self.setupUi(self)

        self.setStyleSheet("background-color: white;")

        self.capImage_0.connect(self.setImage_0)
        self.capImage_1.connect(self.setImage_1)
        self.capImage_2.connect(self.setImage_2)
        self.capImage_3.connect(self.setImage_3)
        self.capImage_4.connect(self.setImage_4)
        self.capImage_5.connect(self.setImage_5)
        
        self.capImage_6.connect(self.setImage_6)
        self.capImage_7.connect(self.setImage_7)
        self.capImage_8.connect(self.setImage_8)
        self.capImage_9.connect(self.setImage_9)

        clickable(self.label_form_0).connect(self.label_form_0_Func)
        clickable(self.label_form_1).connect(self.label_form_1_Func)
        clickable(self.label_form_2).connect(self.label_form_2_Func)
        clickable(self.label_form_3).connect(self.label_form_3_Func)
        clickable(self.label_form_4).connect(self.label_form_4_Func)
        clickable(self.label_form_5).connect(self.label_form_5_Func)
        
        d_clickable(self.label_form_6).connect(self.label_form_6_Func)
        d_clickable(self.label_form_7).connect(self.label_form_6_Func)
        d_clickable(self.label_form_8).connect(self.label_form_7_Func)
        d_clickable(self.label_form_9).connect(self.label_form_7_Func)
        
        clickable(self.label_form_OK).connect(self.pushButton_form_3_Next_Func)

    def setImageList(self):
        for i in range(0, 6):
            time.sleep(0.2)
            capture_path = captureList[i]
            img = cv2.imread(capture_path, cv2.IMREAD_COLOR)
            rgbImage = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            h, w, ch = rgbImage.shape
            bytesPerLine = ch * w
            convertToQtFormat = QImage(rgbImage.data, w, h, bytesPerLine, QImage.Format_RGB888)
            p = convertToQtFormat.scaled(256, 342, Qt.KeepAspectRatio)

            if i == 0:
                self.capImage_0.emit(p)
            elif i == 1:
                self.capImage_1.emit(p)
            elif i == 2:
                self.capImage_2.emit(p)
            elif i == 3:
                self.capImage_3.emit(p)
            elif i == 4:
                self.capImage_4.emit(p)
            elif i == 5:
                self.capImage_5.emit(p)

    @pyqtSlot(QImage)
    def setImage_0(self, image):
        self.label_form_0.setPixmap(QPixmap.fromImage(image))
    @pyqtSlot(QImage)
    def setImage_1(self, image):
        self.label_form_1.setPixmap(QPixmap.fromImage(image))
    @pyqtSlot(QImage)
    def setImage_2(self, image):
        self.label_form_2.setPixmap(QPixmap.fromImage(image))
    @pyqtSlot(QImage)
    def setImage_3(self, image):
        self.label_form_3.setPixmap(QPixmap.fromImage(image))
    @pyqtSlot(QImage)
    def setImage_4(self, image):
        self.label_form_4.setPixmap(QPixmap.fromImage(image))
    @pyqtSlot(QImage)
    def setImage_5(self, image):
        self.label_form_5.setPixmap(QPixmap.fromImage(image))
    
    @pyqtSlot(QImage)
    def setImage_6(self, image):
        self.label_form_6.setPixmap(QPixmap.fromImage(image))
    @pyqtSlot(QImage)
    def setImage_7(self, image):
        self.label_form_7.setPixmap(QPixmap.fromImage(image))
    @pyqtSlot(QImage)
    def setImage_8(self, image):
        self.label_form_8.setPixmap(QPixmap.fromImage(image))
    @pyqtSlot(QImage)
    def setImage_9(self, image):
        self.label_form_9.setPixmap(QPixmap.fromImage(image))

    def pushButton_form_3_Next_Func(self):
        nextCnt = 0

        for item in selected_captureList:
            if item != 0:
                nextCnt += 1

        if nextCnt == 2:
            form_4.setImageList()
            form_4.label.setText('printing')
            Print_Worker_Start(form_4)
            widget.setCurrentIndex(widget.currentIndex() + 1)

    def selected_cap_Func(self, index, i):
        img = cv2.imread(captureList[index], cv2.IMREAD_COLOR)
        rgbImage = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgbImage.shape
        bytesPerLine = ch * w
        convertToQtFormat = QImage(rgbImage.data, w, h, bytesPerLine, QImage.Format_RGB888)
        p = convertToQtFormat.scaled(278, 408, Qt.KeepAspectRatio)

        if i == 0:
            self.capImage_6.emit(p)
            self.capImage_7.emit(p)
        elif i == 1:
            self.capImage_8.emit(p)
            self.capImage_9.emit(p)

    def check_selected_cap_Func(self, index):
        if len(selected_captureList) < 3:
            if not captureList[index] in selected_captureList:
                if selected_captureList[0] == 0:
                    selected_captureList[0] = captureList[index]
                    self.selected_cap_Func(index, 0)

                elif selected_captureList[1] == 0:
                    selected_captureList[1] = captureList[index]
                    self.selected_cap_Func(index, 1)
            
    def check_remove_cap_Func(self, index):
        if index == 0:
            selected_captureList[0] = 0
            self.label_form_6.clear()
            self.label_form_7.clear()
        elif index == 1:
            selected_captureList[1] = 0
            self.label_form_8.clear()
            self.label_form_9.clear()

    def label_form_0_Func(self):  # Add
        self.check_selected_cap_Func(0)
    def label_form_1_Func(self):  # Add
        self.check_selected_cap_Func(1)
    def label_form_2_Func(self):  # Add
        self.check_selected_cap_Func(2)
    def label_form_3_Func(self):  # Add
        self.check_selected_cap_Func(3)
    def label_form_4_Func(self):  # Add
        self.check_selected_cap_Func(4)
    def label_form_5_Func(self):  # Add
        self.check_selected_cap_Func(5)

    def label_form_6_Func(self):  # Remove
        self.check_remove_cap_Func(0)
    def label_form_7_Func(self):  # Remove
        self.check_remove_cap_Func(1)

# endregion

# region [Form_4]
def Print_Worker_Start(self):
    if not self.print_worker.isRun:
        self.print_worker.isRun = True
        self.print_worker.start()

def Print_Worker_Stop(self):
    if self.print_worker.isRun:
        self.print_worker.isRun = False

class Print_Worker(QThread):
    def __init__(self, parent=None):
        super(Print_Worker, self).__init__(parent)
        self.isRun = False

    def run(self):
        try:
            while self.isRun:
                Print_Worker_Stop(self.parent())
                
                now = datetime.now()
                current_time = now.strftime('%Y_%m_%d_%H_%M_%S')
                savePath = '/home/test/Desktop/image_capture/' + str(now.date()) + '/' + current_time + '.jpg'
                screen = form_4.widget_test.grab()
                screen.save(savePath)
                
                cnt = int(form_1.printCount/2)
                
                for i in range(cnt):
                    time.sleep(2)
                    form_4.label.setText('printing')
                    
                    printer = QtPrintSupport.QPrinter()
                    painter = QtGui.QPainter()
                    
                    printer.setResolution(300)
                    # printer.setFullPage(True)
                    printer.setPageMargins(0, 0, 0, 0, QPrinter.Millimeter)
                    
                    painter.begin(printer)
                    painter.setRenderHint(QPainter.SmoothPixmapTransform)
                    painter.drawPixmap(17, 15, screen)
                    painter.end()
                
                    time.sleep(4)
                    form_4.label.setText('printing.')
                    time.sleep(4)
                    form_4.label.setText('printing..')
                    time.sleep(4)
                    form_4.label.setText('printing...')
                    time.sleep(4)
                    form_4.label.setText('printing....')
                    time.sleep(4)
                    form_4.label.setText('printing.....')
                    time.sleep(4)
                    
                # delete ...
                ### 초기화 구현 ###
                for del_file in captureList:
                    if os.path.exists(del_file):
                        os.remove(del_file)
                
                captureList.clear()

                selected_captureList[0] = 0

                form_1.widge_form_1_0.show()
                form_1.widge_form_1_1.hide()
                form_1.widge_form_1_2.hide()

                form_3.label_form_0.clear()
                form_3.label_form_1.clear()
                form_3.label_form_2.clear()
                form_3.label_form_3.clear()
                form_3.label_form_4.clear()
                form_3.label_form_5.clear()
                
                form_3.label_form_6.clear()
                form_3.label_form_7.clear()
                form_3.label_form_8.clear()
                form_3.label_form_9.clear()
                ### 초기화 구현 ###
            
                widget.setCurrentIndex(widget.currentIndex() - 3)

        except Exception as ex:
            print(ex)

            for del_file in captureList:
                if os.path.exists(del_file):
                    os.remove(del_file)

            captureList.clear()

            selected_captureList[0] = 0

            form_1.widge_form_1_0.show()
            form_1.widge_form_1_1.hide()
            form_1.widge_form_1_2.hide()

            form_3.label_form_0.clear()
            form_3.label_form_1.clear()
            form_3.label_form_2.clear()
            form_3.label_form_3.clear()
            form_3.label_form_4.clear()
            form_3.label_form_5.clear()
            
            form_3.label_form_6.clear()
            form_3.label_form_7.clear()
            form_3.label_form_8.clear()
            form_3.label_form_9.clear()

            widget.setCurrentIndex(widget.currentIndex() - 3)

class Form_4(QDialog, _form_4):
    capImage_0 = pyqtSignal(QImage)
    capImage_1 = pyqtSignal(QImage)
    capImage_2 = pyqtSignal(QImage)
    capImage_3 = pyqtSignal(QImage)

    def __init__(self):
        super(Form_4, self).__init__()
        self.setupUi(self)

        self.setStyleSheet("background-color: white;")
        
        self.widget_test.hide()

        self.capImage_0.connect(self.setImage_0)
        self.capImage_1.connect(self.setImage_1)
        self.capImage_2.connect(self.setImage_2)
        self.capImage_3.connect(self.setImage_3)
        
        self.print_worker = Print_Worker(parent=self)

    def setImageList(self):
        for i in range(0, 2):
            time.sleep(0.2)
            transform = QtGui.QTransform().rotate(270)
            pixmap = QPixmap(selected_captureList[i])
            pixmap = pixmap.transformed(transform, Qt.SmoothTransformation).scaled(542, 814, Qt.KeepAspectRatio)

            if i == 0:
                self.label_image_0.setPixmap(QPixmap(pixmap))
                self.label_image_1.setPixmap(QPixmap(pixmap))
            elif i == 1:
                self.label_image_2.setPixmap(QPixmap(pixmap))
                self.label_image_3.setPixmap(QPixmap(pixmap))

    @pyqtSlot(QImage)
    def setImage_0(self, image):
        self.label_image.setPixmap(QPixmap.fromImage(image))
    @pyqtSlot(QImage)
    def setImage_1(self, image):
        self.label_image_1.setPixmap(QPixmap.fromImage(image))
    @pyqtSlot(QImage)
    def setImage_2(self, image):
        self.label_image_2.setPixmap(QPixmap.fromImage(image))
    @pyqtSlot(QImage)
    def setImage_3(self, image):
        self.label_image_3.setPixmap(QPixmap.fromImage(image))

# endregion

# region [Main]
if __name__ == "__main__":
    # 화면 전환용 Widget 설정
    widget = QtWidgets.QStackedWidget()

    # 레이아웃 인스턴스 생성
    form_1 = Form_1()
    form_2 = Form_2()
    form_3 = Form_3()
    form_4 = Form_4()

    # Widget 추가
    widget.addWidget(form_1)
    widget.addWidget(form_2)
    widget.addWidget(form_3)
    widget.addWidget(form_4)

    # 프로그램 화면을 보여주는 코드
    widget.setFixedHeight(1080)
    widget.setFixedWidth(1920)
    widget.showFullScreen()
    widget.show()

    # 프로그램을 이벤트루프로 진입시키는(프로그램을 작동시키는) 코드
    app.exec_()
# endregiond
