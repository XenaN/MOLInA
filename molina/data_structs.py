'''MolScribe functionality'''

#%% Imports

import torch, cv2

from dataclasses import dataclass
from typing import Any, List, Dict, Optional

import numpy as np

from molscribe import MolScribe



#%% Functions

# TODO: we do not need PIL here, read via cv2 and remove this function
#def arrayToCV2(self, image: Image) -> np.array:
#    '''Transforms array Image to CV2 format'''
#    
#    return cv2.cvtColor(image, cv2.COLOR_RGB2BGR)


@dataclass
class ImagePaths():
    '''Stores image and annotation paths'''
    
    path_image: str
    '''Path to the image file'''
    path_annotation: str
    '''Path to the annotation file'''


@dataclass
class ImageData():
    '''Stores info on molecule image and its annotation'''
    
    image_paths: ImagePaths
    '''Paths to the image files'''
    image: np.array
    '''Numpy-array representation of the image'''
    atoms: list # define type more precisely (list of tuples of 2 floats and strs? or better specifical data structure)
    '''List of recognized atoms and their parameters'''
    bonds: list # define type more precisely (list of tuples of 2 ints and str? or better specifical data structure)
    '''List of recognized bonds and their parameters'''
    
    def run_molscribe(self) -> None:
        '''Annotates image via MolScribe'''
        # [optional] prepare data
        
        # run molscribe
        
        # update self.atoms and self.bonds
        
        pass
        # return
    
    def save_annotation(self) -> None:
        '''Saves current annotation to the corresponding file'''
        # TODO: we need exceptions, do not forget to create the ticket
        
        pass
        # return


def image_data_from_image_file(path: str) -> ImageData:
    '''Generates ImageData object from image file'''
    # check file formats
    
    # generate paths
    
    # read image (no exceptions if unreadable, image, atoms, and bonds are empty)
    
    # read annotation (ignore if unreadable)
    
    # prepare atoms and bonds data structures
    
    # construct the object
    pass
    # return


@dataclass
class Dataset():
    '''Represents list of molecular images forming one dataset'''
    
    images: List[ImagePaths]
    '''List of images forming the dataset'''
    current_image: ImageData
    '''Image which is viewed in GUI'''
    num_images: int
    '''Total number of images in dataset'''
    current_image_idx: int = 0
    '''Index of the current image'''
    
    
    # HINT: possibly good idea to make __post_init__ and do not init current_image,
    #       so that it will be generated from self.images and self.current_image_idx
    
    
    def change_current_image(self, idx: int) -> None:
        '''Changes current image to another one by give idx'''
        pass
        # return


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


