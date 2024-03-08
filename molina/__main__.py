'''Launches GUI via CLI'''

#%% Imports

import sys

from PySide6.QtWidgets import QApplication
from molina import MainWindow


#%% Functions

def main():
    '''Main function'''
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()
    
    return


#%% Main

main()


