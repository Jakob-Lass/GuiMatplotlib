from PyQt5 import QtGui, QtCore, QtWidgets, uic
from PyQt5.QtCore import pyqtSignal, pyqtSlot

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg,NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import numpy as np

from os import path


class Mpltab(QtWidgets.QWidget):
    """ Widget to keep track of mpl figure in tab"""
    def __init__(self,MplCanvas, plotId, tabId, mainWindow, parent=None, toolbar=True, docked=True, dockingIcon=None, unDockingIcon=None):
        super().__init__(parent=parent)

        # Save both plotId and tabId
        self.plotId = plotId
        self.tabId = tabId

        # If docked, as standard the Mpltab is created as docked in a DetachableTabWidget
        self.docked=docked
        self.mainWindow = mainWindow

        self.layout = QtWidgets.QVBoxLayout()
        self.layout.setContentsMargins(0,0,0,0) # Remove border around layout

        self.dockingIcon = dockingIcon
        self.unDockingIcon = unDockingIcon
        
        if toolbar: # If a toolbar is wanted, create it, otherwise create menubar above figure
            self.menubar = NavigationToolbar(MplCanvas, None)
        else:
            self.menubar = QtWidgets.QMenuBar(self)
            self.menubar.setFixedHeight(25)

        # ad menubar and canvas to layout
        self.layout.addWidget(self.menubar)
        self.layout.addWidget(MplCanvas)
        if not self.dockingIcon is None and not self.unDockingIcon is None:
            self.dockAction = QtWidgets.QAction(self.unDockingIcon,'Undock',self.menubar)
        else:
            self.dockAction = QtWidgets.QAction('Undock',self.menubar)
        
        if not self.docked: # start undocked
            self.undock(parent=self.parent)

        self.setLayout(self.layout)

        # Add shortcut to dock
        self.dockAction.setShortcut("Ctrl+D")
        self.menubar.addAction(self.dockAction)
        self.dockAction.triggered.connect(self.toggleDocked)

    def toggleDocked(self):
        if self.docked:
            self.parent().parent().detachTab(index=self.tabId,point=QtGui.QCursor().pos())
        else:
            parent = self.parent()
            parent.dock()#attachTab(parent.contentWidget, parent.objectName(), parent.windowIcon())
            


    def undock(self,newParent):
        self.docked = False
        self.dockAction.setText('Dock')
        if not self.dockingIcon is None and not self.unDockingIcon is None:
            self.dockAction.setIcon(self.dockingIcon)
        self.setParent(newParent)
        

    def dock(self,newParent):
        self.docked = True
        self.dockAction.setText('Undock')
        if not self.dockingIcon is None and not self.unDockingIcon is None:
            self.dockAction.setIcon(self.unDockingIcon)
        self.setParent(newParent)


class MplCanvas(FigureCanvasQTAgg):
    """Simple Matplotlib class"""
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        super(MplCanvas, self).__init__(self.fig)

    # Upon deletion, also close the figure
    def __del__(self):
        plt.close(self.fig)


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

        self.old_removeTab = lambda index: QtWidgets.QTabWidget.removeTab(self,index)

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
        contentWidget.undock(newParent=detachedTab)
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
        #contentWidget.setParent(self)
        contentWidget.dock(newParent=self)

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
        """Add matplotlibtab to DetachableTabWidget"""
        
        # If no name, generate one
        if tabName is None:
            count = self.count()
            if count is False:
                count = 0
            tabName = 'Matplotlib Figure '+str(count)
        
        # Create the MPL object
        sc = MplCanvas(self.parent().tabWidget, width=5, height=4, dpi=100)
        # Create a random plot
        sc.axes.plot(np.random.rand(10),np.random.rand(10))

        # plotId is simply the next index in self.plots
        plotId = len(self.plots)

        # Create icons for docking/undocking
        dockingIcon = QtGui.QIcon()
        dockingIcon.addPixmap(QtGui.QPixmap(self.app.AppContext.get_resource('icons/dock.png')))
        
        unDockingIcon = QtGui.QIcon()
        unDockingIcon.addPixmap(QtGui.QPixmap(self.app.AppContext.get_resource('icons/undock.png')))
        
        # Create Mpltab
        tab = Mpltab(MplCanvas=sc,plotId=plotId,tabId=self.count(),parent=self, docked=True, mainWindow = self.parent(),\
            dockingIcon=dockingIcon,unDockingIcon=unDockingIcon)
        
        # add the tab with temporary name (used in debugging to signify an error)
        self.addTab(tab, 'Temporary')
        # Add plot to list of plots
        self.plots.append(sc)

        # Set focus to newly created tab
        self.setCurrentIndex(tab.tabId)
        
        # Set name of newly created tab
        self.setTabText(tab.tabId,tabName)

    

    def removeTab(self,index):
        # find ID and delete both entry in self.plots as well as figure
        plotId = self.widget(index).plotId
        plot = self.plots[plotId]
        self.plots[plotId] = None
        del plot
        self.old_removeTab(index)

    @pyqtSlot()
    def on_close_tab(self):
        if self.tabBar.count():
            idx = self.tabBar.currentIndex()
            self.removeTab(idx)
        else:
            self.parent().close()

    ##
    #  When a tab is detached, the contents are placed into this QDialog.  The tab
    #  can be re-attached by closing the dialog or by double clicking on its
    #  window frame.
    class DetachedTab(QtWidgets.QMainWindow):
        onCloseSignal = pyqtSignal(QtWidgets.QWidget, str, QtGui.QIcon)
        
        def __init__(self, contentWidget, parent=None,app=None, plotId = None):
            QtWidgets.QMainWindow.__init__(self, parent)

            
            self.contentWidget = contentWidget     
            self.setCentralWidget(contentWidget)       
            
            self.setWindowFlag(QtCore.Qt.WindowMinimizeButtonHint, True)
            self.setWindowFlag(QtCore.Qt.WindowMaximizeButtonHint, True)
            self.docked = False
            self.plotId = self.contentWidget.plotId
            

            self.contentWidget.show()
            self.wasOutside = False


            self.shortcut = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+W"), self, self.close)
            
            
            self.app = app
            self.show()
            
        def dock(self):
            self.onCloseSignal.emit(self.contentWidget, self.objectName(), self.windowIcon())
            self.docked = True
            self.close()

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
                self.dock()

            return QtWidgets.QDialog.event(self, event)


        ##
        #  If the dialog is closed, emit the onCloseSignal and give the
        #  content widget back to the DetachableTabWidget
        #
        #  @param    event    a close event
        def closeEvent(self, event):
            plot = self.parent().tabWidget.plots[self.plotId]
            self.parent().tabWidget.plots[self.plotId] = None
            del plot
            self.close()
            #self.onCloseSignal.emit(self.contentWidget, self.objectName(), self.windowIcon())
        
        #def moveEvent(self,event):
        #    pos = QtGui.QCursor.pos()
        #    if self.parent().geometry().contains(pos) and self.wasOutside:
        #        self.enterParent(event)
        #        
        #    else:
        #        self.wasOutside = True

        def enterParent(self,event):
            pixmap = QtGui.QScreen.grabWindow(self.app.primaryScreen(), 
                        self.winId())

            QtWidgets.QApplication.processEvents()
            self.dock()
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


        def closeEvent(self, event):
            plot = self.parent().tabWidget.plots[self.plotId]
            self.parent().tabWidget.plots[self.plotId] = None
            del plot
            self.close()

        ##
        #  Get the position of the end of the drag
        #
        #  @param    event    a drop event
        def dropEvent(self, event):
            self.dragDropedPos = event.pos()
            QtWidgets.QTabBar.dropEvent(self, event)


MainBase, MainForm = uic.loadUiType(path.join(path.dirname(__file__),"Main.ui"))
class MainWindow(MainBase, MainForm):

    def __init__(self, app, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.app = app
        self.setupUi(self)

        self.tabWidget = DetachableTabWidget(self,app = app)
        self.tabWidget.tabCloseRequested.connect(lambda index: self.tabWidget.removeTab(index))

        self.shortcut = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+W"), self, self.tabWidget.on_close_tab)
        self.shortcut = QtWidgets.QShortcut(QtGui.QKeySequence("Ctrl+P"), self, self.tabWidget.addtab)
        self.actionPlot_Random.triggered.connect(self.tabWidget.addtab)

        
        self.tabWidget.show()
        self.setCentralWidget(self.tabWidget)
        self.show()
        
