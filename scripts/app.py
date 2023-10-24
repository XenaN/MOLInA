'''Script running GUI'''

if __name__ == '__main__':
    
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(sys.argv[0]), '..'))
    
    from PySide6.QtWidgets import QApplication
    from molina import MainWindow
    
    app = QApplication(sys.argv)
    
    window = MainWindow()
    window.show()
    
    app.exec_()


