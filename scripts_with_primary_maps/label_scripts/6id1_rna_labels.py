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
    "339.1.90"
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
  "label_group_model_id": "339.2",
  "label_group_name": "RNA_feature_labels",
  "labels": [
    {
      "atomspec": "#339.1/G:4",
      "category_key": "pre_mRNA_features",
      "category_name": "pre-mRNA features",
      "color": "#303030",
      "index": 1,
      "model_name": "label_01_5_SS_res_1_6",
      "text": "? 5'SS (res. 1-6)"
    },
    {
      "atomspec": "#339.1/G:136",
      "category_key": "pre_mRNA_features",
      "category_name": "pre-mRNA features",
      "color": "#303030",
      "index": 2,
      "model_name": "label_02_intron_res_1_30_118_155",
      "text": "intron (res. 1-30;118-155)"
    },
    {
      "atomspec": "#339.1/G:142",
      "category_key": "pre_mRNA_features",
      "category_name": "pre-mRNA features",
      "color": "#303030",
      "index": 3,
      "model_name": "label_03_BP_region_res_139_145",
      "text": "BP region (res. 139-145)"
    },
    {
      "atomspec": "#339.1/G:144",
      "category_key": "pre_mRNA_features",
      "category_name": "pre-mRNA features",
      "color": "#303030",
      "index": 4,
      "model_name": "label_04_BP_A_res_144",
      "text": "BP-A (res. 144)"
    },
    {
      "atomspec": "#339.1/G:152",
      "category_key": "pre_mRNA_features",
      "category_name": "pre-mRNA features",
      "color": "#303030",
      "index": 5,
      "model_name": "label_05_PPT_res_150_155",
      "text": "PPT (res. 150-155)"
    },
    {
      "atomspec": "#339.1/H:28",
      "category_key": "snRNA_snRNA_regions",
      "category_name": "snRNA-snRNA interacting regions",
      "color": "#047857",
      "index": 6,
      "model_name": "label_06_U2_U6_helix_I_res_26_30",
      "text": "U2/U6 helix I (res. 26-30)"
    },
    {
      "atomspec": "#339.1/H:36",
      "category_key": "snRNA_pre_mRNA_regions",
      "category_name": "snRNA-pre-mRNA regions",
      "color": "#0B6E2D",
      "index": 7,
      "model_name": "label_07_U2_BP_pairing_res_32_41",
      "text": "U2 BP pairing (res. 32-41)"
    },
    {
      "atomspec": "#339.1/H:71",
      "category_key": "internal_stem_loops",
      "category_name": "internal stem loops",
      "color": "#167A38",
      "index": 8,
      "model_name": "label_08_U2_stem_IIa_res_46_47_54_60_67_75_77_80",
      "text": "U2 stem IIa (res. 46-47;54-60;67-75;77-80)"
    },
    {
      "atomspec": "#339.1/B:40",
      "category_key": "snRNA_pre_mRNA_regions",
      "category_name": "snRNA-pre-mRNA regions",
      "color": "#1B3CD0",
      "index": 9,
      "model_name": "label_09_U5_loop_I_res_38_42",
      "text": "U5 loop I (res. 38-42)"
    },
    {
      "atomspec": "#339.1/F:16",
      "category_key": "internal_stem_loops",
      "category_name": "internal stem loops",
      "color": "#DC143C",
      "index": 10,
      "model_name": "label_10_U6_5_terminal_SL_res_1_30",
      "text": "U6 5' terminal SL (res. 1-30)"
    },
    {
      "atomspec": "#339.1/F:48",
      "category_key": "snRNA_snRNA_regions",
      "category_name": "snRNA-snRNA interacting regions",
      "color": "#D0183C",
      "index": 11,
      "model_name": "label_11_U2_U6_helix_I_res_35_60",
      "text": "U2/U6 helix I (res. 35-60)"
    },
    {
      "atomspec": "#339.1/F:44",
      "category_key": "snRNA_pre_mRNA_regions",
      "category_name": "snRNA-pre-mRNA regions",
      "color": "#E01842",
      "index": 12,
      "model_name": "label_12_U6_5_SS_contact_res_38_49",
      "text": "U6 5'SS contact (res. 38-49)"
    },
    {
      "atomspec": "#339.1/F:44",
      "category_key": "other_snRNA_regions",
      "category_name": "other snRNA regions",
      "color": "#DC143C",
      "index": 13,
      "model_name": "label_13_U6_ACAGAGA_res_41_47",
      "text": "U6 ACAGAGA (res. 41-47)"
    },
    {
      "atomspec": "#339.1/F:88",
      "category_key": "internal_stem_loops",
      "category_name": "internal stem loops",
      "color": "#D61A3D",
      "index": 14,
      "model_name": "label_14_U6_ISL_res_79_97",
      "text": "U6 ISL (res. 79-97)"
    },
    {
      "atomspec": "#339.1/F:93",
      "category_key": "catalytic_core_regions",
      "category_name": "catalytic core regions",
      "color": "#C91236",
      "index": 15,
      "model_name": "label_15_U6_AGC_triad_res_92_94",
      "text": "U6 AGC triad (res. 92-94)"
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
  "structure_model_id": "339.1"
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
