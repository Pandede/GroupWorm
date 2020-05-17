# -*- coding: utf-8 -*-
"""
Created on Wed Apr 15 15:45:42 2020

@author: Chan Chak Tong
"""

import sys
import os
from PyQt5.QtWidgets import QMainWindow, QApplication, QDialog, QMessageBox, QTableWidgetItem
from PyQt5.QtCore import QTimer

from worm import WormThread
from gui import Ui_MainWindow, Ui_SettingDialog, Ui_LoginDialog

class MsgboxBuilder: 
    @classmethod
    def critical(self, msg):
        self.__build_msgbox(self, QMessageBox.Critical, msg)
    
    @classmethod
    def warning(self, msg):
        self.__build_msgbox(self, QMessageBox.Warning, msg)
    
    def __build_msgbox(self, msg_type, msg):
        msgbox = QMessageBox()
        msgbox.setWindowTitle('Error')
        msgbox.setIcon(msg_type)
        msgbox.setText(msg)
        msgbox.setStandardButtons(QMessageBox.Ok)
        msgbox.setDefaultButton(QMessageBox.Ok)
        msgbox.exec_()
        
class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.group_id, self.keywords = self.load_meta()
        self.setupUi(self)
        self.start_button.clicked.connect(self.start)
        self.stop_button.clicked.connect(self.stop)
        
    def __check_validity(self):
        if self.top.isnumeric() and self.scroll_times.isnumeric() and self.freq.isnumeric() and int(self.top) > 0 and int(self.scroll_times) > 0 and int(self.freq) > 0:
            return True
        return False
    
    def __update_view(self, records):
        for record_time, feed_id, link in records:
            row_count = self.detail_view.rowCount()
            self.detail_view.insertRow(row_count)
            self.detail_view.setItem(row_count, 0, QTableWidgetItem(record_time))
            self.detail_view.setItem(row_count, 1, QTableWidgetItem(feed_id))
            self.detail_view.setItem(row_count, 2, QTableWidgetItem(link))
    
    def __update_status(self, status):
        self.progress_label.setText('Listening... (%d/%d)' % (status['matched_cases'], status['total_cases']))
        
        self.counter = self.freq
        if hasattr(self, 'timer'):
            self.timer.stop()
        else:
            self.timer = QTimer(self)
            self.timer.timeout.connect(self.__update_timer)
        self.timer.start(1000)
        
    def __update_timer(self):
        self.seconds_label.setText(str(self.counter))
        self.counter = max(self.counter - 1, 0)
      
    def load_meta(self, path='./config.ini'):
        setting_dialog = SettingDialog()
        if os.path.isfile(path):
            with open(path) as config:
                group_id = config.readline()
                keywords = config.readline()
        else:   
            if setting_dialog.exec_():
                group_id, keywords = setting_dialog.fetch()
            else:
                sys.exit(0)
        
        group_id = group_id.strip()
        invalid_char = (', ', ' ,', ' , ')
        valid_char = ','
        for c in invalid_char:
            keywords = keywords.replace(c, valid_char)
        keywords = keywords.split(valid_char)
        return group_id, keywords
            
    def start(self):
        login_dialog = LoginDialog()
        if login_dialog.exec_():
            username, password = login_dialog.fetch()
        else:
            return
        
        self.top = self.top_k_text.text()
        self.scroll_times = self.scroll_time_text.text()
        self.freq = self.freq_text.text()
        
        if self.__check_validity():
            self.start_button.setEnabled(False)
            QApplication.processEvents()
            self.start_button.hide()
            self.stop_button.setEnabled(True)
            self.stop_button.show()
            
            self.top = int(self.top)
            self.scroll_times = int(self.scroll_times)
            self.freq = int(self.freq)
            
            try:
                self.worm = WormThread(username, password)
                self.worm.record_signal.connect(self.__update_view)
                self.worm.status_signal.connect(self.__update_status)
                self.progress_label.setText('Locating...')
                QApplication.processEvents()
                self.worm.locate(r'https://www.facebook.com/groups/%s/' % self.group_id)
                self.progress_label.setText('Listening...')
                QApplication.processEvents()
                self.worm.listen(self.keywords, 
                                 top=self.top, 
                                 scroll_times=self.scroll_times,
                                 freq=self.freq)
            except:
                self.stop()
        else:
            MsgboxBuilder.critical('Invalid entries')
    
    def stop(self):
        self.stop_button.setEnabled(False)
        QApplication.processEvents()
        self.stop_button.hide()
        self.start_button.setEnabled(True)
        self.start_button.show()
        self.seconds_label.setText('0')
        
        if hasattr(self, 'timer'): self.timer.stop()
        self.progress_label.setText('Closing...')
        QApplication.processEvents()
        self.worm.stop()
        self.progress_label.setText('Ready')
        
                   
class SettingDialog(QDialog, Ui_SettingDialog):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        
    def __check_validity(self):
        if self.group_id == '' or self.keywords == '':
            MsgboxBuilder.critical('Group ID or Keywords cannot be empty')
            return False
        return True
            
    def accept(self):
        self.group_id = self.group_id_text.toPlainText()
        self.keywords = self.keywords_text.toPlainText()
        if self.__check_validity():
            super().accept()
        
    def fetch(self):
        return self.group_id, self.keywords

class LoginDialog(QDialog, Ui_LoginDialog):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
    
    def __check_validity(self):
        if self.username == '' or self.password == '':
            MsgboxBuilder.critical('Username or password cannot be empty')
            return False
        return True
    
    def accept(self):
        self.username = self.username_text.text()
        self.password = self.password_text.text()
        if self.__check_validity():
            super().accept()
            
    def fetch(self):
        return self.username, self.password

app = QApplication(sys.argv)
main_window = MainWindow()
main_window.show()
sys.exit(app.exec_())