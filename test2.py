from PyQt5 import QtGui, QtCore, QtWidgets, uic
from PyQt5.QtCore import pyqtSignal, pyqtSlot

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg,NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import numpy as np
class MplCanvas(FigureCanvasQTAgg):

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)


##
# The DetachableTabWidget adds additional functionality to Qt's QTabWidget that allows it
# to detach and re-attach tabs.
#
# Additional Features:
#   Detach tabs by
#     dragging the tabs away from the tab bar
#     double clicking the tab
#   Re-attach tabs by
#     closing the detached tab's window
#     double clicking the detached tab's window frame
#
# Modified Features:
#   Re-ordering (moving) tabs by dragging was re-implemented  
#   
class DetachableTabWidget(QtWidgets.QTabWidget):
    def __init__(self, parent=None,app=None):
        QtWidgets.QTabWidget.__init__(self, parent)

        self.tabBar = self.TabBar(self,app=app)
        self.tabBar.onDetachTabSignal.connect(self.detachTab)
        self.tabBar.onMoveTabSignal.connect(self.moveTab)

        self.setTabBar(self.tabBar)
        self.app = app
        self.plots = []

    ##
    #  The default movable functionality of QTabWidget must remain disabled
    #  so as not to conflict with the added features
    def setMovable(self, movable):
        pass

    ##
    #  Move a tab from one position (index) to another
    #
    #  @param    fromIndex    the original index location of the tab
    #  @param    toIndex      the new index location of the tab
    @pyqtSlot(int, int)
    def moveTab(self, fromIndex, toIndex):
        widget = self.widget(fromIndex)
        icon = self.tabIcon(fromIndex)
        text = self.tabText(fromIndex)

        self.removeTab(fromIndex)
        self.insertTab(toIndex, widget, icon, text)
        self.setCurrentIndex(toIndex)


    ##
    #  Detach the tab by removing it's contents and placing them in
    #  a DetachedTab dialog
    #
    #  @param    index    the index location of the tab to be detached
    #  @param    point    the screen position for creating the new DetachedTab dialog
    @pyqtSlot(int, QtCore.QPoint)
    def detachTab(self, index, point):

        # Get the tab content
        name = self.tabText(index)
        icon = self.tabIcon(index)        
        if icon.isNull():
            icon = self.window().windowIcon()              
        contentWidget = self.widget(index)
        contentWidgetRect = contentWidget.frameGeometry()

        # Create a new detached tab window
        detachedTab = self.DetachedTab(contentWidget, self.parentWidget(),app=self.app)
        detachedTab.setWindowModality(QtCore.Qt.NonModal)
        detachedTab.setWindowTitle(name)
        detachedTab.setWindowIcon(icon)
        detachedTab.setObjectName(name)
        detachedTab.setGeometry(contentWidgetRect)
        detachedTab.onCloseSignal.connect(self.attachTab)
        detachedTab.move(point)
        detachedTab.show()


    ##
    #  Re-attach the tab by removing the content from the DetachedTab dialog,
    #  closing it, and placing the content back into the DetachableTabWidget
    #
    #  @param    contentWidget    the content widget from the DetachedTab dialog
    #  @param    name             the name of the detached tab
    #  @param    icon             the window icon for the detached tab
    @pyqtSlot(QtWidgets.QWidget, str, QtGui.QIcon)
    def attachTab(self, contentWidget, name, icon):

        # Make the content widget a child of this widget
        contentWidget.setParent(self)


        # Create an image from the given icon
        if not icon.isNull():
            tabIconPixmap = icon.pixmap(icon.availableSizes()[0])
            tabIconImage = tabIconPixmap.toImage()
        else:
            tabIconImage = None


        # Create an image of the main window icon
        if not icon.isNull():
            windowIconPixmap = self.window().windowIcon().pixmap(icon.availableSizes()[0])
            windowIconImage = windowIconPixmap.toImage()
        else:
            windowIconImage = None


        # Determine if the given image and the main window icon are the same.
        # If they are, then do not add the icon to the tab
        if tabIconImage == windowIconImage:
            index = self.addTab(contentWidget, name)
        else:
            index = self.addTab(contentWidget, icon, name)


        # Make this tab the current tab
        if index > -1:
            self.setCurrentIndex(index)
    
    

    def addtab(self,*,tabName=None):
        if tabName is None:
            count = self.count()
            if count is False:
                count = 0
            tabName = 'Matplotlib Figure '+str(count)
        
        tab = QtWidgets.QWidget()
        self.addTab(tab, 'Temporary')
        
    
        layout = QtWidgets.QVBoxLayout()
        sc = MplCanvas(self.parent().tabWidget, width=5, height=4, dpi=100)
        sc.axes.plot(np.random.rand(10),np.random.rand(10))
        toolbar = NavigationToolbar(sc, None)
        layout.addWidget(toolbar)
        layout.addWidget(sc)
        self.plots.append(sc)

        self.setCurrentIndex(self.count()-1)
        
        self.setTabText(self.count()-1,tabName)
        tab.setLayout(layout)

    @pyqtSlot()
    def on_close_tab(self):
        if self.tabBar.count():
            idx = self.tabBar.currentIndex()
            self.removeTab(idx)    

    ##
    #  When a tab is detached, the contents are placed into this QDialog.  The tab
    #  can be re-attached by closing the dialog or by double clicking on its
    #  window frame.
    class DetachedTab(QtWidgets.QMainWindow):
        onCloseSignal = pyqtSignal(QtWidgets.QWidget, str, QtGui.QIcon)
        
        def __init__(self, contentWidget, parent=None,app=None):
            QtWidgets.QMainWindow.__init__(self, parent)

            
            centralWidget = QtWidgets.QWidget()
            self.setCentralWidget(centralWidget)
            
            self.setWindowFlag(QtCore.Qt.WindowMinimizeButtonHint, True)
            self.setWindowFlag(QtCore.Qt.WindowMaximizeButtonHint, True)

            
            layout = QtWidgets.QVBoxLayout(centralWidget)    
            centralWidget.setLayout(layout)        
            self.contentWidget = contentWidget            
            
            layout.addWidget(self.contentWidget)

            self.contentWidget.show()
            self.wasOutside = False
            
            self.app = app
            self.show()
            

        ##
        #  Capture a double click event on the dialog's window frame
        #
        #  @param    event    an event
        #
        #  @return            true if the event was recognized
        def event(self, event):

            # If the event type is QEvent.NonClientAreaMouseButtonDblClick then
            # close the dialog
            if event.type() == 176:
                event.accept()
                self.close()

            return QtWidgets.QDialog.event(self, event)


        ##
        #  If the dialog is closed, emit the onCloseSignal and give the
        #  content widget back to the DetachableTabWidget
        #
        #  @param    event    a close event
        def closeEvent(self, event):
            self.onCloseSignal.emit(self.contentWidget, self.objectName(), self.windowIcon())

        def moveEvent(self,event):
            pos = QtGui.QCursor.pos()
            if self.parent().geometry().contains(pos) and self.wasOutside:
                self.enterParent(event)
                
            else:
                self.wasOutside = True

        def enterParent(self,event):
            pixmap = QtGui.QScreen.grabWindow(self.app.primaryScreen(), 
                        self.winId())

            QtWidgets.QApplication.processEvents()
            self.close()
            QtWidgets.QApplication.processEvents()
            #self.parent().tabWidget.tabBar.dropEvent(event)
            #return None
            # Convert the move event into a drag
            drag = QtGui.QDrag(self)
            mimeData = QtCore.QMimeData()
            mimeData.setData('action', b'application/tab-attach')
            drag.setMimeData(mimeData)

            # Create the appearance of dragging the tab content
            
            tab = self.parent().tabWidget.tabBar.count()-1

            
            
            
            targetPixmap = QtGui.QPixmap(pixmap.size())
            targetPixmap.fill(QtCore.Qt.transparent)
            painter = QtGui.QPainter(targetPixmap)
            painter.setOpacity(0.85)
            painter.drawPixmap(0, 0, pixmap)
            painter.end()
            drag.setPixmap(targetPixmap)

            # Initiate the drag
            dropAction = drag.exec_(QtCore.Qt.MoveAction | QtCore.Qt.CopyAction)
            obj = self.parent().tabWidget.tabBar
            # If the drag completed outside of the tab bar, detach the tab and move
            # the content to the current cursor position

            
            
            if dropAction == QtCore.Qt.IgnoreAction and not self.parent().geometry().contains(obj.mouseCursor.pos()):
                event.accept()
                event.wasOutside=True
                
                obj.onDetachTabSignal.emit(tab, obj.mouseCursor.pos())

            # Else if the drag completed inside the tab bar, move the selected tab to the new position
            elif dropAction == QtCore.Qt.MoveAction:
                if not self.dragDropedPos.isNull():
                    event.accept()
                    obj.onMoveTabSignal.emit(tab, obj.tabAt(self.dragDropedPos))




    ##
    #  The TabBar class re-implements some of the functionality of the QTabBar widget
    class TabBar(QtWidgets.QTabBar):
        onDetachTabSignal = pyqtSignal(int, QtCore.QPoint)
        onMoveTabSignal = pyqtSignal(int, int)
        

        def __init__(self, parent=None,app=None):
            QtWidgets.QTabBar.__init__(self, parent)

            self.setMovable(True)
            self.setAcceptDrops(True)
            self.setTabsClosable(True)
            self.setElideMode(QtCore.Qt.ElideRight)
            self.setSelectionBehaviorOnRemove(QtWidgets.QTabBar.SelectLeftTab)


            self.dragStartPos = QtCore.QPoint()
            self.dragDropedPos = QtCore.QPoint()
            self.mouseCursor = QtGui.QCursor()
            self.dragInitiated = False
            self.wasOutside = False

            self.app = app


        ##
        #  Send the onDetachTabSignal when a tab is double clicked
        #
        #  @param    event    a mouse double click event
        def mouseDoubleClickEvent(self, event):
            event.accept()
            self.onDetachTabSignal.emit(self.tabAt(event.pos()), self.mouseCursor.pos())


        ##
        #  Set the starting position for a drag event when the mouse button is pressed
        #
        #  @param    event    a mouse press event
        def mousePressEvent(self, event):
            if event.button() == QtCore.Qt.LeftButton:
                self.dragStartPos = event.pos()

            self.dragDropedPos.setX(0)
            self.dragDropedPos.setY(0)

            self.dragInitiated = False
            
            QtWidgets.QTabBar.mousePressEvent(self, event)

        
        ##
        #  Determine if the current movement is a drag.  If it is, convert it into a QDrag.  If the
        #  drag ends inside the tab bar, emit an onMoveTabSignal.  If the drag ends outside the tab
        #  bar, emit an onDetachTabSignal.
        #
        #  @param    event    a mouse move event
        def mouseMoveEvent(self, event):
            #return QtWidgets.QTabBar.mouseMoveEvent(self,event)

            # Determine if the current movement is detected as a drag
            if not self.dragStartPos.isNull() and ((event.pos() - self.dragStartPos).manhattanLength() < QtWidgets.QApplication.startDragDistance()):
                self.dragInitiated = True

            
            
            # If the current movement is a drag initiated by the left button
            if (((event.buttons() & QtCore.Qt.LeftButton)) and self.dragInitiated):
                
                # Stop the move event
                finishMoveEvent = QtGui.QMouseEvent(QtCore.QEvent.MouseMove, event.pos(), QtCore.Qt.NoButton, QtCore.Qt.NoButton, QtCore.Qt.NoModifier)
                QtWidgets.QTabBar.mouseMoveEvent(self, finishMoveEvent)

                # Convert the move event into a drag
                drag = QtGui.QDrag(self)
                mimeData = QtCore.QMimeData()
                mimeData.setData('action', b'application/tab-detach')
                drag.setMimeData(mimeData)

                # Create the appearance of dragging the tab content

                pixmap = QtGui.QScreen.grabWindow(self.app.primaryScreen(), 
                            self.parent().widget(0).winId())
                targetPixmap = QtGui.QPixmap(pixmap.size())
                targetPixmap.fill(QtCore.Qt.transparent)
                painter = QtGui.QPainter(targetPixmap)
                painter.setOpacity(0.85)
                painter.drawPixmap(0, 0, pixmap)
                painter.end()
                drag.setPixmap(targetPixmap)

                # Initiate the drag
                dropAction = drag.exec_(QtCore.Qt.MoveAction | QtCore.Qt.CopyAction)

                # If the drag completed outside of the tab bar, detach the tab and move
                # the content to the current cursor position
                
                if dropAction == QtCore.Qt.IgnoreAction and not self.parent().parent().geometry().contains(self.mouseCursor.pos()):
                    
                    event.accept()
                    self.onDetachTabSignal.emit(self.tabAt(self.dragStartPos), self.mouseCursor.pos())

                # Else if the drag completed inside the tab bar, move the selected tab to the new position
                elif dropAction == QtCore.Qt.MoveAction:
                    
                    if not self.dragDropedPos.isNull():
                        event.accept()
                        self.onMoveTabSignal.emit(self.tabAt(self.dragStartPos), self.tabAt(self.dragDropedPos))
            else:
                QtWidgets.QTabBar.mouseMoveEvent(self, event)


        ##
        #  Determine if the drag has entered a tab position from another tab position
        #
        #  @param    event    a drag enter event
        def dragEnterEvent(self, event):
            mimeData = event.mimeData()
            formats = mimeData.formats()
            
            if 'action' in formats and mimeData.data('action') == b'application/tab-detach':
                event.acceptProposedAction()
                

            QtWidgets.QTabBar.dragMoveEvent(self, event)


        ##
        #  Get the position of the end of the drag
        #
        #  @param    event    a drop event
        def dropEvent(self, event):
            self.dragDropedPos = event.pos()
            QtWidgets.QTabBar.dropEvent(self, event)


MainBase, MainForm = uic.loadUiType("/home/lass/Dropbox/PhD/Software/GuiMatplotlib/src/main/python/Main.ui")
class MainWindow(MainBase, MainForm):

    def __init__(self, app, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.app = app
        self.setupUi(self)

        self.tabWidget = DetachableTabWidget(self,app = app)
        self.tabWidget.tabCloseRequested.connect(lambda index: self.tabWidget.removeTab(index))

        self.shortcut = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+W"), self, self.tabWidget.on_close_tab)

        self.actionPlot_Random.triggered.connect(self.tabWidget.addtab)

        
        self.tabWidget.show()
        self.setCentralWidget(self.tabWidget)
        self.show()
        

        

if __name__ == '__main__':
    import sys
    from os import path

    

    app = QtWidgets.QApplication(sys.argv)

    mainWindow = MainWindow(app)
    
    

    try:
        exitStatus = app.exec_()
        print('Done...')
        sys.exit(exitStatus)
    except:
        pass