from typing import Dict, Tuple
from rdkit import Chem

from molina.constants import RGROUP_SYMBOLS, BOND_TYPES, ABBREVIATIONS, FORMULA_REGEX


BOND_TYPES_3 = {
    1: Chem.rdchem.BondType.SINGLE,
    2: Chem.rdchem.BondType.DOUBLE,
    3: Chem.rdchem.BondType.TRIPLE,
}


def annotation_to_coords_and_edges(data) -> Dict:
    """Function to data prepare for converting into SMILES or molblock"""
    # Remove hydrogen if needed
    filtered_atoms_data = [atom for atom in data["atoms"] if atom["atom_symbol"] != "H"]
    mask = [atom["atom_number"] for atom in data["atoms"] if atom["atom_symbol"] == "H"]
    if len(filtered_atoms_data) == 0:
        filtered_bonds_data = []
        for bond in data["bonds"]:
            for i in mask:
                if i not in bond["endpoint_atoms"]:
                    filtered_bonds_data.append(bond)

        data = {"atoms": filtered_atoms_data, "bonds": filtered_bonds_data}

    data_output = {}

    if "atoms" in data and "bonds" in data:
        atoms_data = data["atoms"]
        coords = [(atom["x"], atom["y"]) for atom in atoms_data]
        symbols = [atom["atom_symbol"] for atom in atoms_data]

        data_output["chartok_coords"] = {"coords": coords, "symbols": symbols}

        bonds_data = data["bonds"]
        num_atoms = max(max(bond["endpoint_atoms"]) for bond in bonds_data) + 1

        edges = [[0 for _ in range(num_atoms)] for _ in range(num_atoms)]

        for bond in bonds_data:
            i, j = bond["endpoint_atoms"]
            bond_type_int = BOND_TYPES.index(
                bond["bond_type"]
            )  # Map bond type to an integer
            edges[i][j] = bond_type_int
            edges[j][i] = bond_type_int

        data_output["edges"] = edges

    return data_output


def convert_graph_to_molfile(
    coords, symbols, edges, image=None, debug=False
) -> Chem.rdchem.RWMol:
    """Create molblock from RDkit"""
    mol = Chem.RWMol()
    n = len(symbols)
    ids = []

    for i in range(n):
        symbol = symbols[i]
        if symbol[0] == "[":
            symbol = symbol[1:-1]

        if symbol in RGROUP_SYMBOLS:
            atom = Chem.Atom("*")
            if symbol[0] == "R" and symbol[1:].isdigit():
                atom.SetIsotope(int(symbol[1:]))
            Chem.SetAtomAlias(atom, symbol)

        elif symbol in ABBREVIATIONS:
            atom = Chem.Atom("*")
            Chem.SetAtomAlias(atom, symbol)

        else:
            try:  # try to get SMILES of atom
                atom = Chem.AtomFromSmiles(symbols[i])
                atom.SetChiralTag(Chem.rdchem.ChiralType.CHI_UNSPECIFIED)

            except:  # otherwise, abbreviation or condensed formula
                atom = Chem.Atom("*")
                Chem.SetAtomAlias(atom, symbol)

        if atom.GetSymbol() == "*":
            atom.SetProp("molFileAlias", symbol)

        idx = mol.AddAtom(atom)
        assert idx == i
        ids.append(idx)

    for i in range(n):
        for j in range(i + 1, n):
            if edges[i][j] == 1:
                mol.AddBond(ids[i], ids[j], Chem.BondType.SINGLE)
            elif edges[i][j] == 2:
                mol.AddBond(ids[i], ids[j], Chem.BondType.DOUBLE)
            elif edges[i][j] == 3:
                mol.AddBond(ids[i], ids[j], Chem.BondType.TRIPLE)
            elif edges[i][j] == 4:
                mol.AddBond(ids[i], ids[j], Chem.BondType.AROMATIC)
            elif edges[i][j] == 5:
                mol.AddBond(ids[i], ids[j], Chem.BondType.SINGLE)
                mol.GetBondBetweenAtoms(ids[i], ids[j]).SetBondDir(
                    Chem.BondDir.BEGINWEDGE
                )
            elif edges[i][j] == 6:
                mol.AddBond(ids[i], ids[j], Chem.BondType.SINGLE)
                mol.GetBondBetweenAtoms(ids[i], ids[j]).SetBondDir(
                    Chem.BondDir.BEGINDASH
                )

    try:
        molblock = Chem.MolToMolBlock(mol)
    except Exception as e:
        molblock = ""

    return molblock


def _parse_tokens(tokens: list):
    """
    Parse tokens of condensed formula into list of pairs `(elt, num)`
    where `num` is the multiplicity of the atom (or nested condensed formula) `elt`
    Used by `_parse_formula`, which does the same thing but takes a formula in string form as input
    """
    elements = []
    i = 0
    j = 0
    while i < len(tokens):
        if tokens[i] == "(":
            while j < len(tokens) and tokens[j] != ")":
                j += 1
            elt = _parse_tokens(tokens[i + 1 : j])
        else:
            elt = tokens[i]
        j += 1
        if j < len(tokens) and tokens[j].isnumeric():
            num = int(tokens[j])
            j += 1
        else:
            num = 1
        elements.append((elt, num))
        i = j
    return elements


def _parse_formula(formula: str):
    """
    Parse condensed formula into list of pairs `(elt, num)`
    where `num` is the subscript to the atom (or nested condensed formula) `elt`
    Example: "C2H4O" -> [('C', 2), ('H', 4), ('O', 1)]
    """
    tokens = FORMULA_REGEX.findall(formula)
    # if ''.join(tokens) != formula:
    #     tokens = FORMULA_REGEX_BACKUP.findall(formula)
    return _parse_tokens(tokens)


def _expand_carbon(elements: list):
    """
    Given list of pairs `(elt, num)`, output single list of all atoms in order,
    expanding carbon sequences (CaXb where a > 1 and X is halogen) if necessary
    Example: [('C', 2), ('H', 4), ('O', 1)] -> ['C', 'H', 'H', 'C', 'H', 'H', 'O'])
    """
    expanded = []
    i = 0
    while i < len(elements):
        elt, num = elements[i]
        # expand carbon sequence
        if elt == "C" and num > 1 and i + 1 < len(elements):
            next_elt, next_num = elements[i + 1]
            quotient, remainder = next_num // num, next_num % num
            for _ in range(num):
                expanded.append("C")
                for _ in range(quotient):
                    expanded.append(next_elt)
            for _ in range(remainder):
                expanded.append(next_elt)
            i += 2
        # recurse if `elt` itself is a list (nested formula)
        elif isinstance(elt, list):
            new_elt = _expand_carbon(elt)
            for _ in range(num):
                expanded.append(new_elt)
            i += 1
        # simplest case: simply append `elt` `num` times
        else:
            for _ in range(num):
                expanded.append(elt)
            i += 1
    return expanded


def _condensed_formula_list_to_smiles(
    formula_list, start_bond, end_bond=None, direction=None
):
    """
    Converts condensed formula (in the form of a list of symbols) to smiles
    Input:
    `formula_list`: e.g. ['C', 'H', 'H', 'N', ['C', 'H', 'H', 'H'], ['C', 'H', 'H', 'H']] for CH2N(CH3)2
    `start_bond`: # bonds attached to beginning of formula
    `end_bond`: # bonds attached to end of formula (deduce automatically if None)
    `direction` (1, -1, or None): direction in which to process the list (1: left to right; -1: right to left; None: deduce automatically)
    Returns:
    `smiles`: smiles corresponding to input condensed formula
    `bonds_left`: bonds remaining at the end of the formula (for connecting back to main molecule); should equal `end_bond` if specified
    `num_trials`: number of trials
    `success` (bool): whether conversion was successful
    """
    # `direction` not specified: try left to right; if fails, try right to left
    if direction is None:
        num_trials = 1
        for dir_choice in [1, -1]:
            smiles, bonds_left, trials, success = _condensed_formula_list_to_smiles(
                formula_list, start_bond, end_bond, dir_choice
            )
            num_trials += trials
            if success:
                return smiles, bonds_left, num_trials, success
        return None, None, num_trials, False
    assert direction == 1 or direction == -1


def get_smiles_from_symbol(symbol, mol, atom, bonds):
    """
    Convert symbol (abbrev. or condensed formula) to smiles
    If condensed formula, determine parsing direction and num. bonds on each side using coordinates
    """
    if symbol in ABBREVIATIONS:
        return ABBREVIATIONS[symbol].smiles
    if len(symbol) > 20:
        return None

    total_bonds = int(sum([bond.GetBondTypeAsDouble() for bond in bonds]))
    formula_list = _expand_carbon(_parse_formula(symbol))
    smiles, bonds_left, num_trails, success = _condensed_formula_list_to_smiles(
        formula_list, total_bonds, None
    )
    if success:
        return smiles
    return None


def convert_smiles_to_mol(smiles):
    if smiles is None or smiles == "":
        return None
    try:
        mol = Chem.MolFromSmiles(smiles)
    except:
        return None
    return mol


def expand_functional_group(mol, mappings) -> Tuple[str, Chem.rdchem.RWMol]:
    """If alias is not simple, function converts alias to SMILES separately"""
    # Check alias
    bool_alias = (
        any([len(Chem.GetAtomAlias(atom)) > 0 for atom in mol.GetAtoms()])
        or len(mappings) > 0
    )

    if bool_alias:
        mol_w = Chem.RWMol(mol)
        num_atoms = mol_w.GetNumAtoms()
        for i, atom in enumerate(mol_w.GetAtoms()):  # reset radical electrons
            atom.SetNumRadicalElectrons(0)

        atoms_to_remove = []
        for i in range(num_atoms):
            atom = mol_w.GetAtomWithIdx(i)
            if atom.GetSymbol() == "*":
                symbol = Chem.GetAtomAlias(atom)
                isotope = atom.GetIsotope()
                if isotope > 0 and isotope in mappings:
                    symbol = mappings[isotope]
                if not (isinstance(symbol, str) and len(symbol) > 0):
                    continue
                # rgroups do not need to be expanded
                if symbol in RGROUP_SYMBOLS:
                    continue

                bonds = atom.GetBonds()
                sub_smiles = get_smiles_from_symbol(symbol, mol_w, atom, bonds)

                # create mol object for abbreviation/condensed formula from its SMILES
                mol_r = convert_smiles_to_mol(sub_smiles)

                if mol_r is None:
                    # atom.SetAtomicNum(6)
                    atom.SetIsotope(0)
                    continue

                # remove bonds connected to abbreviation/condensed formula
                adjacent_indices = [bond.GetOtherAtomIdx(i) for bond in bonds]
                for adjacent_idx in adjacent_indices:
                    mol_w.RemoveBond(i, adjacent_idx)

                adjacent_atoms = [
                    mol_w.GetAtomWithIdx(adjacent_idx)
                    for adjacent_idx in adjacent_indices
                ]
                for adjacent_atom, bond in zip(adjacent_atoms, bonds):
                    adjacent_atom.SetNumRadicalElectrons(
                        int(bond.GetBondTypeAsDouble())
                    )

                # get indices of atoms of main body that connect to substituent
                bonding_atoms_w = adjacent_indices
                # assume indices are concated after combine mol_w and mol_r
                bonding_atoms_r = [mol_w.GetNumAtoms()]
                for atm in mol_r.GetAtoms():
                    if atm.GetNumRadicalElectrons() and atm.GetIdx() > 0:
                        bonding_atoms_r.append(mol_w.GetNumAtoms() + atm.GetIdx())

                # combine main body and substituent into a single molecule object
                combo = Chem.CombineMols(mol_w, mol_r)

                # connect substituent to main body with bonds
                mol_w = Chem.RWMol(combo)
                # if len(bonding_atoms_r) == 1:  # substituent uses one atom to bond to main body
                for atm in bonding_atoms_w:
                    bond_order = mol_w.GetAtomWithIdx(atm).GetNumRadicalElectrons()
                    mol_w.AddBond(
                        atm, bonding_atoms_r[0], order=BOND_TYPES_3[bond_order]
                    )

                # reset radical electrons
                for atm in bonding_atoms_w:
                    mol_w.GetAtomWithIdx(atm).SetNumRadicalElectrons(0)
                for atm in bonding_atoms_r:
                    mol_w.GetAtomWithIdx(atm).SetNumRadicalElectrons(0)
                atoms_to_remove.append(i)

        # Remove atom in the end, otherwise the id will change
        # Reverse the order and remove atoms with larger id first
        atoms_to_remove.sort(reverse=True)
        for i in atoms_to_remove:
            mol_w.RemoveAtom(i)
        smiles = Chem.MolToSmiles(mol_w)
        mol = mol_w.GetMol()
    else:
        smiles = Chem.MolToSmiles(mol)
    return smiles, mol
