from typing import Optional, List, Dict, Tuple

import numpy as np
import pandas as pd
from PySide6.QtCore import QObject, Signal, QPoint, QLine

from molina.drawing_objects import Atom, TypedLine
from molina.action_managers import DrawingActionManager


class DataManager(QObject):
    dataUpdateToDataset = Signal(object)
    newDataToDrawingWidget = Signal()
    pointUpdate = Signal(str, object, object)
    lineUpdate = Signal(str, object, object)
    """
    DataManager managers the exchange of information between DrawingWidget and Dataset.
    DrawingWidget needs coordinates, image size, types of bonds, and atoms.
    Dataset of images stores coordinates in fractions and indices of atoms between which there is a bond.
    Also Dataset save types of atoms and bonds.
    DataManager saves all information about the object (atom or bond) and makes some calculations.
    DataManager can have only one instance.
    DataManager delegates all operations to DrawingActionManager, enabling it to cancel the last action(s).
    """
    _instance = None
    _is_init = False
    def __new__(cls):
        if not cls._instance:
            cls._instance = super(DataManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if self._is_init:
            return
        super(DataManager, self).__init__()
        self._is_init = True
            
        self._next_bond_id = 0
        self._next_atom_id = 0
        self._action_manager = DrawingActionManager(self)
        self._bonds = pd.DataFrame(columns=["id",
                                            "line_number",
                                            "line_instance",
                                            "bond_type",
                                            "endpoint_atoms",
                                            "confidence",
                                            "deleted"])

        self._atoms = pd.DataFrame(columns=["id",
                                            "atom_number",
                                            "atom_instance",
                                            "atom_symbol",
                                            "x",
                                            "y",
                                            "confidence",
                                            "deleted"])
        
        
    def _sendDataToDataset(self) -> None:
        """ Emit signal to send updated data to Dataset: 
            empty or full dictionary
            atoms - atom number, atom symbol, x, y, confidence
            bonds - bond_type, endpoint_atoms, confidence
        """
        if self._atoms.shape[0] == 0:
            self.dataUpdateToDataset.emit({"atoms": [],
                                           "bonds": []})
        else:
            filtered_atoms = self._atoms[self._atoms["deleted"] != True]
            atoms_data = filtered_atoms.drop(columns=["id", "atom_instance", "deleted"]).to_dict(orient="records")

            filtered_bonds = self._bonds[self._bonds["deleted"] != True]
            bonds_data = filtered_bonds[["bond_type", "endpoint_atoms", "confidence"]].to_dict(orient="records")

            self.dataUpdateToDataset.emit({"atoms": atoms_data,
                                           "bonds": bonds_data})
            
    def sendNewDataToDrawingWidget(self, data: Dict[str, Dict]) -> None:
        """ When image already has annotation, create common data for DataManager
        and emit signal to send necessary data to draw it by DrawingWidget
        """
        self._atoms = pd.DataFrame(data["atoms"])
        self._atoms["atom_instance"] = self._atoms.apply(lambda row: Atom(QPoint(row["x"], row["y"]),
                                                                          row["atom_symbol"],
                                                                          None), axis=1)
        self._atoms["id"] = self._atoms.index
        self._atoms["atom_number"] = self._atoms.index
        self._atoms["deleted"] = False

        self._next_atom_id = self._atoms.index[-1] + 1

        if "confidence" not in self._atoms.columns:
            self._atoms["confidence"] = "not_modeling"

        self._bonds = pd.DataFrame(data["bonds"])

        if not self._bonds.empty:
            self._bonds["id"] = self._bonds.index
            self._bonds["line_number"] = self._bonds.index
            self._bonds["deleted"] = False

            self._next_bond_id = self._bonds.index[-1] + 1

            lines = []
            for bond in data["bonds"]:
                lines.append(
                    TypedLine(
                        QLine(self._atoms[self._atoms["atom_number"] == 
                                        bond["endpoint_atoms"][0]]["atom_instance"].values[0].position,
                            self._atoms[self._atoms["atom_number"] == 
                                        bond["endpoint_atoms"][1]]["atom_instance"].values[0].position),
                            bond["bond_type"],
                            None
                            )
                )

            self._bonds["line_instance"] = lines

            if "confidence" not in self._bonds.columns:
                self._bonds["confidence"] = "not_modeling"

        self._action_manager = DrawingActionManager(self)
        self.newDataToDrawingWidget.emit()
    
    def addAtom(self, atom: Atom, idx: int) -> None:
        """ Add new atom data after drawing point """
        new_data = pd.DataFrame({
            "id": self._next_atom_id,
            "atom_number": idx,
            "atom_instance": atom,
            "atom_symbol": atom.name,
            "x": atom.position.x(),
            "y": atom.position.y(),
            "confidence": "not_modeling",
            "deleted": False
        }, index=[0])
        if self._atoms.empty:
            self._atoms = new_data.copy()
        else:
            self._atoms = pd.concat([self._atoms, new_data], ignore_index=True)

        self._sendDataToDataset()

        self._action_manager.addAction(self._next_atom_id, "add_atom")

        self._next_atom_id += 1
    
    def addBond(self, line: TypedLine, bond_info: List, idx: int) -> None:
        """ Add new bond data after drawing line """
        new_data = pd.DataFrame({
            "id": self._next_bond_id,
            "line_number": idx,
            "line_instance": line,
            "bond_type": line.type,
            "endpoint_atoms": [bond_info],
            "confidence": "not_modeling",
            "deleted": False
        }, index=[0])

        if self._bonds.empty:
            self._bonds = new_data.copy()
        else:
            self._bonds = pd.concat([self._bonds, new_data], ignore_index=True)   

        self._sendDataToDataset()

        self._action_manager.addAction(self._next_bond_id, "add_bond")
        
        self._next_bond_id += 1
    
    def _pointIsLineEndpoint(self, point: QPoint, line: QLine) -> bool:
        """ Check if a point is part of a line"""
        return line.p1() == point or line.p2() == point

    def _recombineEndpoints(self) -> None:
        """ endpoint_atoms is list of atom indexes.
         When atom deleted, indexes are changed. 
         This function refill endpoint_atoms with actual indexes
         """
        self._bonds["endpoint_atoms"] = [[] for _ in range(len(self._bonds))]

        filtered_atoms = self._atoms[self._atoms['deleted'] == False]
        filtered_bonds = self._bonds[self._bonds['deleted'] == False]

        for bond_index, bond_row in filtered_bonds.iterrows():
            for atom_index, atom_row in filtered_atoms.iterrows():
                if self._pointIsLineEndpoint(atom_row['atom_instance'].position, bond_row['line_instance'].line):
                    self._bonds.at[bond_index, 'endpoint_atoms'].append(atom_row['atom_number'])

    def deleteBond(self, index: int, length: Optional[int] = None):
        """ When the bond deleted, for this bond flag 'deleted' becomes True.
        line_number rearranged.
        Data for dataset is updated.
        """
        uid = self._bonds.loc[self._bonds["line_number"] == index, "id"].to_list()
        self._bonds.loc[self._bonds["line_number"] == index, "deleted"] = True
        if self._bonds["deleted"].all() != True:
            self._bonds.loc[self._bonds["deleted"] == False, "line_number"] = np.arange(length)

        self._action_manager.addAction(uid, "delete_bond")

        self._sendDataToDataset()
    
    def deleteAtom(self, index: int, length: Optional[int] = None):
        """ When the atom deleted, for this atom flag 'deleted' becomes True.
        atom_number is rearranged.
        Additionally, any bonds associated with the deleted atom are marked as 
            'True' under the 'deleted' flag.
        line_number is rearranged.
        Data for dataset is updated.
        """
        uid = self._atoms.loc[self._atoms["atom_number"] == index, "id"].to_list()

        self._atoms.loc[self._atoms["atom_number"] == index, "deleted"] = True
        if self._atoms["deleted"].all() != True:
            self._atoms.loc[self._atoms["deleted"] == False, "atom_number"] = np.arange(length)
    
        if not self._bonds.empty and self._bonds["deleted"].all() != True:
            
            bonds = self._bonds.loc[self._bonds["deleted"] == False]

            uids_bond = bonds.loc[bonds['endpoint_atoms'].apply(
                lambda endpoints: index in endpoints), "id"].to_list()

            if uids_bond:

                self._bonds.loc[self._bonds['endpoint_atoms'].apply(
                    lambda endpoints: index in endpoints), 'deleted'] = True

                self._recombineEndpoints()

                length_bond = self._bonds.loc[self._bonds["deleted"] == False].shape[0]
                self._bonds.loc[self._bonds["deleted"] == False, 
                                "line_number"] = np.arange(length_bond)

                self._action_manager.addAction((uid, uids_bond), "delete_atom_and_bond")

                line_idxs = self._bonds.loc[self._bonds["id"].isin(uids_bond), "line_number"].to_list()
                line_idxs.reverse()
                
                if len(line_idxs) != 0:
                    for i in line_idxs:
                        self.lineUpdate.emit("delete", i, None)
        
        else:
            self._action_manager.addAction(uid, "delete_atom")

        self._sendDataToDataset()

    def updateDistances(self, text_size: int, bond_distance: float) -> None:
        """ For data from Dataset there ar no any information about distances. It is saved in DrawingWidget.
        When DrawingWidget gets not full atom and bond instances it updates distance and size.
        """
        for idx in self._atoms.index:
            self._atoms.at[idx, "atom_instance"].size = text_size
        
        for idx in self._bonds.index:
            self._bonds.at[idx, "line_instance"].size = bond_distance

    def getDrawingData(self) -> None:
        """ Return data needed to DrawingWidget: 
            points - atom position on not scaled image
            lines - bond position on not scaled image
        """
        filtered_points = self._atoms[self._atoms["deleted"] != True]
        points_data = filtered_points["atom_instance"].to_list()

        if not self._bonds.empty:
            filtered_lines = self._bonds[self._bonds["deleted"] != True]
            bonds_data = filtered_lines["line_instance"].to_list()
        else: 
            bonds_data = []

        return {"points": points_data,
                "lines": bonds_data}
    
    def allDeleted(self) -> Tuple[List]:
        """ Set flag 'deleted' True for all actual objects """
        uids_atoms = self._atoms.loc[self._atoms["deleted"] == False, "id"].to_list()
        self._atoms["deleted"] = True
        
        uids_bonds = self._bonds.loc[self._bonds["deleted"] == False, "id"].to_list()
        self._bonds["deleted"] = True

        self._action_manager.addAction((uids_atoms, uids_bonds), "delete_atom_and_bond")

        self._sendDataToDataset()
    
    def cleanAll(self) -> None:
        """ Reset info when image is changed """
        self._bonds = pd.DataFrame(columns=["id",
                                            "line_number",
                                            "line_instance",
                                            "bond_type",
                                            "endpoint_atoms",
                                            "confidence",
                                            "deleted"])

        self._atoms = pd.DataFrame(columns=["id",
                                            "atom_number",
                                            "atom_instance",
                                            "atom_symbol",
                                            "x",
                                            "y",
                                            "confidence",
                                            "deleted"])
        self._next_bond_id = 0
        self._next_atom_id = 0

        self._action_manager = DrawingActionManager(self)
    
    def undo(self) -> None:
        """ ctrl+z follow-up function"""
        self._action_manager.undo()

    def undoAddAtom(self, uid: int) -> None:
        """ Delete last added atom """
        self._atoms.loc[self._atoms["id"] == uid, "deleted"] = True
        self.pointUpdate.emit("delete", None, None)
        self._sendDataToDataset()

    def undoDeleteAtom(self, uid: int) -> None:
        """ Return last deleted atom """
        self._atoms.loc[self._atoms["id"] == uid, "deleted"] = False
        length = self._atoms.loc[self._atoms["deleted"] == False, "atom_number"].shape[0]
        self._atoms.loc[self._atoms["deleted"] == False, "atom_number"] = np.arange(length)
        
        assert self._atoms.loc[self._atoms["id"] == uid, "atom_number"].shape[0] == 1 
        self.pointUpdate.emit("add", 
                         self._atoms.loc[self._atoms["id"] == uid, "atom_number"].iloc[0],
                         self._atoms.loc[self._atoms["id"] == uid, "atom_instance"].iloc[0])
        self._sendDataToDataset()

    def undoAddBond(self, uid: int) -> None:
        """ Delete last added bond """
        self._bonds.loc[self._bonds["id"] == uid, "deleted"] = True
        self.lineUpdate.emit("delete", None, None)

        self._sendDataToDataset()

    def undoDeleteBond(self, uid: int) -> None:
        """ Return last deleted bond """
        assert len(uid) == 1
        uid = uid[0]
        self._bonds.loc[self._bonds["id"] == uid, "deleted"] = False
        length = self._bonds.loc[self._bonds["deleted"] == False, "line_number"].shape[0]
        self._bonds.loc[self._bonds["deleted"] == False, "line_number"] = np.arange(length)

        assert self._bonds.loc[self._bonds["id"] == uid, "line_number"].shape[0] == 1 
        self.lineUpdate.emit("add", 
                        self._bonds.loc[self._bonds["id"] == uid, "line_number"].iloc[0],
                        self._bonds.loc[self._bonds["id"] == uid, "line_instance"].iloc[0])
        
        self._sendDataToDataset()

    def undoDeleteAtomAndBond(self, data: Tuple[int, List[int]]) -> None:
        """ Return last deleted atoms and bonds """
        uid_atom, uids_bond = data
        for idx in uid_atom:
            self._atoms.loc[self._atoms["id"] == idx, "deleted"] = False

            length = self._atoms.loc[self._atoms["deleted"] == False, "atom_number"].shape[0]
            self._atoms.loc[self._atoms["deleted"] == False, "atom_number"] = np.arange(length)

            self.pointUpdate.emit("add", self._atoms.loc[self._atoms["id"] == idx, "atom_number"].iloc[0], 
                                  self._atoms.loc[self._atoms["id"] == idx, "atom_instance"].iloc[0])
        
        for idx in uids_bond:
            self._bonds.loc[self._bonds["id"] == idx, "deleted"] = False

            length = self._bonds.loc[self._bonds["deleted"] == False, "line_number"].shape[0]
            self._bonds.loc[self._bonds["deleted"] == False, "line_number"] = np.arange(length)

            self.lineUpdate.emit("add", self._bonds.loc[self._bonds["id"] == idx, "line_number"].iloc[0], 
                                 self._bonds.loc[self._bonds["id"] == idx, "line_instance"].iloc[0])
            
        self._recombineEndpoints()
        self._sendDataToDataset()
