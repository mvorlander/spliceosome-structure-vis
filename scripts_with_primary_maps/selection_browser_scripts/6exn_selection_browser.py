#!/usr/bin/env python3
"""Open a small ChimeraX browser for generated named selections."""

from __future__ import annotations

import json
import sys

from chimerax.core.commands import run


def _ui_available(session) -> bool:
    return bool(getattr(getattr(session, "ui", None), "is_gui", False))


def open_selection_browser(session, spec_path: str) -> None:
    with open(spec_path, "r", encoding="utf-8") as handle:
        spec = json.load(handle)
    selectors = list(spec.get("selectors", []))
    if not selectors:
        session.logger.info("No spliceosome named selections are available for this structure.")
        return
    if not _ui_available(session):
        session.logger.info(
            f"Loaded {len(selectors)} spliceosome named selections; "
            "the selection browser is skipped in no-GUI ChimeraX."
        )
        return

    from chimerax.core.tools import ToolInstance
    from chimerax.ui import MainToolWindow
    from Qt.QtCore import Qt
    from Qt.QtGui import QColor, QBrush, QFont
    from Qt.QtWidgets import (
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QPushButton,
        QTreeWidget,
        QTreeWidgetItem,
        QVBoxLayout,
    )

    class SpliceosomeSelectionBrowser(ToolInstance):
        SESSION_ENDURING = False
        SESSION_SAVE = False

        def __init__(self, session, tool_name, spec, selectors):
            super().__init__(session, tool_name)
            self.spec = spec
            self.selectors = selectors
            self.filtered = list(selectors)
            self.tool_window = MainToolWindow(self)
            parent = self.tool_window.ui_area
            layout = QVBoxLayout(parent)
            title = QLabel(
                f"{spec.get('pdb_id', '').upper()} named selections "
                f"({len(selectors)} total)"
            )
            layout.addWidget(title)
            self.search = QLineEdit(parent)
            self.search.setPlaceholderText("Search selector, label, category, residues, or atomspec")
            layout.addWidget(self.search)
            self.tree = QTreeWidget(parent)
            self.tree.setColumnCount(3)
            self.tree.setHeaderLabels(["Selection", "Target", "Selector"])
            self.tree.setAlternatingRowColors(True)
            self.tree.setRootIsDecorated(True)
            self.tree.setUniformRowHeights(False)
            layout.addWidget(self.tree)
            buttons = QHBoxLayout()
            self.select_button = QPushButton("Select + Zoom", parent)
            self.clear_button = QPushButton("Clear", parent)
            buttons.addWidget(self.select_button)
            buttons.addWidget(self.clear_button)
            layout.addLayout(buttons)

            self.search.textChanged.connect(self._filter)
            self.tree.itemClicked.connect(self._activate_item)
            self.tree.itemDoubleClicked.connect(self._activate_item)
            self.select_button.clicked.connect(self._activate_current)
            self.clear_button.clicked.connect(lambda: run(self.session, "select clear"))
            self._populate()
            self.tool_window.manage("side")

        def _filter_text(self, item):
            return " ".join(
                str(item.get(key, ""))
                for key in ("name", "label", "category", "atomspec", "comment")
            ).lower()

        def _filter(self, text):
            needle = text.strip().lower()
            self.filtered = [
                item for item in self.selectors if not needle or needle in self._filter_text(item)
            ]
            self._populate()

        def _populate(self):
            self.tree.clear()
            grouped = {}
            for item in self.filtered:
                family = item.get("family") or (
                    "RNA" if "RNA" in item.get("category", "") else "Protein/RNP groups"
                )
                group = item.get("group") or item.get("category") or "other selections"
                grouped.setdefault(family, {}).setdefault(group, []).append(item)

            family_order = ["RNA", "Protein/RNP groups", "Other"]
            for family in sorted(grouped, key=lambda value: (family_order.index(value) if value in family_order else 99, value)):
                family_count = sum(len(items) for items in grouped[family].values())
                family_item = QTreeWidgetItem([f"{family} ({family_count})", "", ""])
                self._style_group_item(family_item, family)
                self.tree.addTopLevelItem(family_item)
                for group in sorted(grouped[family]):
                    rows = sorted(grouped[family][group], key=lambda value: (value.get("label") or value.get("name", "")).lower())
                    group_item = QTreeWidgetItem([f"{group} ({len(rows)})", "", ""])
                    self._style_group_item(group_item, group)
                    family_item.addChild(group_item)
                    for data in rows:
                        label = data.get("label") or data.get("name")
                        atomspec = data.get("atomspec", "")
                        selector = data.get("name", "")
                        row = QTreeWidgetItem([f"  {label}", atomspec, selector])
                        row.setData(0, Qt.UserRole, data)
                        self._style_leaf_item(row, data)
                        group_item.addChild(row)
            self.tree.expandAll()
            for column in range(3):
                self.tree.resizeColumnToContents(column)

        def _style_group_item(self, item, label):
            font = item.font(0)
            font.setBold(True)
            item.setFont(0, font)
            item.setForeground(0, QBrush(QColor("#20242a")))
            item.setBackground(0, QBrush(QColor("#eef2f7")))

        def _style_leaf_item(self, item, data):
            color = QColor(data.get("color") or "#9CA3AF")
            pale = QColor(color)
            pale.setAlpha(45)
            for column in range(3):
                item.setBackground(column, QBrush(pale))
            item.setForeground(0, QBrush(color))
            font = item.font(0)
            font.setBold(True)
            item.setFont(0, font)
            item.setToolTip(
                0,
                f"{data.get('label') or data.get('name')}\n"
                f"{data.get('category', '')} / {data.get('group', '')}\n"
                f"{data.get('comment', '')}",
            )

        def _activate_current(self):
            item = self.tree.currentItem()
            if item is not None:
                self._activate_item(item)

        def _activate_item(self, item, column=0):
            data = item.data(0, Qt.UserRole)
            if not data:
                return
            selector = data.get("name", "")
            if not selector:
                return
            run(self.session, "select clear")
            run(self.session, f"select {selector}")
            run(self.session, "view sel")

    tool_name = f"Spliceosome Selections {spec.get('pdb_id', '').upper()}".strip()
    SpliceosomeSelectionBrowser(session, tool_name, spec, selectors)
    session.logger.info(f"Opened spliceosome named selection browser with {len(selectors)} entries.")

# Embedded named-selection specification for remote execution from GitHub.
_EMBEDDED_SPEC = {
  "pdb_id": "6exn",
  "selectors": [
    {
      "atomspec": "#333.1/H",
      "category": "subcomplex",
      "color": "#EAA439",
      "comment": "EJC/mRNP",
      "family": "Protein/RNP groups",
      "feature": "",
      "group": "EJC/mRNP groups",
      "group_key": "",
      "kind": "subcomplex",
      "label": "EJC/mRNP",
      "name": "pdb_6EXN_EJC_mRNP",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#333.1/K,L,M,N,S,T,y",
      "category": "subcomplex",
      "color": "#F4BF67",
      "comment": "NTC/NTR related",
      "family": "Protein/RNP groups",
      "feature": "",
      "group": "NTC/NTR groups",
      "group_key": "",
      "kind": "subcomplex",
      "label": "NTC/NTR related",
      "name": "pdb_6EXN_NTC_NTR_related",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#333.1/J,O,P,t,u,v,w",
      "category": "subcomplex",
      "color": "#F4BF67",
      "comment": "NTC/PRP19",
      "family": "Protein/RNP groups",
      "feature": "",
      "group": "NTC/NTR groups",
      "group_key": "",
      "kind": "subcomplex",
      "label": "NTC/PRP19",
      "name": "pdb_6EXN_NTC_PRP19",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#333.1/E,I",
      "category": "subcomplex",
      "color": "#303030",
      "comment": "RNA/substrate",
      "family": "RNA",
      "feature": "",
      "group": "pre-mRNA features",
      "group_key": "",
      "kind": "subcomplex",
      "label": "RNA/substrate",
      "name": "pdb_6EXN_RNA_substrate",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#333.1/V,c,o",
      "category": "subcomplex",
      "color": "#9CA3AF",
      "comment": "Second step factors",
      "family": "Protein/RNP groups",
      "feature": "",
      "group": "other protein/RNP groups",
      "group_key": "",
      "kind": "subcomplex",
      "label": "Second step factors",
      "name": "pdb_6EXN_Second_step_factors",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#333.1/k,l,m,n,p,q,r",
      "category": "subcomplex",
      "color": "#BFE6BF",
      "comment": "U2 Sm ring",
      "family": "Protein/RNP groups",
      "feature": "",
      "group": "U2/SF3B groups",
      "group_key": "",
      "kind": "subcomplex",
      "label": "U2 Sm ring",
      "name": "pdb_6EXN_U2_Sm_ring",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#333.1/2,D,W,Y",
      "category": "subcomplex",
      "color": "#2F8B4D",
      "comment": "U2 snRNP",
      "family": "Protein/RNP groups",
      "feature": "",
      "group": "U2/SF3B groups",
      "group_key": "",
      "kind": "subcomplex",
      "label": "U2 snRNP",
      "name": "pdb_6EXN_U2_snRNP",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#333.1/b,d,e,f,g,h,j",
      "category": "subcomplex",
      "color": "#BFC3E8",
      "comment": "U5 Sm ring",
      "family": "Protein/RNP groups",
      "feature": "",
      "group": "U5 snRNP groups",
      "group_key": "",
      "kind": "subcomplex",
      "label": "U5 Sm ring",
      "name": "pdb_6EXN_U5_Sm_ring",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#333.1/5,A,C",
      "category": "subcomplex",
      "color": "#0000CD",
      "comment": "U5 snRNP",
      "family": "Protein/RNP groups",
      "feature": "",
      "group": "U5 snRNP groups",
      "group_key": "",
      "kind": "subcomplex",
      "label": "U5 snRNP",
      "name": "pdb_6EXN_U5_snRNP",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#333.1/6",
      "category": "subcomplex",
      "color": "#DC143C",
      "comment": "U6 snRNP",
      "family": "Protein/RNP groups",
      "feature": "",
      "group": "U6 snRNP groups",
      "group_key": "",
      "kind": "subcomplex",
      "label": "U6 snRNP",
      "name": "pdb_6EXN_U6_snRNP",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#333.1/R,X,a,s",
      "category": "subcomplex",
      "color": "#9CA3AF",
      "comment": "other",
      "family": "Protein/RNP groups",
      "feature": "",
      "group": "other protein/RNP groups",
      "group_key": "",
      "kind": "subcomplex",
      "label": "other",
      "name": "pdb_6EXN_other",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#333.1/E:-14,-13,-12,-11,-10,-9,-8,-7,-6,-5,-4,-3,-2,-1,1,2,3,4,5,6,7,8,9,10,11,12,13,15-19",
      "category": "substrate RNA feature",
      "color": "#FF8C00",
      "comment": "ligated exons: residues -14,-13,-12,-11,-10,-9,-8,-7,-6,-5,-4,-3,-2,-1,1,2,3,4,5,6,7,8,9,10,11,12,13;15-19, component-name, high confidence, validation not_applicable",
      "family": "RNA",
      "feature": "ligated_exons",
      "group": "pre-mRNA features",
      "group_key": "pre_mRNA_features",
      "kind": "rna_feature",
      "label": "ligated exons",
      "name": "P_6EXN_ligated_exons",
      "section": "Named selections for resolved substrate RNA features."
    },
    {
      "atomspec": "#333.1/E:-14,-13,-12,-11,-10,-9,-8,-7,-6,-5,-4,-3,-2,-1,1,2,3,4,5,6,7,8,9,10,11,12,13,15-19|#333.1/I:1-16,56-73,91-95",
      "category": "substrate RNA feature",
      "color": "#303030",
      "comment": "substrate RNA: residues -14,-13,-12,-11,-10,-9,-8,-7,-6,-5,-4,-3,-2,-1,1,2,3,4,5,6,7,8,9,10,11,12,13;15-19; 1-16;56-73;91-95, component, medium confidence, validation not_applicable",
      "family": "RNA",
      "feature": "substrate",
      "group": "pre-mRNA features",
      "group_key": "pre_mRNA_features",
      "kind": "rna_feature",
      "label": "substrate RNA",
      "name": "P_6EXN_substrate",
      "section": "Named selections for resolved substrate RNA features."
    },
    {
      "atomspec": "#333.1/E:-14--12",
      "category": "substrate RNA feature",
      "color": "#303030",
      "comment": "5' splice site: residues -14--12, sequence-motif, medium confidence, validation uncertain uncertain validation",
      "family": "RNA",
      "feature": "five_prime_splice_site",
      "group": "pre-mRNA features",
      "group_key": "pre_mRNA_features",
      "kind": "rna_feature",
      "label": "5' splice site",
      "name": "P_6EXN_5SS",
      "section": "Named selections for resolved substrate RNA features."
    },
    {
      "atomspec": "#333.1/E:-14,-13,-12,-11,-10,-9,-8,-7,-6,-5,-4,-3,-2,-1,1,2,3,4,5,6,7,8,9,10,11,12,13,15-19|#333.1/I:1-16,56-73,91-95",
      "category": "substrate RNA feature",
      "color": "#303030",
      "comment": "intron from 5' splice site: residues -14,-13,-12,-11,-10,-9,-8,-7,-6,-5,-4,-3,-2,-1,1,2,3,4,5,6,7,8,9,10,11,12,13;15-19; 1-16;56-73;91-95, component-name/five-ss-inference, high/low confidence, validation not_applicable",
      "family": "RNA",
      "feature": "intron",
      "group": "pre-mRNA features",
      "group_key": "pre_mRNA_features",
      "kind": "rna_feature",
      "label": "intron from 5' splice site",
      "name": "P_6EXN_intron",
      "section": "Named selections for resolved substrate RNA features."
    },
    {
      "atomspec": "#333.1/E:-14--1",
      "category": "substrate RNA feature",
      "color": "#FF8C00",
      "comment": "5' exon: residues -14--1, auth-residue-numbering, high confidence, validation not_applicable",
      "family": "RNA",
      "feature": "exon_5",
      "group": "pre-mRNA features",
      "group_key": "pre_mRNA_features",
      "kind": "rna_feature",
      "label": "5' exon",
      "name": "P_6EXN_5exon",
      "section": "Named selections for resolved substrate RNA features."
    },
    {
      "atomspec": "#333.1/E:1-13,15-19",
      "category": "substrate RNA feature",
      "color": "#D97706",
      "comment": "3' exon: residues 1-13;15-19, auth-residue-numbering, high confidence, validation not_applicable",
      "family": "RNA",
      "feature": "exon_3",
      "group": "pre-mRNA features",
      "group_key": "pre_mRNA_features",
      "kind": "rna_feature",
      "label": "3' exon",
      "name": "P_6EXN_3exon",
      "section": "Named selections for resolved substrate RNA features."
    },
    {
      "atomspec": "#333.1/I:1-16,56-73,91-95",
      "category": "substrate RNA feature",
      "color": "#303030",
      "comment": "intron lariat: residues 1-16;56-73;91-95, component-name, high confidence, validation not_applicable",
      "family": "RNA",
      "feature": "intron_lariat",
      "group": "pre-mRNA features",
      "group_key": "pre_mRNA_features",
      "kind": "rna_feature",
      "label": "intron lariat",
      "name": "P_6EXN_intron_lariat",
      "section": "Named selections for resolved substrate RNA features."
    },
    {
      "atomspec": "#333.1/I:62-72",
      "category": "substrate RNA feature",
      "color": "#303030",
      "comment": "branch point region: residues 62-72, network-scored-motif, high confidence, validation validated",
      "family": "RNA",
      "feature": "branch_point_region",
      "group": "pre-mRNA features",
      "group_key": "pre_mRNA_features",
      "kind": "rna_feature",
      "label": "branch point region",
      "name": "P_6EXN_branch_region",
      "section": "Named selections for resolved substrate RNA features."
    },
    {
      "atomspec": "#333.1/I:70",
      "category": "substrate RNA feature",
      "color": "#303030",
      "comment": "branch point adenosine: residues 70, network-scored-motif, high confidence, validation validated",
      "family": "RNA",
      "feature": "branch_point_adenosine",
      "group": "pre-mRNA features",
      "group_key": "pre_mRNA_features",
      "kind": "rna_feature",
      "label": "branch point adenosine",
      "name": "P_6EXN_branch_A",
      "section": "Named selections for resolved substrate RNA features."
    },
    {
      "atomspec": "#333.1/I:93-95",
      "category": "substrate RNA feature",
      "color": "#303030",
      "comment": "3' splice site: residues 93-95, sequence-motif, medium confidence, validation validated",
      "family": "RNA",
      "feature": "three_prime_splice_site",
      "group": "pre-mRNA features",
      "group_key": "pre_mRNA_features",
      "kind": "rna_feature",
      "label": "3' splice site",
      "name": "P_6EXN_3SS",
      "section": "Named selections for resolved substrate RNA features."
    },
    {
      "atomspec": "#333.1/2:26-30",
      "category": "snRNA feature",
      "color": "#047857",
      "comment": "U2 snRNA U2/U6 helix I partner: residues 26-30, review-region, high confidence",
      "family": "RNA",
      "feature": "U2_U6_helix_I_partner",
      "group": "snRNA-snRNA interacting regions",
      "group_key": "snRNA_snRNA_regions",
      "kind": "rna_feature",
      "label": "U2 snRNA U2/U6 helix I partner",
      "name": "P_6EXN_U2_U6_helix_I_partner",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#333.1/2:33-42",
      "category": "snRNA feature",
      "color": "#0B6E2D",
      "comment": "U2 snRNA branchpoint pairing region: residues 33-42, sequence-motif-neighborhood, medium confidence",
      "family": "RNA",
      "feature": "U2_branchpoint_pairing_region",
      "group": "snRNA-pre-mRNA regions",
      "group_key": "snRNA_pre_mRNA_regions",
      "kind": "rna_feature",
      "label": "U2 snRNA branchpoint pairing region",
      "name": "P_6EXN_U2_branchpoint_pairing_region",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#333.1/2:46-48,54-60",
      "category": "snRNA feature",
      "color": "#167A38",
      "comment": "U2 snRNA stem IIa: residues 46-48;54-60, review-region, low confidence",
      "family": "RNA",
      "feature": "U2_stem_IIa",
      "group": "internal stem loops",
      "group_key": "internal_stem_loops",
      "kind": "rna_feature",
      "label": "U2 snRNA stem IIa",
      "name": "P_6EXN_U2_stem_IIa",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#333.1/5:53-57",
      "category": "snRNA feature",
      "color": "#1B3CD0",
      "comment": "U5 snRNA loop I: residues 53-57, sequence-motif, medium confidence",
      "family": "RNA",
      "feature": "U5_loop_I",
      "group": "snRNA-pre-mRNA regions",
      "group_key": "snRNA_pre_mRNA_regions",
      "kind": "rna_feature",
      "label": "U5 snRNA loop I",
      "name": "P_6EXN_U5_loop_I",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#333.1/6:1-30",
      "category": "snRNA feature",
      "color": "#DC143C",
      "comment": "U6 snRNA 5' terminal stem-loop: residues 1-30, reference-alignment, high confidence",
      "family": "RNA",
      "feature": "U6_5prime_terminal_stem_loop",
      "group": "internal stem loops",
      "group_key": "internal_stem_loops",
      "kind": "rna_feature",
      "label": "U6 snRNA 5' terminal stem-loop",
      "name": "P_6EXN_U6_5_terminal_stem_loop",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#333.1/6:41-66",
      "category": "snRNA feature",
      "color": "#D0183C",
      "comment": "U6 snRNA U2/U6 helix I partner: residues 41-66, motif-neighborhood, medium confidence",
      "family": "RNA",
      "feature": "U6_U2_helix_I_partner",
      "group": "snRNA-snRNA interacting regions",
      "group_key": "snRNA_snRNA_regions",
      "kind": "rna_feature",
      "label": "U6 snRNA U2/U6 helix I partner",
      "name": "P_6EXN_U6_U2_helix_I_partner",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#333.1/6:44-55",
      "category": "snRNA feature",
      "color": "#E01842",
      "comment": "U6 snRNA 5' splice-site upstream contact: residues 44-55, motif-neighborhood, medium confidence",
      "family": "RNA",
      "feature": "U6_5SS_upstream_contact",
      "group": "other snRNA regions",
      "group_key": "other_snRNA_regions",
      "kind": "rna_feature",
      "label": "U6 snRNA 5' splice-site upstream contact",
      "name": "P_6EXN_U6_5SS_upstream_contact",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#333.1/6:46-73",
      "category": "snRNA feature",
      "color": "#D61A3D",
      "comment": "U6 snRNA internal stem-loop: residues 46-73, motif-neighborhood, low confidence",
      "family": "RNA",
      "feature": "U6_ISL",
      "group": "internal stem loops",
      "group_key": "internal_stem_loops",
      "kind": "rna_feature",
      "label": "U6 snRNA internal stem-loop",
      "name": "P_6EXN_U6_ISL",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#333.1/6:47-53",
      "category": "snRNA feature",
      "color": "#DC143C",
      "comment": "U6 snRNA ACAGAGA box: residues 47-53, sequence-motif, high confidence",
      "family": "RNA",
      "feature": "U6_ACAGAGA_box",
      "group": "other snRNA regions",
      "group_key": "other_snRNA_regions",
      "kind": "rna_feature",
      "label": "U6 snRNA ACAGAGA box",
      "name": "P_6EXN_U6_ACAGAGA_box",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#333.1/6:59-61",
      "category": "snRNA feature",
      "color": "#C91236",
      "comment": "U6 snRNA AGC catalytic triad: residues 59-61, sequence-motif, medium confidence",
      "family": "RNA",
      "feature": "U6_AGC_catalytic_triad",
      "group": "catalytic core regions",
      "group_key": "catalytic_core_regions",
      "kind": "rna_feature",
      "label": "U6 snRNA AGC catalytic triad",
      "name": "P_6EXN_U6_AGC_catalytic_triad",
      "section": "Named selections for resolved snRNA functional regions."
    }
  ],
  "structure_group_id": "333",
  "structure_model_id": "333.1"
}

import os as _os
import tempfile as _tempfile
_fd, _spec_path = _tempfile.mkstemp(prefix='spliceosome_named_selections_', suffix='.json')
try:
    with _os.fdopen(_fd, 'w', encoding='utf-8') as _handle:
        json.dump(_EMBEDDED_SPEC, _handle)
    open_selection_browser(session, _spec_path)
finally:
    try:
        _os.remove(_spec_path)
    except OSError:
        pass
