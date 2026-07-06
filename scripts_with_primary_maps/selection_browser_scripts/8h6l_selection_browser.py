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
  "pdb_id": "8h6l",
  "selectors": [
    {
      "atomspec": "#382.1/A",
      "category": "subcomplex",
      "color": "#303030",
      "comment": "RNA/substrate",
      "family": "RNA",
      "feature": "",
      "group": "pre-mRNA features",
      "group_key": "",
      "kind": "subcomplex",
      "label": "RNA/substrate",
      "name": "pdb_8H6L_RNA_substrate",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#382.1/2a,2b,2c,2d,2e,2f,2g",
      "category": "subcomplex",
      "color": "#BFE6BF",
      "comment": "U2 Sm ring",
      "family": "Protein/RNP groups",
      "feature": "",
      "group": "U2/SF3B groups",
      "group_key": "",
      "kind": "subcomplex",
      "label": "U2 Sm ring",
      "name": "pdb_8H6L_U2_Sm_ring",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#382.1/2A,2B,2C",
      "category": "subcomplex",
      "color": "#2F8B4D",
      "comment": "U2 snRNP",
      "family": "Protein/RNP groups",
      "feature": "",
      "group": "U2/SF3B groups",
      "group_key": "",
      "kind": "subcomplex",
      "label": "U2 snRNP",
      "name": "pdb_8H6L_U2_snRNP",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#382.1/2D,2E,2F,2G,2H,2I,2J,2K,2L,2M",
      "category": "subcomplex",
      "color": "#6DBE70",
      "comment": "U2/SF3B",
      "family": "Protein/RNP groups",
      "feature": "",
      "group": "U2/SF3B groups",
      "group_key": "",
      "kind": "subcomplex",
      "label": "U2/SF3B",
      "name": "pdb_8H6L_U2_SF3B",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#382.1/4a,4b,4c,4d,4e,4f,4g",
      "category": "subcomplex",
      "color": "#F5E85A",
      "comment": "U4 Sm ring",
      "family": "Protein/RNP groups",
      "feature": "",
      "group": "U4 snRNP groups",
      "group_key": "",
      "kind": "subcomplex",
      "label": "U4 Sm ring",
      "name": "pdb_8H6L_U4_Sm_ring",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#382.1/4A",
      "category": "subcomplex",
      "color": "#D8C800",
      "comment": "U4 snRNP",
      "family": "Protein/RNP groups",
      "feature": "",
      "group": "U4 snRNP groups",
      "group_key": "",
      "kind": "subcomplex",
      "label": "U4 snRNP",
      "name": "pdb_8H6L_U4_snRNP",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#382.1/4B,4C,4D,4E,4F",
      "category": "subcomplex",
      "color": "#C3BA7A",
      "comment": "U4/U6 snRNP",
      "family": "Protein/RNP groups",
      "feature": "",
      "group": "U4/U6 groups",
      "group_key": "",
      "kind": "subcomplex",
      "label": "U4/U6 snRNP",
      "name": "pdb_8H6L_U4_U6_snRNP",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#382.1/5a,5b,5c,5d,5e,5f,5g",
      "category": "subcomplex",
      "color": "#BFC3E8",
      "comment": "U5 Sm ring",
      "family": "Protein/RNP groups",
      "feature": "",
      "group": "U5 snRNP groups",
      "group_key": "",
      "kind": "subcomplex",
      "label": "U5 Sm ring",
      "name": "pdb_8H6L_U5_Sm_ring",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#382.1/4G,4J,5A,5B,5C,5D,5E",
      "category": "subcomplex",
      "color": "#0000CD",
      "comment": "U5 snRNP",
      "family": "Protein/RNP groups",
      "feature": "",
      "group": "U5 snRNP groups",
      "group_key": "",
      "kind": "subcomplex",
      "label": "U5 snRNP",
      "name": "pdb_8H6L_U5_snRNP",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#382.1/6a,6b,6c,6d,6e,6f,6g",
      "category": "subcomplex",
      "color": "#FECACA",
      "comment": "U6 LSm",
      "family": "Protein/RNP groups",
      "feature": "",
      "group": "U6 snRNP groups",
      "group_key": "",
      "kind": "subcomplex",
      "label": "U6 LSm",
      "name": "pdb_8H6L_U6_LSm",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#382.1/6A",
      "category": "subcomplex",
      "color": "#DC143C",
      "comment": "U6 snRNP",
      "family": "Protein/RNP groups",
      "feature": "",
      "group": "U6 snRNP groups",
      "group_key": "",
      "kind": "subcomplex",
      "label": "U6 snRNP",
      "name": "pdb_8H6L_U6_snRNP",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#382.1/4H,4I,4Z",
      "category": "subcomplex",
      "color": "#9CA3AF",
      "comment": "other",
      "family": "Protein/RNP groups",
      "feature": "",
      "group": "other protein/RNP groups",
      "group_key": "",
      "kind": "subcomplex",
      "label": "other",
      "name": "pdb_8H6L_other",
      "section": "Named selections for subcomplexes using original deposited chain IDs."
    },
    {
      "atomspec": "#382.1/A:7-48",
      "category": "substrate RNA feature",
      "color": "#303030",
      "comment": "upstream intron: residues 7-48, exon-definition-inference, medium confidence, validation not_applicable",
      "family": "RNA",
      "feature": "intron",
      "group": "pre-mRNA features",
      "group_key": "pre_mRNA_features",
      "kind": "rna_feature",
      "label": "upstream intron",
      "name": "B_8H6L_intron",
      "section": "Named selections for resolved substrate RNA features."
    },
    {
      "atomspec": "#382.1/A:7-48,102-116",
      "category": "substrate RNA feature",
      "color": "#303030",
      "comment": "substrate RNA: residues 7-48;102-116, component, medium confidence, validation not_applicable",
      "family": "RNA",
      "feature": "substrate",
      "group": "pre-mRNA features",
      "group_key": "pre_mRNA_features",
      "kind": "rna_feature",
      "label": "substrate RNA",
      "name": "B_8H6L_substrate",
      "section": "Named selections for resolved substrate RNA features."
    },
    {
      "atomspec": "#382.1/A:24-30",
      "category": "substrate RNA feature",
      "color": "#303030",
      "comment": "branch point region: residues 24-30, network-scored-motif, high confidence, validation validated",
      "family": "RNA",
      "feature": "branch_point_region",
      "group": "pre-mRNA features",
      "group_key": "pre_mRNA_features",
      "kind": "rna_feature",
      "label": "branch point region",
      "name": "B_8H6L_branch_region",
      "section": "Named selections for resolved substrate RNA features."
    },
    {
      "atomspec": "#382.1/A:29",
      "category": "substrate RNA feature",
      "color": "#303030",
      "comment": "branch point adenosine: residues 29, network-scored-motif, high confidence, validation validated",
      "family": "RNA",
      "feature": "branch_point_adenosine",
      "group": "pre-mRNA features",
      "group_key": "pre_mRNA_features",
      "kind": "rna_feature",
      "label": "branch point adenosine",
      "name": "B_8H6L_branch_A",
      "section": "Named selections for resolved substrate RNA features."
    },
    {
      "atomspec": "#382.1/A:35-48",
      "category": "substrate RNA feature",
      "color": "#303030",
      "comment": "polypyrimidine tract: residues 35-48, sequence-motif, medium confidence, validation validated",
      "family": "RNA",
      "feature": "polypyrimidine_tract",
      "group": "pre-mRNA features",
      "group_key": "pre_mRNA_features",
      "kind": "rna_feature",
      "label": "polypyrimidine tract",
      "name": "B_8H6L_PPT",
      "section": "Named selections for resolved substrate RNA features."
    },
    {
      "atomspec": "#382.1/A:102-107",
      "category": "substrate RNA feature",
      "color": "#FF8C00",
      "comment": "exon-defined exon: residues 102-107, exon-definition-inference, medium confidence, validation not_applicable",
      "family": "RNA",
      "feature": "exon_defined_exon",
      "group": "pre-mRNA features",
      "group_key": "pre_mRNA_features",
      "kind": "rna_feature",
      "label": "exon-defined exon",
      "name": "B_8H6L_exon",
      "section": "Named selections for resolved substrate RNA features."
    },
    {
      "atomspec": "#382.1/A:108-113",
      "category": "substrate RNA feature",
      "color": "#303030",
      "comment": "5' splice site: residues 108-113, sequence-motif, medium confidence, validation uncertain uncertain validation",
      "family": "RNA",
      "feature": "five_prime_splice_site",
      "group": "pre-mRNA features",
      "group_key": "pre_mRNA_features",
      "kind": "rna_feature",
      "label": "5' splice site",
      "name": "B_8H6L_5SS",
      "section": "Named selections for resolved substrate RNA features."
    },
    {
      "atomspec": "#382.1/2A:30",
      "category": "snRNA feature",
      "color": "#047857",
      "comment": "U2 snRNA U2/U6 helix I partner: residues 30, review-region, high confidence",
      "family": "RNA",
      "feature": "U2_U6_helix_I_partner",
      "group": "snRNA-snRNA interacting regions",
      "group_key": "snRNA_snRNA_regions",
      "kind": "rna_feature",
      "label": "U2 snRNA U2/U6 helix I partner",
      "name": "B_8H6L_U2_U6_helix_I_partner",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#382.1/2A:32-41",
      "category": "snRNA feature",
      "color": "#0B6E2D",
      "comment": "U2 snRNA branchpoint pairing region: residues 32-41, sequence-motif-neighborhood, medium confidence",
      "family": "RNA",
      "feature": "U2_branchpoint_pairing_region",
      "group": "snRNA-pre-mRNA regions",
      "group_key": "snRNA_pre_mRNA_regions",
      "kind": "rna_feature",
      "label": "U2 snRNA branchpoint pairing region",
      "name": "B_8H6L_U2_branchpoint_pairing_region",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#382.1/2A:46-65",
      "category": "snRNA feature",
      "color": "#167A38",
      "comment": "U2 snRNA stem IIa: residues 46-65, review-region, low confidence",
      "family": "RNA",
      "feature": "U2_stem_IIa",
      "group": "internal stem loops",
      "group_key": "internal_stem_loops",
      "kind": "rna_feature",
      "label": "U2 snRNA stem IIa",
      "name": "B_8H6L_U2_stem_IIa",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#382.1/2A:99-105",
      "category": "snRNA feature",
      "color": "#2F8B4D",
      "comment": "U2 snRNA Sm site: residues 99-105, sequence-motif, medium confidence",
      "family": "RNA",
      "feature": "U2_Sm_site",
      "group": "other snRNA regions",
      "group_key": "other_snRNA_regions",
      "kind": "rna_feature",
      "label": "U2 snRNA Sm site",
      "name": "B_8H6L_U2_Sm_site",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#382.1/4A:1-18",
      "category": "snRNA feature",
      "color": "#D8C800",
      "comment": "U4 snRNA U4/U6 stem I partner: residues 1-18, reference-alignment, high confidence",
      "family": "RNA",
      "feature": "U4_U6_stem_I_partner",
      "group": "snRNA-snRNA interacting regions",
      "group_key": "snRNA_snRNA_regions",
      "kind": "rna_feature",
      "label": "U4 snRNA U4/U6 stem I partner",
      "name": "B_8H6L_U4_U6_stem_I_partner",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#382.1/4A:56-63",
      "category": "snRNA feature",
      "color": "#E0CF1A",
      "comment": "U4 snRNA U4/U6 stem II partner: residues 56-63, reference-alignment, high confidence",
      "family": "RNA",
      "feature": "U4_U6_stem_II_partner",
      "group": "snRNA-snRNA interacting regions",
      "group_key": "snRNA_snRNA_regions",
      "kind": "rna_feature",
      "label": "U4 snRNA U4/U6 stem II partner",
      "name": "B_8H6L_U4_U6_stem_II_partner",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#382.1/4A:59-63,70-76,83-94",
      "category": "snRNA feature",
      "color": "#F0DF2E",
      "comment": "U4 snRNA Brr2 loading region: residues 59-63;70-76;83-94, review-region, low confidence",
      "family": "RNA",
      "feature": "U4_Brr2_loading_region",
      "group": "other snRNA regions",
      "group_key": "other_snRNA_regions",
      "kind": "rna_feature",
      "label": "U4 snRNA Brr2 loading region",
      "name": "B_8H6L_U4_Brr2_loading_region",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#382.1/4A:118-124",
      "category": "snRNA feature",
      "color": "#F5E85A",
      "comment": "U4 snRNA Sm site: residues 118-124, sequence-motif, medium confidence",
      "family": "RNA",
      "feature": "U4_Sm_site",
      "group": "other snRNA regions",
      "group_key": "other_snRNA_regions",
      "kind": "rna_feature",
      "label": "U4 snRNA Sm site",
      "name": "B_8H6L_U4_Sm_site",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#382.1/5A:38-42",
      "category": "snRNA feature",
      "color": "#1B3CD0",
      "comment": "U5 snRNA loop I: residues 38-42, sequence-motif, medium confidence",
      "family": "RNA",
      "feature": "U5_loop_I",
      "group": "snRNA-pre-mRNA regions",
      "group_key": "snRNA_pre_mRNA_regions",
      "kind": "rna_feature",
      "label": "U5 snRNA loop I",
      "name": "B_8H6L_U5_loop_I",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#382.1/6A:36-60",
      "category": "snRNA feature",
      "color": "#D0183C",
      "comment": "U6 snRNA U2/U6 helix I partner: residues 36-60, motif-neighborhood, medium confidence",
      "family": "RNA",
      "feature": "U6_U2_helix_I_partner",
      "group": "snRNA-snRNA interacting regions",
      "group_key": "snRNA_snRNA_regions",
      "kind": "rna_feature",
      "label": "U6 snRNA U2/U6 helix I partner",
      "name": "B_8H6L_U6_U2_helix_I_partner",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#382.1/6A:38-49",
      "category": "snRNA feature",
      "color": "#E01842",
      "comment": "U6 snRNA 5' splice-site upstream contact: residues 38-49, motif-neighborhood, medium confidence",
      "family": "RNA",
      "feature": "U6_5SS_upstream_contact",
      "group": "other snRNA regions",
      "group_key": "other_snRNA_regions",
      "kind": "rna_feature",
      "label": "U6 snRNA 5' splice-site upstream contact",
      "name": "B_8H6L_U6_5SS_upstream_contact",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#382.1/6A:41-47",
      "category": "snRNA feature",
      "color": "#DC143C",
      "comment": "U6 snRNA ACAGAGA box: residues 41-47, sequence-motif, high confidence",
      "family": "RNA",
      "feature": "U6_ACAGAGA_box",
      "group": "other snRNA regions",
      "group_key": "other_snRNA_regions",
      "kind": "rna_feature",
      "label": "U6 snRNA ACAGAGA box",
      "name": "B_8H6L_U6_ACAGAGA_box",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#382.1/6A:52-61",
      "category": "snRNA feature",
      "color": "#E01842",
      "comment": "U6 snRNA U4/U6 stem II partner: residues 52-61, reference-alignment, high confidence",
      "family": "RNA",
      "feature": "U6_U4_stem_II_partner",
      "group": "other snRNA regions",
      "group_key": "other_snRNA_regions",
      "kind": "rna_feature",
      "label": "U6 snRNA U4/U6 stem II partner",
      "name": "B_8H6L_U6_U4_stem_II_partner",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#382.1/6A:63-74",
      "category": "snRNA feature",
      "color": "#D9183E",
      "comment": "U6 snRNA U4/U6 stem I partner: residues 63-74, reference-alignment, high confidence",
      "family": "RNA",
      "feature": "U6_U4_stem_I_partner",
      "group": "other snRNA regions",
      "group_key": "other_snRNA_regions",
      "kind": "rna_feature",
      "label": "U6 snRNA U4/U6 stem I partner",
      "name": "B_8H6L_U6_U4_stem_I_partner",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#382.1/6A:85-96,102-105",
      "category": "snRNA feature",
      "color": "#D61A3D",
      "comment": "U6 snRNA internal stem-loop: residues 85-96;102-105, motif-neighborhood, low confidence",
      "family": "RNA",
      "feature": "U6_ISL",
      "group": "internal stem loops",
      "group_key": "internal_stem_loops",
      "kind": "rna_feature",
      "label": "U6 snRNA internal stem-loop",
      "name": "B_8H6L_U6_ISL",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#382.1/6A:92-94",
      "category": "snRNA feature",
      "color": "#C91236",
      "comment": "U6 snRNA AGC catalytic triad: residues 92-94, sequence-motif, medium confidence",
      "family": "RNA",
      "feature": "U6_AGC_catalytic_triad",
      "group": "catalytic core regions",
      "group_key": "catalytic_core_regions",
      "kind": "rna_feature",
      "label": "U6 snRNA AGC catalytic triad",
      "name": "B_8H6L_U6_AGC_catalytic_triad",
      "section": "Named selections for resolved snRNA functional regions."
    },
    {
      "atomspec": "#382.1/6A:102-105",
      "category": "snRNA feature",
      "color": "#E33A55",
      "comment": "U6 snRNA LSm site: residues 102-105, terminal-region, low confidence",
      "family": "RNA",
      "feature": "U6_LSm_site",
      "group": "other snRNA regions",
      "group_key": "other_snRNA_regions",
      "kind": "rna_feature",
      "label": "U6 snRNA LSm site",
      "name": "B_8H6L_U6_LSm_site",
      "section": "Named selections for resolved snRNA functional regions."
    }
  ],
  "structure_group_id": "382",
  "structure_model_id": "382.1"
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
