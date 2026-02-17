
from __future__ import annotations

from pathlib import Path
from rdkit import Chem
from rdkit.Chem import AllChem

MOLECULES = {
    "water": "O",
    "methane": "C",
    "ethane": "CC",
    "propane": "CCC",
    "butane": "CCCC",
    "ammonia": "N",
    "co2": "O=C=O",
    "oxygen": "O=O",
    "nitrogen": "N#N",
    "hydrogen": "[H][H]",
    "ethanol": "CCO",
    "acetone": "CC(=O)C",
    "acetic_acid": "CC(=O)O",
    "formic_acid": "C(=O)O",
    "benzene": "c1ccccc1",
    "toluene": "Cc1ccccc1",
    "phenol": "Oc1ccccc1",
    "glucose": "OC[C@H]1O[C@H](O)[C@H](O)[C@@H](O)[C@@H]1O",
    "glycine": "NCC(=O)O",
    "alanine": "CC(N)C(=O)O",
    "glycerol": "OCC(O)CO",
    "urea": "NC(=O)N",
    "hcl": "[H]Cl",
    "naoh": "[Na+].[OH-]",
    "nacl": "[Na+].[Cl-]",
    "sulfuric_acid": "OS(=O)(=O)O",
    "nitric_acid": "O[N+](=O)[O-]",
}

def smiles_to_pdb(smiles: str, out_path: Path):
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError(f"Bad SMILES: {smiles}")

    mol = Chem.AddHs(mol)
    AllChem.EmbedMolecule(mol, AllChem.ETKDGv3())
    AllChem.UFFOptimizeMolecule(mol, maxIters=500)

    pdb_block = Chem.MolToPDBBlock(mol)
    out_path.write_text(pdb_block, encoding="utf-8")

def main():
    root = Path(__file__).resolve().parents[1]
    out_dir = root / "assets" / "molecules"
    out_dir.mkdir(parents=True, exist_ok=True)

    ok = 0
    for name, smi in MOLECULES.items():
        out = out_dir / f"{name}.pdb"
        try:
            smiles_to_pdb(smi, out)
            ok += 1
            print(f"[OK] {out}")
        except Exception as e:
            print(f"[FAIL] {name}: {e}")

    print(f"Done. Generated: {ok}")

if __name__ == "__main__":
    main()
