import os
import re
import sqlite3
import sys
from urllib.request import urlopen

from PyQt5 import QtGui, QtCore, QtWidgets
import PyQt5
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtWidgets import QLabel, QLineEdit, QPushButton, \
    QGridLayout, QCheckBox, QApplication, QWidget, QComboBox, QMessageBox
from bs4 import BeautifulSoup
import requests


class GUI(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.username_label = QLabel('　　用户名')
        self.username_combo = QComboBox()
        self.username_combo.setEditable(True)
        self.password_label = QLabel('　　密　码')
        self.password_lineedit = QLineEdit()
        self.password_lineedit.setEchoMode(QLineEdit.Password)

        self.usedTraffic_label = QLabel('　　已使用')
        self.usedTraffic_lineedit = QLineEdit()
        self.balance_label = QLabel('　　余　额')
        self.balance_lineedit = QLineEdit()

        self.autologin = QCheckBox('自动登录')
        self.remember = QCheckBox('记住密码')
        self.remember.setChecked(True)
        self.login_button = QPushButton('登录')
        self.timer = QTimer()
        self.warning = 0

        layout = QGridLayout()
        layout.addWidget(self.username_label, 0, 0, 1, 1)
        layout.addWidget(self.username_combo, 0, 1, 1, 1)
        layout.addWidget(self.password_label, 1, 0, 1, 1)
        layout.addWidget(self.password_lineedit, 1, 1, 1, 1)
        layout.addWidget(self.usedTraffic_label, 2, 0, 1, 1)
        layout.addWidget(self.usedTraffic_lineedit, 2, 1, 1, 1)
        layout.addWidget(self.balance_label, 3, 0, 1, 1)
        layout.addWidget(self.balance_lineedit, 3, 1, 1, 1)
        layout.addWidget(self.autologin, 4, 0, 1, 1)
        layout.addWidget(self.remember, 4, 1, 1, 1, Qt.AlignRight)
        layout.addWidget(self.login_button, 5, 1, 1, 1)
#         layout.addWidget(self.status_label, 5, 0, 1, 2)

        self.setLayout(layout)
        self.setWindowTitle('自动登录')
        self.setWindowIcon(QIcon('./bupt-logo.jpg'))
        self.setFont(QFont('Adobe 黑体 Std R', 12))

        self.login_button.clicked.connect(self.onButtonClicked)
        self.username_combo.currentIndexChanged.connect(self.username_changed)
        self.timer.timeout.connect(self.getInfo)  # 定时发送

        self.login_url = 'http://gw.bupt.edu.cn'
        self.logout_url = 'http://gw.bupt.edu.cn/F.htm'

        self.login_status = False
        self.bsObj = None
        self.db = 'byrlogin.db'

        self.initSql()
        self.getStatus()

    def initSql(self):
        print('Init database')
        if os.path.exists(self.db):
            self.conn = sqlite3.connect('byrlogin.db')
            self.curs = self.conn.cursor()
        else:
            self.conn = sqlite3.connect('byrlogin.db')
            self.curs = self.conn.cursor()
            self.curs.execute('''CREATE TABLE login_data
                (username VARCHAR(20) PRIMARY KEY,
                password VARCHAR(20));       
                ''')
        self.curs.execute('SELECT username, password from login_data;')
        self.database = self.curs.fetchall()
        self.username_combo.addItems([item[0] for item in self.database])
        self.curs.close()
        self.conn.close()

    def getStatus(self):
        html = urlopen(self.login_url)
        self.bsObj = BeautifulSoup(html.read(), 'lxml')
        title = self.bsObj.title.text
        if title == '欢迎登录北邮校园网络':
            self.login_status = False
            self.setWindowTitle('未登录')
            self.login_button.setText('登录')

        elif title == '上网注销窗':
            self.login_status = True
            self.setWindowTitle('已登录')
            self.login_button.setText('注销')
            self.timer.start(60000)

        self.getInfo()

    def onButtonClicked(self):
        if self.login_status == False:
            self.login()
            self.getInfo()
        else:
            self.logout()

    def username_changed(self):
        for item in self.database:
            if self.username_combo.currentText() in item:
                self.password_lineedit.setText(item[1])
                return

    def login(self):
        username = self.username_combo.currentText().strip()
        password = self.password_lineedit.text().strip()

        if len(username) != 10 or not username.isdigit():
            self.username_combo.setCurrentText('')
            self.username_combo.setCurrentText('错误: ID应为10位数字,请重新输入')
            return
        elif len(password) == 0:
            self.password_lineedit.setText('错误: 请输入密码')
            return

        print(username, password)

        self.conn = sqlite3.connect('byrlogin.db')
        self.curs = self.conn.cursor()

        if self.remember.isChecked():

            for item in self.database:
                if username in item:
                    sql = 'UPDATE login_data SET password = ? WHERE username = ?;'
                    break
            else:
                sql = 'INSERT INTO login_data (password, username) VALUES (?, ?);'

            print(sql)
            try:
                self.curs.execute(sql, (password, username))
                self.conn.commit()
            except:
                return

        self.curs.execute('SELECT username, password from login_data;')
        self.database = self.curs.fetchall()
        print(self.database)
        self.curs.close()
        self.conn.close()

        login_form = {'DDDDD': username, 'upass': password, '0MKKey': ''}
        s = requests.Session()
        s.post(self.login_url, login_form)
        self.login_button.setText('注销')
        self.setWindowTitle('已登录')
        self.login_status = True

    def logout(self):
        s = requests.Session()
        s.get(self.logout_url)
        self.login_button.setText('登录')
        self.setWindowTitle('请登录')
        self.login_status = False
        self.timer.stop()

    def getInfo(self):
        try:
            html = urlopen(self.login_url)
        except:
            return
        self.bsObj = BeautifulSoup(html.read(), 'lxml')

        pattern = re.compile(r'flow=\'(.*?)\';.*?fee=\'(.*?)\';')

        if self.login_status == True:
            self.setWindowTitle('已登录')
            self.login_button.setText('注销')

            script = self.bsObj.head.script.text
            results = pattern.findall(script)
            self.usedTraffic = str(
                round(int(results[0][0].strip()) / 1024 / 1024, 3)) + ' GB'
            balance = str(round(int(results[0][1].strip()) / 10000, 2)) + ' 元'

            self.usedTraffic_lineedit.setText(self.usedTraffic)
            self.balance_lineedit.setText(balance)
        else:
            self.setWindowTitle('请登录')
            self.login_button.setText('登录')
            self.usedTraffic_lineedit.setText('')
            self.balance_lineedit.setText('')

    def timeout(self):
        self.getInfo()
        if self.usedTraffic >= 20 and self.warning == 0:
            self.logout()
            QMessageBox.warning(self, '警告', '流量即将用完')
            self.warning = 1

if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = GUI()
    win.show()
    app.exec_()
    app.exit()
