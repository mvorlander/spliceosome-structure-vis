"""Delete implausibly long covalent bonds from open ChimeraX atomic models."""

from chimerax.atomic import AtomicStructure


IDEAL_BOND_LENGTH_A = {
    frozenset(("H", "H")): 0.75,
    frozenset(("H", "C")): 1.10,
    frozenset(("H", "N")): 1.05,
    frozenset(("H", "O")): 1.00,
    frozenset(("H", "S")): 1.35,
    frozenset(("C", "C")): 1.55,
    frozenset(("C", "N")): 1.47,
    frozenset(("C", "O")): 1.43,
    frozenset(("C", "P")): 1.85,
    frozenset(("C", "S")): 1.82,
    frozenset(("N", "N")): 1.45,
    frozenset(("N", "O")): 1.40,
    frozenset(("N", "P")): 1.75,
    frozenset(("N", "S")): 1.75,
    frozenset(("O", "O")): 1.48,
    frozenset(("O", "P")): 1.62,
    frozenset(("O", "S")): 1.60,
    frozenset(("P", "P")): 2.20,
    frozenset(("P", "S")): 2.05,
    frozenset(("S", "S")): 2.05,
    frozenset(("N", "ZN")): 2.15,
    frozenset(("O", "ZN")): 2.10,
    frozenset(("S", "ZN")): 2.35,
}


def element_name(atom):
    try:
        return atom.element.name.upper()
    except Exception:
        return ""


def ideal_length(atom1, atom2):
    return IDEAL_BOND_LENGTH_A.get(frozenset((element_name(atom1), element_name(atom2))), 1.6)


def residue_number(residue):
    try:
        return int(residue.number)
    except Exception:
        return None


def describe_atom(atom):
    residue = atom.residue
    chain = getattr(residue, "chain_id", "?")
    number = getattr(residue, "number", "?")
    return f"/{chain}:{number}@{atom.name}"


def prune_implausible_bonds(session, multiplier=10.0, min_absolute_length=10.0, dry_run=False):
    inspected = 0
    removed = []
    for model in session.models.list(type=AtomicStructure):
        for bond in list(model.bonds):
            inspected += 1
            atom1, atom2 = bond.atoms
            ideal = ideal_length(atom1, atom2)
            cutoff = max(min_absolute_length, multiplier * ideal)
            if bond.length <= cutoff:
                continue
            removed.append((model, bond, atom1, atom2, float(bond.length), ideal, cutoff))
            if not dry_run:
                bond.delete()
    action = "Flagged" if dry_run else "Pruned"
    print(
        f"{action} {len(removed)} implausible covalent bonds "
        f"(inspected {inspected}; multiplier={multiplier}; min_absolute_length={min_absolute_length})."
    )
    for model, _bond, atom1, atom2, length, ideal, cutoff in removed[:200]:
        n1 = residue_number(atom1.residue)
        n2 = residue_number(atom2.residue)
        seq_gap = "" if n1 is None or n2 is None else f"; residue_number_gap={abs(n1 - n2)}"
        print(
            f"{model}: {describe_atom(atom1)} -- {describe_atom(atom2)} "
            f"length={length:.2f} A cutoff={cutoff:.2f} A ideal={ideal:.2f} A{seq_gap}"
        )
    if len(removed) > 200:
        print(f"... {len(removed) - 200} additional flagged bonds not printed")
    return removed


prune_implausible_bonds(session)
