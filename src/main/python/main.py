from fbs_runtime.application_context.PyQt5 import ApplicationContext, \
    cached_property

from MainWindow import MainWindow
import sys

class AppContext(ApplicationContext):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)

        

    def run(self):
        self.main_window.show()
        
        return self.app.exec_()

    @cached_property
    def main_window(self):
        res = MainWindow(self.app)
        
        return res # Pass context to the window.

def main():
    appctxt = AppContext()
    exit_code = appctxt.run()
    sys.exit(exit_code)

if __name__ == '__main__':
    main()