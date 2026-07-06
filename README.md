# Spliceosome Cryo-EM ChimeraX Scripts

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21168651.svg)](https://doi.org/10.5281/zenodo.21168651)

Lightweight static dashboard for copying ChimeraX scripts for spliceosome cryo-EM PDB entries.

- 134 deposited PDB entries.
- Original deposited chain identifiers only.
- Thumbnail PNGs and RNA 2D preview panels are included.
- No mmCIF files, local CIF models, or large map binaries are included.
- ChimeraX scripts use `open <pdb_id>` so ChimeraX downloads structures directly from the PDB.
- Primary-map script variants use `open emdb:<id>` so ChimeraX can download deposited primary EMDB maps on demand.

Open `index.html` locally, or use the GitHub Pages dashboard:
https://mvorlander.github.io/spliceosome-structure-vis/

The local curated CIF-only entries `9s2e` / ILS-AQR, `local_step2`, and `9s2f` / DIS are intentionally excluded.
