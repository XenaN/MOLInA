'''MolScribe functionality'''

#%% Imports
import json
from pathlib import Path

import torch, cv2

from dataclasses import dataclass, field
from typing import Any, List, Dict, Optional
import numpy.typing as npt

import numpy as np
from PySide6.QtCore import QObject, Signal

from molscribe import MolScribe


MOLSCRIBE = './models/molscribe_aux_1m.pth'


@dataclass
class ImageData():
    '''Stores info on molecule image and its annotation'''
    
    path_image: str
    '''Path to the image file'''
    path_annotation: str
    '''Path to the annotation file'''
    image: np.array
    '''Numpy-array representation of the image'''
    atoms: Optional[List[dict[str, float]]]  = field(default_factory=list) # define type more precisely (list of tuples of 2 floats and strs? or better specifical data structure)
    '''List of recognized atoms and their parameters'''
    bonds: Optional[List[dict[str, Any]]]  = field(default_factory=list)# define type more precisely (list of tuples of 2 ints and str? or better specifical data structure)
    '''List of recognized bonds and their parameters'''
    
    def run_molscribe(self) -> None:
        '''Annotates image via MolScribe'''
        image = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)
        self.model = MolScribe(MOLSCRIBE, torch.device('cpu'))
        result = self.model.predict_image(image, return_atoms_bonds=True, return_confidence = True)

        if result:
            self.atoms = result["atoms"]
            self.bonds = result["bonds"]
    
    def save_annotation(self) -> None:
        '''Saves current annotation to the corresponding file'''
        # TODO: we need exceptions, do not forget to create the ticket
        
        pass
        # return


class ImageSignals(QObject):
    current_image = Signal(object)
    current_annotation = Signal(object)
    data_changed = Signal(list)

@dataclass
class Dataset():
    '''Represents list of molecular images forming one dataset'''

    images: Dict[str, ImageData] # Dict поддерживает insertion order
    '''Dictionary of images forming the dataset'''
    num_images: int = 10
    '''Total number of images in dataset'''
    current_image: str = ''
    '''Index of the current image'''

    def __post_init__(self):
        self.current_image_signal = ImageSignals()

    def open_image(self, path: str):
        image = cv2.imread(path, cv2.IMREAD_UNCHANGED) 
        return image
    
    def check_annotation(self, annotation_path: str):
        if annotation_path.is_file():
            with open(annotation_path) as f:
                annotation = json.load(f)
            return annotation
        else:
            return
    
    def run_molscribe_predict(self):
        self.images[self.current_image].run_molscribe()
        return self.images[self.current_image]
    
    def addCoordinates(self, coordinate: Dict):
        self.images[self.current_image].atoms = coordinate["atoms"]
        self.images[self.current_image].bonds = coordinate["bonds"]
        self.current_image_signal.current_annotation.emit({"atoms:": self.images[self.current_image].atoms,
                                                          "bonds": self.images[self.current_image].bonds})
        
    def change_current_image(self, path: str) -> None:
        '''Changes current image'''
        if path not in self.images:
            image = self.open_image(path)
            annotation_path = Path.joinpath(Path(path).parent.resolve(),
                                            Path(path).stem + '.json')
            annotation = self.check_annotation(annotation_path)
            if annotation:
                self.images[path] = ImageData(path, 
                                              annotation_path,
                                              image,
                                              annotation["atoms"], 
                                              annotation["bonds"])
            else:
                self.images[path] = ImageData(path,
                                              annotation_path,
                                              image)
            if len(self.images) > 10:
                oldest_key = list(self.images.keys())[0]
                self.images.pop(oldest_key)
        
        self.current_image = path

        self.current_image_signal.current_image.emit(self.images[path].image)
        self.current_image_signal.current_annotation.emit({"atoms:": self.images[path].atoms,
                                                          "bonds": self.images[path].bonds})
        
        
class Worker(QObject):
    finished = Signal()
    result = Signal(object)

    def __init__(self, data):
        super().__init__()
        self.data = data

    def run(self):
        result = self.data.run_molscribe_predict()

        self.result.emit(
            {"atoms:": result.atoms, 
             "bonds": result.bonds})
        self.finished.emit()


# HINT: next two functions possibly require additional code decomposition

def dataset_from_file(fs) -> Dataset:
    '''Creates Dataset from single image file'''
    
    pass
    # return


def dataset_from_directory(path_dir) -> Dataset:
    '''Creates Dataset from directory'''
    # filter image files via os.listdir
    
    # cycle over files
    pass
    # return


