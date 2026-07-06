#!/usr/bin/env python3
"""Create RNA feature labels as one ChimeraX model per label.

This helper is called from generated ChimeraX command scripts.  The standard
`label` command stores all residue labels for one structure in a single child
model, which prevents toggling individual labels in the Model Panel.
"""

from __future__ import annotations

import json
import sys

from chimerax.core.colors import Color
from chimerax.core.commands import ObjectsArg
from chimerax.core.models import Model
from chimerax.label.label3d import ObjectLabels, label_class


OUTLINE_OFFSETS = (
    (-0.085, 0, 0),
    (0.085, 0, 0),
    (0, -0.085, 0),
    (0, 0.085, 0),
    (-0.060, -0.060, 0),
    (-0.060, 0.060, 0),
    (0.060, -0.060, 0),
    (0.060, 0.060, 0),
    (-0.052, 0, 0),
    (0.052, 0, 0),
    (0, -0.052, 0),
    (0, 0.052, 0),
    (-0.037, -0.037, 0),
    (-0.037, 0.037, 0),
    (0.037, -0.037, 0),
    (0.037, 0.037, 0),
)


def _id_tuple(model_id: str) -> tuple[int, ...]:
    return tuple(int(part) for part in str(model_id).split(".") if part)


def _model_by_id(session, model_id: str):
    models = session.models.list(model_id=_id_tuple(model_id))
    return models[0] if models else None


def _parent_model_id(model_id: str) -> str | None:
    parts = str(model_id).split(".")
    return ".".join(parts[:-1]) if len(parts) > 1 else None


def _parse_residues(session, atomspec: str):
    objects, _used, rest = ObjectsArg.parse(atomspec, session)
    if rest.strip():
        raise ValueError(f"Could not parse complete atom specifier: {atomspec!r}")
    return list(objects.residues)


def _color_uint8(color_spec: str):
    return Color(color_spec).uint8x4()


def _category_key(label: dict) -> str:
    return label.get("category_key") or "other_RNA_features"


def _category_name(label: dict) -> str:
    return label.get("category_name") or _category_key(label).replace("_", " ")


def create_label_models(session, spec_path: str) -> None:
    with open(spec_path, "r", encoding="utf-8") as handle:
        spec = json.load(handle)

    structure_id = spec["structure_model_id"]
    structure = _model_by_id(session, structure_id)
    if structure is None:
        raise ValueError(f"Structure model #{structure_id} is not open")

    group_id = spec.get("label_group_model_id") or f"{structure_id}.{spec.get('label_group_child_id', 90)}"
    cleanup_ids = [group_id] + spec.get("cleanup_model_ids", [])
    for cleanup_id in cleanup_ids:
        old_group = _model_by_id(session, cleanup_id)
        if old_group is not None:
            session.models.close([old_group])

    group = Model(spec.get("label_group_name", "RNA_feature_labels"), session)
    group.id = _id_tuple(group_id)
    parent_id = _parent_model_id(group_id)
    parent = _model_by_id(session, parent_id) if parent_id else None
    if parent is None:
        parent = structure
    if parent is not structure:
        group.position = structure.position
    session.models.add([group], parent=parent)

    view = session.main_view
    height = spec.get("height", 3)
    size = spec.get("size", 96)
    background_spec = spec.get("background")
    background = None if background_spec in (None, "", "none") else _color_uint8(background_spec)
    outline_color = _color_uint8(spec.get("outline_color", "#ffffff"))
    outline_offsets = spec.get("outline_offsets", OUTLINE_OFFSETS)
    visible_category_keys = set(spec.get("default_visible_category_keys", []))
    visible_category_names = set(spec.get("default_visible_category_names", []))

    category_models = {}
    category_counts = {}
    created = 0
    for label in spec.get("labels", []):
        residues = _parse_residues(session, label["atomspec"])
        if not residues:
            session.logger.warning(f"No residues found for RNA label atom specifier {label['atomspec']!r}")
            continue

        category_key = _category_key(label)
        if category_key not in category_models:
            category_index = len(category_models) + 1
            category_name = _category_name(label)
            category_group = Model(category_name, session)
            category_group.id = _id_tuple(f"{group_id}.{category_index}")
            session.models.add([category_group], parent=group)
            if visible_category_keys or visible_category_names:
                category_group.display = category_key in visible_category_keys or category_name in visible_category_names
            category_models[category_key] = (category_group, category_index)
            category_counts[category_key] = 0

        category_group, category_index = category_models[category_key]
        category_counts[category_key] += 1
        feature_index = category_counts[category_key]
        feature_id = f"{group_id}.{category_index}.{feature_index}"

        feature_group = Model(label["model_name"], session)
        feature_group.id = _id_tuple(feature_id)
        session.models.add([feature_group], parent=category_group)

        for outline_index, offset in enumerate(outline_offsets, start=1):
            outline_model = ObjectLabels(session)
            outline_model.name = f"{label['model_name']}_outline_{outline_index:02d}"
            outline_model.id = _id_tuple(f"{feature_id}.{outline_index}")
            session.models.add([outline_model], parent=feature_group)
            outline_settings = {
                "text": label["text"],
                "color": outline_color,
                "background": None,
                "height": height,
                "size": size,
                "offset": tuple(offset),
                "position": "centroid",
            }
            outline_model.add_labels(residues, label_class(residues[0]), view, outline_settings, on_top=True)

        foreground_model = ObjectLabels(session)
        foreground_model.name = f"{label['model_name']}_text"
        foreground_model.id = _id_tuple(f"{feature_id}.{len(outline_offsets) + 1}")
        session.models.add([foreground_model], parent=feature_group)
        foreground_settings = {
            "text": label["text"],
            "color": _color_uint8(label["color"]),
            "background": background,
            "height": height,
            "size": size,
            "position": "centroid",
        }
        foreground_model.add_labels(residues, label_class(residues[0]), view, foreground_settings, on_top=True)
        created += 1

    session.logger.info(f"Created {created} independently togglable RNA feature label models under #{group_id}")

# Embedded label specification for remote execution from GitHub.
_EMBEDDED_SPEC = {
  "background": "none",
  "cleanup_model_ids": [
    "391.1.90"
  ],
  "default_visible_category_keys": [
    "pre_mRNA_features",
    "snRNA_pre_mRNA_regions"
  ],
  "default_visible_category_names": [
    "pre-mRNA features",
    "snRNA-pre-mRNA regions"
  ],
  "height": 3.35,
  "label_group_model_id": "391.2",
  "label_group_name": "RNA_feature_labels",
  "labels": [
    {
      "atomspec": "#391.1/Z:54",
      "category_key": "pre_mRNA_features",
      "category_model_id": "391.2.1",
      "category_name": "pre-mRNA features",
      "color": "#FF8C00",
      "default_visible": true,
      "feature": "exon_5",
      "index": 1,
      "label_model_id": "391.2.1.1",
      "model_name": "label_01_5_exon_res_49_58",
      "selector_name": "B_8Q7N_5exon",
      "text": "5' exon (res. 49-58)"
    },
    {
      "atomspec": "#391.1/Z:62",
      "category_key": "pre_mRNA_features",
      "category_model_id": "391.2.1",
      "category_name": "pre-mRNA features",
      "color": "#303030",
      "default_visible": true,
      "feature": "five_prime_splice_site",
      "index": 2,
      "label_model_id": "391.2.1.2",
      "model_name": "label_02_5_SS_res_59_64",
      "selector_name": "B_8Q7N_5SS",
      "text": "? 5'SS (res. 59-64)"
    },
    {
      "atomspec": "#391.1/Z:69",
      "category_key": "pre_mRNA_features",
      "category_model_id": "391.2.1",
      "category_name": "pre-mRNA features",
      "color": "#303030",
      "default_visible": true,
      "feature": "intron",
      "index": 3,
      "label_model_id": "391.2.1.3",
      "model_name": "label_03_intron_res_59_79",
      "selector_name": "B_8Q7N_intron",
      "text": "intron (res. 59-79)"
    },
    {
      "atomspec": "#391.1/4:10",
      "category_key": "snRNA_snRNA_regions",
      "category_model_id": "391.2.2",
      "category_name": "snRNA-snRNA interacting regions",
      "color": "#D8C800",
      "default_visible": false,
      "feature": "U4_U6_stem_I_partner",
      "index": 4,
      "label_model_id": "391.2.2.1",
      "model_name": "label_04_U4_U6_stem_I_res_1_18",
      "selector_name": "B_8Q7N_U4_U6_stem_I_partner",
      "text": "U4/U6 stem I (res. 1-18)"
    },
    {
      "atomspec": "#391.1/4:59",
      "category_key": "snRNA_snRNA_regions",
      "category_model_id": "391.2.2",
      "category_name": "snRNA-snRNA interacting regions",
      "color": "#E0CF1A",
      "default_visible": false,
      "feature": "U4_U6_stem_II_partner",
      "index": 5,
      "label_model_id": "391.2.2.2",
      "model_name": "label_05_U4_U6_stem_II_res_56_62",
      "selector_name": "B_8Q7N_U4_U6_stem_II_partner",
      "text": "U4/U6 stem II (res. 56-62)"
    },
    {
      "atomspec": "#391.1/4:74",
      "category_key": "other_snRNA_regions",
      "category_model_id": "391.2.3",
      "category_name": "other snRNA regions",
      "color": "#F0DF2E",
      "default_visible": false,
      "feature": "U4_Brr2_loading_region",
      "index": 6,
      "label_model_id": "391.2.3.1",
      "model_name": "label_06_U4_Brr2_region_res_60_62_68_81",
      "selector_name": "B_8Q7N_U4_Brr2_loading_region",
      "text": "U4 Brr2 region (res. 60-62;68-81)"
    },
    {
      "atomspec": "#391.1/5:40",
      "category_key": "snRNA_pre_mRNA_regions",
      "category_model_id": "391.2.4",
      "category_name": "snRNA-pre-mRNA regions",
      "color": "#1B3CD0",
      "default_visible": true,
      "feature": "U5_loop_I",
      "index": 7,
      "label_model_id": "391.2.4.1",
      "model_name": "label_07_U5_loop_I_res_38_42",
      "selector_name": "B_8Q7N_U5_loop_I",
      "text": "U5 loop I (res. 38-42)"
    },
    {
      "atomspec": "#391.1/6:16",
      "category_key": "internal_stem_loops",
      "category_model_id": "391.2.5",
      "category_name": "internal stem loops",
      "color": "#DC143C",
      "default_visible": false,
      "feature": "U6_5prime_terminal_stem_loop",
      "index": 8,
      "label_model_id": "391.2.5.1",
      "model_name": "label_08_U6_5_terminal_SL_res_1_30",
      "selector_name": "B_8Q7N_U6_5_terminal_stem_loop",
      "text": "U6 5' terminal SL (res. 1-30)"
    },
    {
      "atomspec": "#391.1/6:48",
      "category_key": "snRNA_snRNA_regions",
      "category_model_id": "391.2.2",
      "category_name": "snRNA-snRNA interacting regions",
      "color": "#D0183C",
      "default_visible": false,
      "feature": "U6_U2_helix_I_partner",
      "index": 9,
      "label_model_id": "391.2.2.3",
      "model_name": "label_09_U2_U6_helix_I_res_35_60",
      "selector_name": "B_8Q7N_U6_U2_helix_I_partner",
      "text": "U2/U6 helix I (res. 35-60)"
    },
    {
      "atomspec": "#391.1/6:44",
      "category_key": "snRNA_pre_mRNA_regions",
      "category_model_id": "391.2.4",
      "category_name": "snRNA-pre-mRNA regions",
      "color": "#E01842",
      "default_visible": true,
      "feature": "U6_5SS_upstream_contact",
      "index": 10,
      "label_model_id": "391.2.4.2",
      "model_name": "label_10_U6_5_SS_contact_res_38_49",
      "selector_name": "B_8Q7N_U6_5SS_upstream_contact",
      "text": "U6 5'SS contact (res. 38-49)"
    },
    {
      "atomspec": "#391.1/6:44",
      "category_key": "other_snRNA_regions",
      "category_model_id": "391.2.3",
      "category_name": "other snRNA regions",
      "color": "#DC143C",
      "default_visible": false,
      "feature": "U6_ACAGAGA_box",
      "index": 11,
      "label_model_id": "391.2.3.2",
      "model_name": "label_11_U6_ACAGAGA_res_41_47",
      "selector_name": "B_8Q7N_U6_ACAGAGA_box",
      "text": "U6 ACAGAGA (res. 41-47)"
    },
    {
      "atomspec": "#391.1/6:56",
      "category_key": "other_snRNA_regions",
      "category_model_id": "391.2.3",
      "category_name": "other snRNA regions",
      "color": "#E01842",
      "default_visible": false,
      "feature": "U6_U4_stem_II_partner",
      "index": 12,
      "label_model_id": "391.2.3.3",
      "model_name": "label_12_U4_U6_stem_II_res_52_61",
      "selector_name": "B_8Q7N_U6_U4_stem_II_partner",
      "text": "U4/U6 stem II (res. 52-61)"
    },
    {
      "atomspec": "#391.1/6:68",
      "category_key": "other_snRNA_regions",
      "category_model_id": "391.2.3",
      "category_name": "other snRNA regions",
      "color": "#D9183E",
      "default_visible": false,
      "feature": "U6_U4_stem_I_partner",
      "index": 13,
      "label_model_id": "391.2.3.4",
      "model_name": "label_13_U4_U6_stem_I_res_63_74",
      "selector_name": "B_8Q7N_U6_U4_stem_I_partner",
      "text": "U4/U6 stem I (res. 63-74)"
    }
  ],
  "outline_color": "#ffffff",
  "outline_offsets": [
    [
      -0.085,
      0,
      0
    ],
    [
      0.085,
      0,
      0
    ],
    [
      0,
      -0.085,
      0
    ],
    [
      0,
      0.085,
      0
    ],
    [
      -0.06,
      -0.06,
      0
    ],
    [
      -0.06,
      0.06,
      0
    ],
    [
      0.06,
      -0.06,
      0
    ],
    [
      0.06,
      0.06,
      0
    ],
    [
      -0.052,
      0,
      0
    ],
    [
      0.052,
      0,
      0
    ],
    [
      0,
      -0.052,
      0
    ],
    [
      0,
      0.052,
      0
    ],
    [
      -0.037,
      -0.037,
      0
    ],
    [
      -0.037,
      0.037,
      0
    ],
    [
      0.037,
      -0.037,
      0
    ],
    [
      0.037,
      0.037,
      0
    ]
  ],
  "size": 144,
  "structure_model_id": "391.1"
}

import os as _os
import tempfile as _tempfile
_fd, _spec_path = _tempfile.mkstemp(prefix='spliceosome_rna_labels_', suffix='.json')
try:
    with _os.fdopen(_fd, 'w', encoding='utf-8') as _handle:
        json.dump(_EMBEDDED_SPEC, _handle)
    create_label_models(session, _spec_path)
finally:
    try:
        _os.remove(_spec_path)
    except OSError:
        pass
