'''MolScribe functionality'''

#%% Imports

import torch, cv2

from molscribe import MolScribe

from typing import List, Tuple
from PIL.Image import Image
import numpy as np


#%% Functions

MODEL = MolScribe('./models/molscribe_aux_1m.pth', torch.device('cpu'))


def PILtoCV2(image: Image) -> np.array:
    '''Transforms PIL Image to CV2 format'''
    
    return cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)


def ImagesToSmiles(images: List[Image]) -> List[Tuple[str, float]]:
    '''Returns SMILES and confidence for the give image of molecule'''
    images = [PILtoCV2(image) for image in images]
    res = MODEL.predict_images(images, return_confidence = True)
    
    return res


