'''MolScribe functionality'''

#%% Imports

import torch, cv2

from molscribe import MolScribe

from typing import Any, Dict, Optional
from PIL.Image import Image
import numpy as np
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtCore import Signal, QObject


#%% Functions

CHANNELS_COUNT = 4


class AnnotatedImageData(QObject):
    '''Class storing uploaded molecule images'''
    model_completed: Signal = Signal(dict)
    
    image: Optional[np.array] = None
    annotation: Optional[Dict] = None
    model: Optional[MolScribe] = None
    
    def __init__(self):
        super(AnnotatedImageData, self).__init__()

    def setImage(self, image: QPixmap):
        '''Gets image data from UI and prepares it for MolScribe'''
        image = image.toImage()
        image = image.convertToFormat(QImage.Format.Format_RGBA8888)

        width = image.width()
        height = image.height()

        bytes_image = image.constBits()
        array_image = np.array(bytes_image).reshape(height, width, CHANNELS_COUNT)
        self.image = array_image

    def arrayToCV2(self, image: Image) -> np.array:
        '''Transforms array Image to CV2 format'''
        
        return cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

    def imageToSmiles(self) -> None:
        '''Generates annotation & relevant info via MolScribe functionality'''
        if self.model is None:
            self.model = MolScribe('./models/molscribe_aux_1m.pth', torch.device('cpu'))

        image = self.arrayToCV2(self.image)
        result = self.model.predict_image(image, return_confidence = True,
                                          return_atoms_bonds = True)

        self.model_completed.emit(result)
        
        


