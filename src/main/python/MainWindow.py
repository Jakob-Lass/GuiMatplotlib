import sys
import matplotlib
matplotlib.use('Qt5Agg')

from PyQt5 import QtCore, QtWidgets,uic
from PyQt5.QtWidgets import QTabWidget,QWidget
import numpy as np

from os import path

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg,NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

MainBase, MainForm = uic.loadUiType(path.join(path.dirname(__file__),"Main.ui"))

class MplCanvas(FigureCanvasQTAgg):

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)

class Main(MainBase, MainForm):
    def __init__(self, parent=None, guiWindow=None):
        super(Main, self).__init__(parent)
        self.setupUi(self)

class MainWindow(MainBase, MainForm):

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        self.setupUi(self)
        

        self._graphs = []
        self.tabs = []
        self.tabWidget = QTabWidget()
        
        # Create the maptlotlib FigureCanvas object, 
        # which defines a single set of axes as self.axes.
        
        self.plot()
        

        toolbar = NavigationToolbar(self.graphs[0], self)
        self.toolbar = toolbar
        
        self.mainLayout.addWidget(self.toolbar)
        
        self.mainLayout.addWidget(self.tabWidget)
        
        self.actionPlot_Random.triggered.connect(self.plot)

        self.show()

    @property
    def graphs(self):
        return self._graphs

    @graphs.getter
    def graphs(self):
        return self._graphs

    def graphAdder(self,graph):
        self.graphs.append(graph)
        tab = QWidget()
        self.tabs.append(tab)
        tab.addWidget(graph)
        name = 'Plot {}'.format(len(self.graphs)+1)
        
        self.tabWidget.addTab(tab,name)
        print(tab,name)


    def plot(self):
        self.generateRandomGraph()
        print('Graphs: ',len(self.graphs))
        print('Tabs: ',len(self.tabs))


    def generateRandomGraph(self):
        sc = MplCanvas(self, width=5, height=4, dpi=100)
        sc.axes.plot(np.random.rand(10),np.random.rand(10))
        print('Random figure coming up!')
        self.graphAdder(sc)

        
        
