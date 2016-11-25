from PyQt5.QtChart import QChart
from PyQt5.QtChart import QChartView
from PyQt5.QtChart import QLineSeries
from PyQt5.QtChart import QValueAxis
from PyQt5.QtCore import QPoint
from PyQt5.QtCore import QSize
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QWheelEvent


class MyChartView(QChartView):
    def __init__(self, series: QLineSeries, title: str, xTitle: str, yTitle: str,
                 minimumSize=QSize(400, 400), *args):
        super().__init__(*args)

        chart = QChart()
        chart.setTitle(title)

        axisX = QValueAxis(chart)
        axisX.setTitleText(xTitle)
        chart.setAxisX(axisX)

        axisY = QValueAxis(chart)
        axisY.setTitleText(yTitle)
        chart.setAxisY(axisY)

        chart.legend().show()
        chart.legend().setAlignment(Qt.AlignBottom)

        self.setChart(chart)

        self.set_series(series)

        self.setMinimumSize(minimumSize)
        self.setRenderHint(QPainter.Antialiasing)

        self.pan = Pan(self)

    def set_series(self, series: QLineSeries):
        self.chart().removeAllSeries()

        if not series or len(series) == 0:
            return

        self.chart().addSeries(series)
        series.setPointLabelsClipping(False)
        series.hovered.connect(lambda p, s: series.setPointLabelsVisible(s))

        x_y_points = list(zip(*((e.x(), e.y()) for e in series.pointsVector())))

        axisX = self.chart().axisX()
        axisX.setRange(min(x_y_points[0]), max(x_y_points[0]))
        axisX.setMinorTickCount(1)
        axisX.setTickCount(10)
        axisX.applyNiceNumbers()
        self.chart().setAxisX(axisX, series)

        axisY = self.chart().axisY()
        axisY.setRange(min(x_y_points[1]), max(x_y_points[1]))
        axisY.setTickCount(18)
        axisY.applyNiceNumbers()
        self.chart().setAxisY(axisY, series)

    def add_series(self, series: QLineSeries):
        self.chart().addSeries(series)
        series.setPointLabelsClipping(False)
        series.hovered.connect(lambda p, s: series.setPointLabelsVisible(s))

        self.chart().setAxisX(self.chart().axisX(), series)
        self.chart().setAxisY(self.chart().axisY(), series)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.pan.start(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.pan.end(event)

    def mouseMoveEvent(self, event):
        if self.pan.active:
            dist = self.pan.move(event)
            self.chart().scroll(dist.x(), -dist.y())
            # axis_x = self.chart().axisX()
            # axis_y = self.chart().axisY()
            # axis_x.setRange(axis_x.min() + dist.x(), axis_x.max() + dist.x())
            # axis_y.setRange(axis_y.min() - dist.y(), axis_y.max() - dist.y())
        else:
            super().mouseMoveEvent(event)

    def wheelEvent(self, event: QWheelEvent):
        if event.angleDelta().y() > 0:
            self.chart().zoomIn()
        else:
            self.chart().zoomOut()

    def keyPressEvent(self, event):
        {
            Qt.Key_Plus: lambda e: self.chart().zoomIn(),
            Qt.Key_Minus: lambda e: self.chart().zoomOut(),
            Qt.Key_Left: lambda e: self.chart().scroll(-10, 0),
            Qt.Key_Right: lambda e: self.chart().scroll(10, 0),
            Qt.Key_Up: lambda e: self.chart().scroll(0, 10),
            Qt.Key_Down: lambda e: self.chart().scroll(0, -10)
        }.get(event.key(), super().keyPressEvent)(event)


class Pan:
    def __init__(self, widget):
        self.active = False
        self.startX = 0
        self.startY = 0
        self.widget = widget

    def start(self, event):
        self.active = True
        self.startX = event.x()
        self.startY = event.y()
        self.widget.setCursor(Qt.ClosedHandCursor)

    def move(self, event):
        dist = QPoint(self.startX - event.x(), self.startY - event.y())
        self.startX = event.x()
        self.startY = event.y()
        return dist

    def end(self, event):
        self.active = False
        self.widget.setCursor(Qt.ArrowCursor)
