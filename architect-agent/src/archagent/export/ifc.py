"""IFC4 export with IfcOpenShell. Consumes the same Analysis as the validators/renderers."""
from __future__ import annotations

from typing import Dict, List, Tuple

import ifcopenshell
import ifcopenshell.api.aggregate
import ifcopenshell.api.context
import ifcopenshell.api.feature
import ifcopenshell.api.geometry
import ifcopenshell.api.pset
import ifcopenshell.api.root
import ifcopenshell.api.spatial
import ifcopenshell.api.unit
import ifcopenshell.guid
from ifcopenshell import api
import numpy as np

from ..geometry import analyze
from ..geometry.slabs import slab_cells

SLAB_T = 0.2


def _m(name):
    return np.eye(4)


def _place(f, el, x, y, z):
    mat = np.eye(4)
    mat[:3, 3] = (x, y, z)
    api.geometry.edit_object_placement(f, product=el, matrix=mat)


def _box_rep(f, body, x0, y0, z0, x1, y1, z1):
    """Add an extruded rectangle representation positioned by its min corner (caller places product at corner)."""
    profile = f.createIfcRectangleProfileDef("AREA", None, f.createIfcAxis2Placement2D(
        f.createIfcCartesianPoint(((x1 - x0) / 2, (y1 - y0) / 2)), None), x1 - x0, y1 - y0)
    return api.geometry.add_profile_representation(f, context=body, profile=profile, depth=z1 - z0)


def _add_box(f, body, el, x0, y0, z0, x1, y1, z1):
    rep = _box_rep(f, body, x0, y0, z0, x1, y1, z1)
    api.geometry.assign_representation(f, product=el, representation=rep)
    _place(f, el, x0, y0, z0)


def _poly_rep(f, body, polygon, depth):
    pts = [f.createIfcCartesianPoint(tuple(p)) for p in list(polygon.exterior.coords)]
    outer = f.createIfcPolyline(pts)
    inner = []
    for ring in polygon.interiors:
        inner.append(f.createIfcPolyline([f.createIfcCartesianPoint(tuple(p)) for p in ring.coords]))
    if inner:
        prof = f.createIfcArbitraryProfileDefWithVoids("AREA", None, outer, inner)
    else:
        prof = f.createIfcArbitraryClosedProfileDef("AREA", None, outer)
    return api.geometry.add_profile_representation(f, context=body, profile=prof, depth=depth)


def export_ifc(model, path: str) -> str:
    an = analyze(model)
    b = an.building
    f = ifcopenshell.file(schema="IFC4")
    project = api.root.create_entity(f, ifc_class="IfcProject", name=b.name or "Project")
    api.unit.assign_unit(f, length={"is_metric": True, "raw": "METERS"})   # model is in metres; the default is millimetres
    ctx = api.context.add_context(f, context_type="Model")
    body = api.context.add_context(f, context_type="Model", context_identifier="Body",
                                   target_view="MODEL_VIEW", parent=ctx)
    site = api.root.create_entity(f, ifc_class="IfcSite", name="Site")
    building = api.root.create_entity(f, ifc_class="IfcBuilding", name=b.name or "Building")
    api.aggregate.assign_object(f, products=[site], relating_object=project)
    api.aggregate.assign_object(f, products=[building], relating_object=site)

    # site boundary as a thin slab-less polygon is overkill for the PoC; store size as properties
    pset = api.pset.add_pset(f, product=site, name="Pset_SiteCommon")
    api.pset.edit_pset(f, pset=pset, properties={"SiteWidth_m": float(b.width), "SiteDepth_m": float(b.depth)})

    for fg in an.floors:
        fl = fg.floor
        storey = api.root.create_entity(f, ifc_class="IfcBuildingStorey", name=fl.name)
        storey.Elevation = float(fl.elevation)
        api.aggregate.assign_object(f, products=[storey], relating_object=building)
        _place(f, storey, 0, 0, fl.elevation)
        contained = []

        # slab (polygon with stair holes), top face at storey level
        if fg.slab is not None and not fg.slab.is_empty:
            polys = fg.slab.geoms if fg.slab.geom_type == "MultiPolygon" else [fg.slab]
            for k, poly in enumerate(polys):
                slab = api.root.create_entity(f, ifc_class="IfcSlab", name=f"{fl.name} Slab {k + 1}")
                api.geometry.assign_representation(f, product=slab, representation=_poly_rep(f, body, poly, SLAB_T))
                _place(f, slab, 0, 0, -SLAB_T)
                contained.append(slab)

        # spaces
        for r in fg.rooms.values():
            if r.id not in fg.boxes:
                continue
            sp = api.root.create_entity(f, ifc_class="IfcSpace", name=r.name)
            sp.LongName = r.kind
            _add_box(f, body, sp, r.x, r.y, 0, r.x + r.width, r.y + r.depth, fl.height)
            api.aggregate.assign_object(f, products=[sp], relating_object=storey)
            ps = api.pset.add_pset(f, product=sp, name="Pset_SpaceCommon")
            api.pset.edit_pset(f, pset=ps, properties={"Reference": r.id, "NetFloorArea": float(r.width * r.depth)})

        # walls + openings
        wall_el = {}
        for w in fg.walls:
            el = api.root.create_entity(f, ifc_class="IfcWall", name=f"Wall {w.id}")
            _add_box(f, body, el, w.x0, w.y0, 0, w.x1, w.y1, fl.height)
            wall_el[w.id] = el
            contained.append(el)
            ps = api.pset.add_pset(f, product=el, name="Pset_WallCommon")
            api.pset.edit_pset(f, pset=ps, properties={"IsExternal": w.kind == "exterior", "Reference": w.id})
        for op in fg.openings:
            if op.problems or op.rect is None or op.wall_id not in wall_el:
                continue
            x0, y0, x1, y1 = op.rect
            void = api.root.create_entity(f, ifc_class="IfcOpeningElement", name=f"Opening {op.id}")
            _add_box(f, body, void, x0, y0, op.z0, x1, y1, op.z1)
            api.feature.add_feature(f, feature=void, element=wall_el[op.wall_id])
            fill = api.root.create_entity(f, ifc_class="IfcDoor" if op.kind == "door" else "IfcWindow", name=op.id)
            _add_box(f, body, fill, x0, y0, op.z0, x1, y1, op.z1)
            f.createIfcRelFillsElement(ifcopenshell.guid.new(), None, None, None, void, fill)
            contained.append(fill)

        # stairs: each step is a box; grouped under one IfcStair via aggregation of IfcStairFlight-less parts
        for st in fl.stairs:
            geo = fg.stairs.get(st.id)
            if not geo or not geo.boxes:
                continue
            stair = api.root.create_entity(f, ifc_class="IfcStair", name=f"Stair {st.id}")
            contained.append(stair)
            items = []
            for (x0, y0, z0, x1, y1, z1) in geo.boxes:
                prof = f.createIfcRectangleProfileDef("AREA", None, f.createIfcAxis2Placement2D(
                    f.createIfcCartesianPoint(((x1 - x0) / 2, (y1 - y0) / 2)), None), x1 - x0, y1 - y0)
                pos = f.createIfcAxis2Placement3D(f.createIfcCartesianPoint((x0, y0, 0.0)), None, None)
                solid = f.createIfcExtrudedAreaSolid(prof, pos, f.createIfcDirection((0.0, 0.0, 1.0)), z1)
                items.append(solid)
            rep = f.createIfcShapeRepresentation(body, "Body", "SweptSolid", items)
            api.geometry.assign_representation(f, product=stair, representation=rep)
            _place(f, stair, 0, 0, 0)

        if contained:
            api.spatial.assign_container(f, products=contained, relating_structure=storey)
    f.write(path)
    return path
