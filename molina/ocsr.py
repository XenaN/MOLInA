'''MolScribe functionality'''

#%% Imports

import torch, cv2

from molscribe import MolScribe

from typing import List, Tuple
from PIL.Image import Image
import numpy as np
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtCore import Signal, QObject


#%% Functions

CHANNELS_COUNT = 4


class AnnotatedImageData(QObject):
    model_completed = Signal(int)
    def __init__(self):
        super(AnnotatedImageData, self).__init__()
        self.image = None
        self.annotation = None
        self.model = None


    def setImage(self, image: QPixmap):
        image = image.toImage()
        image = image.convertToFormat(QImage.Format.Format_RGBA8888)

        width = image.width()
        height = image.height()

        ptr = image.constBits()
        arr = np.array(ptr).reshape(height, width, CHANNELS_COUNT)
        self.image = arr

    def PILtoCV2(self, image: Image) -> np.array:
        '''Transforms PIL Image to CV2 format'''
        
        return cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

    def imageToSmiles(self):
        if self.model is None:
            self.model = MolScribe('./models/molscribe_aux_1m.pth', torch.device('cpu'))
        
        image = self.PILtoCV2(self.image)
        res = self.model.predict_image(image, return_confidence = True)
        print(type(res), res)
        res = 1

        self.model_completed.emit(res)
        
        


