from typing import Optional, List, Dict, Tuple

import numpy as np
import pandas as pd
from PySide6.QtCore import QObject, Signal, QPoint, QLine

from molina.drawing_objects import Atom, TypedLine
from molina.action_managers import DrawingActionManager


class DataManager(QObject):
    dataUpdateToDataset = Signal(object)
    newDataToDrawingWidget = Signal()
    pointUpdate = Signal(object)
    lineUpdate = Signal(object)
    """
    DataManager managers the exchange of information between DrawingWidget and Dataset.
    DrawingWidget needs coordinates, image size, types of bonds and atoms.
    Dataset stores coordinates in fractions and indices of atoms between which there is a bond.
    Also it save types of atoms and bonds.
    It can have only one instance.
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
                                            "type",
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
        
        
    def prepareDataToDrawingWidget(self) -> Dict[str, List]:
        filtered_points = self._atoms[self._atoms["deleted"] != True]
        points_data = filtered_points["atom_instance"].to_list()

        filtered_lines = self._bonds[self._bonds["deleted"] != True]
        bonds_data = filtered_lines["line_instance"].to_list()

        return {"points": points_data,
                "lines": bonds_data}

    def sendDataToDataset(self) -> None:
        if self._atoms.shape[0] == 0:
            self.dataUpdateToDataset.emit({"atoms": [],
                                           "bonds": []})
        else:
            filtered_atoms = self._atoms[self._atoms["deleted"] != True]
            atoms_data = filtered_atoms.drop(columns=["id", "atom_instance", "deleted"]).to_dict(orient="records")

            filtered_bonds = self._bonds[self._bonds["deleted"] != True]
            bonds_data = filtered_bonds[["type", "endpoint_atoms", "confidence"]].to_dict(orient="records")

            self.dataUpdateToDataset.emit({"atoms": atoms_data,
                                       "bonds": bonds_data})
    
    # def sendDataToDrawingWidget(self) -> None:
    #     filtered_atoms = self._atoms[self._atoms["deleted"] != True]
    #     atoms_data = filtered_atoms["atom_instance"].to_list()

    #     filtered_bonds = self._bonds[self._bonds["deleted"] != True]
    #     bonds_data = filtered_bonds["line_instance"].to_list()

    #     self.dataUpdateToDrawingWidget.emit({"atoms": atoms_data,
    #                                          "bonds": bonds_data})
            
    def sendNewDataToDrawingWidget(self, data: Dict[str, Dict]) -> None:
        self._atoms = pd.DataFrame(data["atoms"])
        self._atoms["atom_instance"] = self._atoms.apply(lambda row: Atom(QPoint(row["x"], row["y"]),
                                                                          row["atom_symbol"],
                                                                          None), axis=1)
        self._atoms["id"] = self._atoms.index
        self._atoms["atom_number"] = self._atoms.index
        self._atoms["deleted"] = False

        self._bonds = pd.DataFrame(data["bonds"])
        self._bonds["id"] = self._bonds.index
        self._bonds["line_number"] = self._bonds.index
        self._bonds["deleted"] = False

        lines = []
        for bond in data["bonds"]:
            lines.append(
                TypedLine(
                    QLine(self._atoms[self._atoms["atom_number"] == bond["endpoint_atoms"][0]]["atom_instance"].values[0].position,
                          self._atoms[self._atoms["atom_number"] == bond["endpoint_atoms"][1]]["atom_instance"].values[0].position),
                        bond["bond_type"],
                        None
                        )
            )

        self._bonds["line_instance"] = lines

        self.newDataToDrawingWidget.emit()
    
    def addAtom(self, atom: Atom, index: int) -> None:
        self._atoms.loc[len(self._atoms)] = [
            self._next_atom_id,
            index,
            atom,
            atom.name,
            atom.position.x(),
            atom.position.y(),
            None,
            False
        ]

        self.sendDataToDataset()

        self._action_manager.addAction(self._next_atom_id, "add_atom")

        self._next_atom_id += 1
    
    def addBond(self, line: TypedLine, bond_info: List, index: int) -> None:
        self._bonds.loc[len(self._bonds)] = [
            self._next_bond_id,
            index,
            line,
            line.type,
            bond_info,
            None,
            False
        ]

        self.sendDataToDataset()

        self._action_manager.addAction(self._next_bond_id, "add_bond")
        
        self._next_bond_id += 1
    
    def pointIsLineEndpoint(point: QPoint, line: QLine) -> bool:
        return line.p1() == point or line.p2() == point

    def recombineEndpoints(self) -> None:
        self._bonds["endpoint_atoms"] = [[] for _ in range(len(self._bonds))]

        filtered_atoms = self._atoms[self._atoms['deleted'] == False]
        filtered_bonds = self._bonds[self._bonds['deleted'] == False]

        for bond_index, bond_row in filtered_bonds.iterrows():
            for atom_index, atom_row in filtered_atoms.iterrows():
                if self.pointIsLineEndpoint(atom_row['atom_instance'].position, bond_row['line_instance'].line):
                    self._bonds.at[bond_index, 'endpoint_atoms'].append(atom_row['atom_number'])

    def deleteBond(self, index: int, length: Optional[int] = None):
        uid = self._bonds.loc[self._bonds["line_number"] == index, "id"].to_list()
        self._bonds.loc[self._bonds["line_number"] == index, "deleted"] = True
        self._bonds.loc[self._bonds["deleted"] is False, "line_number"] = np.arange(length)

        self._action_manager.addAction(uid, "delete_bond")
    
    def deleteAtom(self, index: int, length: Optional[int] = None):
        uid = self._atoms.loc[self._atoms["atom_number"] == index, "id"].to_list()

        self._atoms.loc[self._atoms["atom_number"] == index, "deleted"] = True
        self._atoms.loc[self._atoms["deleted"] is False, "atom_number"] = np.arange(length)
    
        if self._bonds.shape[0] != 0:
            uids_bond = self._bonds.loc[self._bonds['endpoint_atoms'].apply(lambda endpoints: index in endpoints), "id"].to_list()
            self._bonds.loc[self._bonds['endpoint_atoms'].apply(lambda endpoints: index in endpoints), 'deleted'] = True
            self.recombineEndpoints()
            self._action_manager.addAction((uid, uids_bond), "delete_atom_and_bond")
        else:
            self._action_manager.addAction(uid, "delete_atom")

    def updateDistances(self, text_size: int, bond_distance: float) -> None:
        for idx in self._atoms.index:
            self._atoms.at[idx, "atom_instance"].size = text_size
        
        for idx in self._bonds.index:
            self._bonds.at[idx, "line_instance"].size = bond_distance

    def getDrawingData(self) -> None:
        return self.prepareDataToDrawingWidget()
    
    def allDeleted(self) -> Tuple[List]:
        uids_atoms = self._atoms.loc[self._atoms["deleted"] is False, "id"].to_list()
        self._atoms["deleted"] = True
        
        uids_bonds = self._bonds.loc[self._bonds["deleted"] is False, "id"].to_list()
        self._bonds["deleted"] = True

        self._action_manager.addAction((uids_atoms, uids_bonds), "delete_atom_and_bond")
    
    def cleanAll(self) -> None:
        self._bonds = pd.DataFrame(columns=["id",
                                            "line_number",
                                            "line_instance",
                                            "type",
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
        # self.sendDataToDataset()
    
    def undo(self) -> None:
        self._action_manager.undo()

    def undoAddAtom(self, uid: int) -> None:
        self._atoms.loc[self._atoms["id"] == uid, "deleted"] = True
        self.pointUpdate.emit("delete")
        self.sendDataToDataset()

    def undoDeleteAtom(self, uid: int) -> None:
        self._atoms.loc[self._atoms["id"] == uid, "deleted"] = False
        length = self._atoms.loc[self._atoms["deleted"] is False, "atom_number"].shape[0]
        self._atoms.loc[self._atoms["deleted"] is False, "atom_number"] = np.arange(length)
        
        assert self._atoms.loc[self._atoms["id"] == uid, "atom_number"].shape[0] == 1 
        self.pointUpdate.emit("add", 
                         self._atoms.loc[self._atoms["id"] == uid, "atom_number"].iloc[0],
                         self._atoms.loc[self._atoms["id"] == uid, "atom_instance"].iloc[0])
        self.sendDataToDataset()

    def undoAddBond(self, uid: int) -> None:
        self._bonds.loc[self._bonds["id"] == uid, "deleted"] = True
        self.lineUpdate.emit("delete")

        self.sendDataToDataset()

    def undoDeleteBond(self, uid: int) -> None:
        self._bonds.loc[self._bonds["id"] == uid, "deleted"] = False
        length = self._bonds.loc[self._bonds["deleted"] is False, "line_number"].shape[0]
        self._bonds.loc[self._bonds["deleted"] is False, "line_number"] = np.arange(length)

        assert self._bonds.loc[self._bonds["id"] == uid, "line_number"].shape[0] == 1 
        self.lineUpdate.emit("add", 
                        self._bonds.loc[self._bonds["id"] == uid, "line_number"].iloc[0],
                        self._bonds.loc[self._bonds["id"] == uid, "line_instance"].iloc[0])
        
        self.sendDataToDataset()

    def undoDeleteAtomAndBond(self, data: Tuple[int, List[int]]) -> None:
        uid_atom, uids_bond = data
        for idx in uid_atom:
            self._atoms.loc[self._atoms["id"] == idx, "deleted"] = False
            self.pointUpdate.emit("add", self._atoms.loc[self._atoms["id"] == idx, "atom_number"])
        
        for idx in uids_bond:
            self._bonds.loc[self._bonds["id"] == idx, "deleted"] = False
            self.lineUpdate.emit("add", self._bonds.loc[self._bonds["id"] == idx, "line_number"])
        
        self.recombineEndpoints()
        self.sendDataToDataset()


