import json, re

data = { "atoms": [ { "atom_symbol": "C",
            "x": 0.84251968503937,
            "y": 0.11023622047244094,
            "confidence": 0.9067103266716003 },
            { "atom_symbol": "N",
            "x": 0.7874015748031497,
            "y": 0.31496062992125984,
            "confidence": 0.9118440747261047 },
            { "atom_symbol": "O",
            "x": 0.4645669291338583,
            "y": 0.05511811023622047,
            "confidence": 0.9083293676376343 } ],
    "bonds": [ { "bond_type": "single",
            "endpoint_atoms": [ 0,
                1 ],
            "confidence": 0.9999998807907104 },
            { "bond_type": "single",
            "endpoint_atoms": [ 1,
                2 ],
            "confidence": 1.0 }]}

string = ''
tab = '        '
for key, value in data.items():
  string = string + str(key) + ':\n' 
  for item in data[key]:
    for internal_key, internal_value in item.items(): 
      string = string + tab + str(internal_key) + ': ' + str(internal_value) + '\n\n'

print(string)