'''MolScribe functionality'''

#%% Imports
import json, copy
from pathlib import Path

import torch, cv2

from dataclasses import dataclass, field
from typing import Any, List, Dict, Optional
import numpy.typing as npt

import numpy as np
from PySide6.QtCore import QObject, Signal

from molscribe import MolScribe

from molina.data_manager import DataManager


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
    atoms: Optional[List[Dict[str, float]]]  = field(default_factory=list) 
    '''List of recognized atoms and their parameters'''
    bonds: Optional[List[Dict[str, Any]]]  = field(default_factory=list)
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
    data_changed = Signal(object)

@dataclass
class Dataset():
    '''Represents list of molecular images forming one dataset'''

    _images: Dict[str, ImageData] # Dict поддерживает insertion order
    '''Dictionary of images forming the dataset'''
    _num_images: int = 10
    '''Total number of images in dataset'''
    _current_image: str = ''
    '''Index of the current image'''
    _current_model: str = "MolScribe"
    '''Current model for prediction atoms and bonds'''

    def __post_init__(self) -> None:
        self._current_image_signal = ImageSignals()
        self.model_map = {"MolScribe": self.run_molscribe_predict, "another": None}
        self._data_manager = DataManager()
        self._data_manager.dataUpdateToDataset.connect(self.update_coordinates)
    
    def set_current_model(self, model_name: str) -> None:
        self._current_model = model_name

    def open_image(self, path: str) -> npt.NDArray:
        image = cv2.imread(path, cv2.IMREAD_UNCHANGED) 
        return image
    
    def check_annotation(self, annotation_path: str) -> Optional[Dict]:
        if annotation_path.is_file():
            with open(annotation_path) as f:
                annotation = json.load(f)
            return annotation
        else:
            return
    
    def run_molscribe_predict(self) -> npt.NDArray:
        self._images[self._current_image].atoms = []
        self._images[self._current_image].bonds = []
        self._images[self._current_image].run_molscribe()

        return self._images[self._current_image]
    
    def update_coordinates(self, coordinates: Dict) -> None:
        if len(coordinates["atoms"]) != 0:
            for atom in coordinates["atoms"]:
                atom['x'] /= self._images[self._current_image].image.shape[1]
                atom['y'] /= self._images[self._current_image].image.shape[0]

            self._images[self._current_image].atoms = coordinates["atoms"]
            self._images[self._current_image].bonds = coordinates["bonds"]
        else:
            self._images[self._current_image].atoms = []
            self._images[self._current_image].bonds = []

        self._current_image_signal.current_annotation.emit({"atoms": self._images[self._current_image].atoms,
                                                            "bonds": self._images[self._current_image].bonds})
    
    def draw_annotation(self) -> None:
        atoms = copy.deepcopy(self._images[self._current_image].atoms)
        for atom in atoms:
            atom['x'] *= self._images[self._current_image].image.shape[1]
            atom['y'] *= self._images[self._current_image].image.shape[0]
        self._data_manager.sendNewDataToDrawingWidget({"atoms": atoms,
                                                       "bonds": self._images[self._current_image].bonds})
        
    def save_annotation(self) -> None:
        if self._current_image and len(self._images[self._current_image].atoms) != 0:

            with open(self._images[self._current_image].path_annotation, 'w', encoding='utf-8') as f:
                json.dump({
                    "atoms": self._images[self._current_image].atoms,
                    "bonds": self._images[self._current_image].bonds
                }, f, ensure_ascii=False, indent=4)

    def change_current_image(self, path: str) -> None:
        '''Changes current image'''
        self._current_image = path
        if path not in self._images:
            image = self.open_image(path)
            annotation_path = Path.joinpath(Path(path).parent.resolve(),
                                            Path(path).stem + '.json')
            annotation = self.check_annotation(annotation_path)
            if annotation:
                self._images[path] = ImageData(path, 
                                              annotation_path,
                                              image,
                                              annotation["atoms"], 
                                              annotation["bonds"])
            else:
                self._images[path] = ImageData(path,
                                              annotation_path,
                                              image)
            if len(self._images) > 10:
                oldest_key = list(self._images.keys())[0]
                self._images.pop(oldest_key)

        self._current_image_signal.current_image.emit(self._images[path].image)
        self._current_image_signal.current_annotation.emit({"atoms": self._images[path].atoms,
                                                           "bonds": self._images[path].bonds})

        if len(self._images[path].atoms) != 0:
            self.draw_annotation()
        
        
class Worker(QObject):
    finished = Signal()
    result = Signal(object)

    def __init__(self, data):
        super().__init__()
        self.data = data

    def run(self):
        result = self.data.model_map[self.data.current_model]()

        self.result.emit(
            {"atoms": result.atoms, 
             "bonds": result.bonds})
        self.finished.emit()



# HINT: next two functions possibly require additional code decomposition

def dataset_from_directory(path_dir) -> Dataset:
    '''Creates Dataset from directory'''
    # filter image files via os.listdir
    
    # cycle over files
    pass
    # return



# %%
