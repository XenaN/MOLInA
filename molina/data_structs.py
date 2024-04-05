"""MolScribe functionality"""

# %% Imports
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


MOLSCRIBE = "./models/molscribe_aux_1m.pth"


@dataclass
class ImageData:
    """Stores info on molecule image and its annotation"""

    path_image: str
    """ Path to the image file """
    path_annotation: str
    """ Path to the annotation file """
    image: np.array
    """ Numpy-array representation of the image """
    atoms: Optional[List[Dict[str, float]]] = field(default_factory=list)
    """ List of recognized atoms and their parameters """
    bonds: Optional[List[Dict[str, Any]]] = field(default_factory=list)
    """ List of recognized bonds and their parameters """

    def runMolscribe(self) -> None:
        """Annotates image via MolScribe"""
        image = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)
        self.model = MolScribe(MOLSCRIBE, torch.device("cpu"))
        result = self.model.predict_image(
            image, return_atoms_bonds=True, return_confidence=True
        )

        if result:
            self.atoms = result["atoms"]
            self.bonds = result["bonds"]

    def saveAnnotation(self) -> None:
        """Saves current annotation to the corresponding file"""
        with open(self.path_annotation, "w", encoding="utf-8") as f:
            json.dump(
                {"atoms": self.atoms, "bonds": self.bonds},
                f,
                ensure_ascii=False,
                indent=4,
            )


class ImageSignals(QObject):
    """Class for signal due to Dataclass can't be QObject"""

    current_image = Signal(object)
    current_annotation = Signal(object)
    data_changed = Signal(object)


@dataclass
class Dataset:
    """Represents list of molecular images forming one dataset"""

    _images: Dict[str, ImageData]
    """ Dictionary of images forming the dataset """
    _num_images: int = 10
    """ Total number of images in dataset """
    _current_image: str = ""
    """ Index of the current image """
    current_model: str = "MolScribe"
    """ Current model for prediction atoms and bonds """

    def __post_init__(self):
        self._current_image_signal = ImageSignals()
        self.model_map = {"MolScribe": self.runMolscribePredict, "another": None}
        self._data_manager = DataManager()
        self._data_manager.dataUpdateToDataset.connect(self.updateCoordinates)

    def setCurrentModel(self, model_name: str) -> None:
        """Change current model when user choose other model"""
        self.current_model = model_name

    def openImage(self, path: str) -> npt.NDArray:
        """Open image with cv2 as numpy array"""
        image = cv2.imread(path, cv2.IMREAD_UNCHANGED)
        return image

    def checkAnnotation(self, annotation_path: str) -> Optional[Dict]:
        """Check annotation existing"""
        if annotation_path.is_file():
            with open(annotation_path) as f:
                annotation = json.load(f)
            return annotation
        else:
            return

    def countAtoms(self) -> None:
        """Create atom indexes"""
        for i, atom in enumerate(self._images[self._current_image].atoms):
            atom["atom_number"] = i

    def runMolscribePredict(self) -> npt.NDArray:
        """Reset all current data and run MolScribe prediction"""
        self._images[self._current_image].atoms = []
        self._images[self._current_image].bonds = []
        self._images[self._current_image].runMolscribe()

        return self._images[self._current_image]

    def updateCoordinates(self, coordinates: Dict) -> None:
        """When user draw new object, DataManager sends actual data.
        This function replace coordinate by fractions and
        update current image atoms and bonds
        """
        if len(coordinates["atoms"]) != 0:
            for atom in coordinates["atoms"]:
                atom["x"] /= self._images[self._current_image].image.shape[1]
                atom["y"] /= self._images[self._current_image].image.shape[0]

            self._images[self._current_image].atoms = coordinates["atoms"]
            self._images[self._current_image].bonds = coordinates["bonds"]
        else:
            self._images[self._current_image].atoms = []
            self._images[self._current_image].bonds = []

        self._current_image_signal.current_annotation.emit(
            {
                "atoms": self._images[self._current_image].atoms,
                "bonds": self._images[self._current_image].bonds,
            }
        )

    def drawAnnotation(self) -> None:
        """Replace fractions by coordinates and send actual data for drawing"""
        atoms = copy.deepcopy(self._images[self._current_image].atoms)
        for atom in atoms:
            atom["x"] *= self._images[self._current_image].image.shape[1]
            atom["y"] *= self._images[self._current_image].image.shape[0]

        self._data_manager.sendNewDataToDrawingWidget(
            {"atoms": atoms, "bonds": self._images[self._current_image].bonds}
        )

    def saveAnnotation(self) -> None:
        """Save annotation of actual image if it is not empty"""
        if self._current_image and len(self._images[self._current_image].atoms) != 0:
            self._images[self._current_image].saveAnnotation()

    def changeCurrentImage(self, path: str) -> None:
        """Changes current image, fill data, save data for _num_images items.
        Emit signals to update text annotation visualization
        """
        self._current_image = path
        if path not in self._images:
            image = self.openImage(path)
            annotation_path = Path.joinpath(
                Path(path).parent.resolve(), Path(path).stem + ".json"
            )
            annotation = self.checkAnnotation(annotation_path)
            if annotation:
                self._images[path] = ImageData(
                    path,
                    annotation_path,
                    image,
                    annotation["atoms"],
                    annotation["bonds"],
                )
                self.countAtoms()
            else:
                self._images[path] = ImageData(path, annotation_path, image)
            if len(self._images) > self._num_images:
                oldest_key = list(self._images.keys())[0]
                self._images.pop(oldest_key)

        self._current_image_signal.current_image.emit(self._images[path].image)
        self._current_image_signal.current_annotation.emit(
            {"atoms": self._images[path].atoms, "bonds": self._images[path].bonds}
        )

        if len(self._images[path].atoms) != 0:
            self.drawAnnotation()


class Worker(QObject):
    """Class for parallel thread"""

    finished = Signal()
    result = Signal(object)

    def __init__(self, data: Dataset):
        super().__init__()
        self.data = data

    def run(self):
        """Run actual model prediction"""
        result = self.data.model_map[self.data.current_model]()
        self.data.countAtoms()
        self.result.emit({"atoms": result.atoms, "bonds": result.bonds})
        self.finished.emit()

        self.data.drawAnnotation()


# HINT: next two functions possibly require additional code decomposition


def dataset_from_directory(path_dir) -> Dataset:
    """Creates Dataset from directory"""
    # filter image files via os.listdir

    # cycle over files
    pass
    # return
