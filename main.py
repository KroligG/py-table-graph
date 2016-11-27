import json
import math
import statistics
import sys

from PyQt5 import QtCore
from PyQt5.QtChart import QLineSeries
from PyQt5.QtCore import QPointF, QLocale
from PyQt5.QtCore import QSize
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QAction, QSlider, QLabel, QDoubleSpinBox, QMessageBox
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QGridLayout
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtWidgets import QWidget, QApplication

import MyQtChart
import MyQtTable


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        cw = CentralWidget(self)
        self.setCentralWidget(cw)

        exitAction = QAction('&Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(self.close)

        openFile = QAction('Open', self)
        openFile.setShortcut('Ctrl+O')
        openFile.setStatusTip('Open Data File')
        openFile.triggered.connect(self.openDataFile)

        saveFile = QAction('Save', self)
        saveFile.setShortcut('Ctrl+S')
        saveFile.setStatusTip('Save Data File')
        saveFile.triggered.connect(self.saveDataFile)

        self.statusBar().showMessage('Ready. Please load data file or enter values manually')

        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(openFile)
        fileMenu.addAction(saveFile)
        fileMenu.addAction(exitAction)

        # self.setGeometry(300, 300, 250, 150)
        self.setWindowTitle('Table plot charter')
        self.show()

    def openDataFile(self):
        fname = QFileDialog.getOpenFileName(self, 'Open file', filter='*.json;;*')

        if fname[0]:
            with open(fname[0], 'r') as f:
                data = json.loads(f.read())
            self.centralWidget().table.update_table(data)
            self.statusBar().showMessage('Data loaded. Note that you can move and resize the chart using mouse')

    def saveDataFile(self):
        fname = QFileDialog.getSaveFileName(self, 'Save file', filter='*.json')

        if fname[0]:
            with open(fname[0], 'w') as f:
                json.dump(self.centralWidget().table.get_table_data(), f)
            self.statusBar().showMessage('File was saved successfully')

    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Confirm', "Are you sure to quit?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            self.close()


class CentralWidget(QWidget):
    repaintChartEvent = QtCore.pyqtSignal()

    def __init__(self, window):
        super().__init__()

        self.windowWidget = window

        self.repaintChartEvent.connect(self.repaint_chart)

        self.lambda_value = 0.2
        self.beta_value = 3
        self.mu_value = 0.8

        grid = QGridLayout()
        self.setLayout(grid)

        self.table = MyQtTable.MyQtTable(1, 1)
        self.table.setFixedWidth(150)
        grid.addWidget(self.table, 1, 0, -1, 1)

        series = QLineSeries()
        series.setName("Values time series")

        self.chart_view = MyQtChart.MyChartView(series, "Chart", "Time", "Value", minimumSize=QSize(800, 650))
        grid.addWidget(self.chart_view, 2, 1, 1, -1)

        self.table.newTableDataEvent.connect(self.update_chart)

        lambdaValueLabel = QLabel("λ=%.2f" % self.lambda_value)
        grid.addWidget(lambdaValueLabel, 1, 1)
        self.lambdaValueLabel = lambdaValueLabel

        qslider = QSlider(Qt.Horizontal)
        qslider.setMinimum(0)
        qslider.setMaximum(100)
        qslider.setValue(self.lambda_value * 100)
        qslider.valueChanged.connect(self.on_lambda_changed)
        qslider.sliderMoved.connect(lambda v: lambdaValueLabel.setText("λ=%.2f" % (v / 100)))
        qslider.setTracking(False)
        grid.addWidget(qslider, 1, 2)

        grid.addWidget(QLabel("μ="), 1, 3)
        muEdit = QDoubleSpinBox()
        muEdit.setValue(self.mu_value)
        muEdit.setSingleStep(0.1)
        grid.addWidget(muEdit, 1, 4)
        muEdit.valueChanged.connect(self.on_mu_changed)

        grid.addWidget(QLabel("β="), 1, 5)
        betaEdit = QDoubleSpinBox()
        betaEdit.setValue(self.beta_value)
        betaEdit.setSingleStep(0.1)
        grid.addWidget(betaEdit, 1, 6)
        betaEdit.valueChanged.connect(self.on_beta_changed)

        # self.table.update_table(json.load(open('data.json')))

    def on_lambda_changed(self, v):
        self.lambda_value = v / 100
        self.lambdaValueLabel.setText("λ=%.2f" % self.lambda_value)
        self.repaintChartEvent.emit()

    def on_mu_changed(self, v):
        if v:
            self.mu_value = float(v)
            self.repaintChartEvent.emit()

    def on_beta_changed(self, v):
        if v:
            self.beta_value = v
            self.repaintChartEvent.emit()

    def repaint_chart(self):
        self.update_chart(self.table.get_table_data())

    def update_chart(self, points):
        if len(points) < 2: return

        series = QLineSeries()
        series.setName("Values")
        series.append([QPointF(p[0], p[1]) for p in points])
        self.chart_view.set_series(series)

        lam = self.lambda_value

        ewmaSeries = QLineSeries()
        ewmaSeries.setName("EWMA")
        x_list = list(zip(*points))[1]
        ewma = [statistics.mean(x_list)]
        for (i, p) in enumerate(points):
            ewma.append(lam * p[1] + (1 - lam) * ewma[-1])
            ewmaSeries.append(QPointF(p[0], ewma[-1]))
        self.chart_view.add_series(ewmaSeries)

        beta = self.beta_value
        mu = self.mu_value
        stdev = statistics.stdev(x_list)
        lclSeries = QLineSeries()
        lclSeries.setName("LCL")
        for (i, x) in points:
            lclSeries.append(QPointF(i, mu - beta * stdev * math.sqrt(lam / (2 - lam) * (1 - (1 - lam) ** (2 * i)))))
        self.chart_view.add_series(lclSeries)


if __name__ == '__main__':
    QLocale.setDefault(QLocale("en-US"))
    app = QApplication(sys.argv)
    ex = MainWindow()
    sys.exit(app.exec_())
