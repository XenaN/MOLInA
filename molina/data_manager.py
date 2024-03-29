import math
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
    lineIndexUpdate = Signal(object)
    atomPositionUpdate = Signal(int, object)
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
                                            "start_atom_idx",
                                            "end_atom_idx",
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
                                                                          row["atom_symbol"]), axis=1)
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
            self._bonds["start_atom_idx"] = self._bonds["endpoint_atoms"].apply(lambda x: x[0])
            self._bonds["end_atom_idx"]  = self._bonds["endpoint_atoms"].apply(lambda x: x[1])

            self._next_bond_id = self._bonds.index[-1] + 1

            lines = []
            for bond_index, bond_row in self._bonds.iterrows():
                atom1 = self._atoms[self._atoms["atom_number"] == 
                                        bond_row["start_atom_idx"]]["atom_instance"].values[0]
                atom2 = self._atoms[self._atoms["atom_number"] == 
                                    bond_row["end_atom_idx"]]["atom_instance"].values[0]
                lines.append(
                    TypedLine(
                        QLine(atom1.position,
                              atom2.position),
                        bond_row["bond_type"],
                        [bond_row["start_atom_idx"], 
                         bond_row["end_atom_idx"]]
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
    
    def addBond(self, line: TypedLine, start_atom_idx: int, end_atom_idx: int, idx: int) -> None:
        """ Add new bond data after drawing line """
        new_data = pd.DataFrame({
            "id": self._next_bond_id,
            "line_number": idx,
            "line_instance": line,
            "bond_type": line.type,
            "start_atom_idx": start_atom_idx,
            "end_atom_idx": end_atom_idx,
            "endpoint_atoms": [start_atom_idx, end_atom_idx],
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
    
    def _pointIsLineEndpoint(self, point: QPoint, line: QLine, rel_tol: float = 0.01) -> bool:
        """ Check if a point is part of a line"""
        mask_1 = math.isclose(line.p1().x(), point.x(), rel_tol=rel_tol) and \
            math.isclose(line.p1().y(), point.y(), rel_tol=rel_tol)
        
        mask_2 = math.isclose(line.p2().x(), point.x(), rel_tol=rel_tol) and \
            math.isclose(line.p2().y(), point.y(), rel_tol=rel_tol)
        
        return mask_1, mask_2

    def _recombineEndpoints(self) -> None:
        """ endpoint_atoms is list of atom indexes.
         When atom deleted, indexes are changed. 
         This function refill endpoint_atoms with actual indexes
         """
        # Reset old endpoints
        self._bonds["endpoint_atoms"] = None
        self._bonds["start_atom_idx"] = None
        self._bonds["end_atom_idx"] = None

        filtered_atoms = self._atoms[self._atoms["deleted"] == False]
        filtered_bonds = self._bonds[self._bonds["deleted"] == False]
        
        for bond_index, bond_row in filtered_bonds.iterrows():
            temp_start = None
            temp_end = None
            for atom_index, atom_row in filtered_atoms.iterrows():
                # Check is any of bond ends equal to atom position
                is_p1, is_p2 = self._pointIsLineEndpoint(atom_row["atom_instance"].position, 
                                                         bond_row["line_instance"].line)
                
                if is_p1:
                    temp_start = atom_row["atom_number"]
                elif is_p2:
                    temp_end = atom_row["atom_number"]
            
            self._bonds.at[bond_index, "start_atom_idx"] = temp_start
            self._bonds.at[bond_index, "end_atom_idx"] = temp_end
        
        # Create endpoints
        self._bonds["endpoint_atoms"] = self._bonds.apply(lambda row: [row["start_atom_idx"], 
                                                                       row["end_atom_idx"]], axis=1)

        endpoints = self._bonds.loc[self._bonds["deleted"] == False, "endpoint_atoms"].tolist()
        
        # Update indexes for drawing line
        if len(endpoints) != 0:
            self.lineIndexUpdate.emit(endpoints)

    def deleteBond(self, index: int, length: Optional[int] = None):
        """ When the bond deleted, for this bond flag "deleted" becomes True.
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
        """ When the atom deleted, for this atom flag "deleted" becomes True.
        atom_number is rearranged.
        Additionally, any bonds associated with the deleted atom are marked as 
            "True" under the "deleted" flag.
        line_number is rearranged.
        Data for dataset is updated.
        """
        # Get not-deleted data 
        atoms = self._atoms.loc[self._atoms["deleted"] == False]

        # Get unique index for deleted atom
        uid = atoms.loc[atoms["atom_number"] == index, "id"].to_list()

        assert len(uid) == 1

        # Set flag deleted for chosen uid and rerange atoms
        self._atoms.loc[self._atoms["id"] == uid[0], "deleted"] = True
        if self._atoms["deleted"].all() != True:
            self._atoms.loc[self._atoms["deleted"] == False, "atom_number"] = np.arange(length)
    
        if not self._bonds.empty and self._bonds["deleted"].all() != True:
            # Get not-deleted bonds
            bonds = self._bonds.loc[self._bonds["deleted"] == False]
            # Check is any bond has atom index as endpoint
            uids_bond = bonds.loc[bonds["endpoint_atoms"].apply(
                lambda endpoints: index in endpoints), "id"].to_list()

            if uids_bond:
                # Set deleted flag and rerange not-deleted bonds
                self._bonds.loc[self._bonds["id"].isin(uids_bond), "deleted"] = True

                length_bond = self._bonds.loc[self._bonds["deleted"] == False].shape[0]
                self._bonds.loc[self._bonds["deleted"] == False, 
                                "line_number"] = np.arange(length_bond)
                # Add action for action manager
                self._action_manager.addAction((uid, uids_bond, "not_all_deleted"), "delete_atom_and_bond")
                
                # Get indexes of deleted bonds and delete them from drawing line bond 
                line_idxs = self._bonds.loc[self._bonds["id"].isin(uids_bond), "line_number"].to_list()
                line_idxs.reverse()
                
                if len(line_idxs) != 0:
                    for i in line_idxs:
                        self.lineUpdate.emit("delete", i, None)

                # Update atom indexes in endpoints of line
                self._recombineEndpoints()

            else:
                self._recombineEndpoints()

                self._action_manager.addAction(uid[0], "delete_atom")
        
        else:
            self._action_manager.addAction(uid[0], "delete_atom")

        self._sendDataToDataset()

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
            endpoints = filtered_lines["endpoint_atoms"].to_list()
        else: 
            bonds_data = []
            endpoints = []

        return {"points": points_data,
                "lines": bonds_data,
                "endpoints": endpoints}
    
    def allDeleted(self) -> Tuple[List]:
        """ Set flag "deleted" True for all actual objects """
        uids_atoms = self._atoms.loc[self._atoms["deleted"] == False, "id"].to_list()
        self._atoms["deleted"] = True
        
        uids_bonds = self._bonds.loc[self._bonds["deleted"] == False, "id"].to_list()
        self._bonds["deleted"] = True

        self._action_manager.addAction((uids_atoms, uids_bonds, "all_deleted"), "delete_atom_and_bond")

        self._sendDataToDataset()
    
    def cleanAll(self) -> None:
        """ Reset info when image is changed """
        self._bonds = pd.DataFrame(columns=["id",
                                            "line_number",
                                            "line_instance",
                                            "bond_type",
                                            "start_atom_idx",
                                            "end_atom_idx",
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

    def undoDeleteAtomAndBond(self, data: Tuple[int, List[int], str]) -> None:
        """ Return last deleted atoms and bonds """
        uid_atom, uids_bond, flag = data
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
        
        # If all object deleted bonds are not recombined, it can be just restored
        if flag == "not_all_deleted":   
            self._recombineEndpoints()

        self._sendDataToDataset()
    
    def _updateLineInstance(self, row, index, position):
        if not row["deleted"] and row["start_atom_idx"] == index:
            row["line_instance"].line.setP1(position)
        elif not row["deleted"] and row["end_atom_idx"] == index:
            row["line_instance"].line.setP2(position)

        return row

    def _updatePosition(self, index: int,  position: QPoint) -> None:
        """ Replace position atom and bond on new one """
        self._atoms.loc[(self._atoms["deleted"] == False) & 
                        (self._atoms["atom_number"] == index),
                        "atom_instance"].item().position = position
        self._atoms.loc[(self._atoms["deleted"] == False) & 
                        (self._atoms["atom_number"] == index),
                        "x"] = position.x()
        self._atoms.loc[(self._atoms["deleted"] == False) & 
                        (self._atoms["atom_number"] == index),
                        "y"] = position.y()

        self._bonds.apply(self._updateLineInstance, axis=1, args=(index, position))

    
    def updateAtomPosition(self, index: int, position: QPoint) -> None:
        """ When atom was moved change its position here """
        atom = self._atoms.loc[(self._atoms["deleted"] == False) & 
                        (self._atoms["atom_number"] == index),
                        "atom_instance"].item()

        self._action_manager.addAction((index, atom.position), "move_atom")

        self._updatePosition(index, position)
        
        self._sendDataToDataset()
    
    def undoUpdateAtomPosition(self, data: Tuple[int, QPoint]) -> None:
        """ Return old position """
        index, old_position = data

        self._updatePosition(index, old_position)
        self._sendDataToDataset()
        self.atomPositionUpdate.emit(index, old_position)
