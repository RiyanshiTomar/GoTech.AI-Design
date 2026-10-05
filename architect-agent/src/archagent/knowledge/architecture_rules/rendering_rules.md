# Rendering rules

* Renderers (SVG, GLB, IFC) are deterministic and never reason. They run ONLY after validation passes.
* The agent never writes SVG, IFC or GLB by hand. It only edits `design.py`.
* Semantics are preserved: SVG group ids `room-<id>`, `wall-<id>`, `door-<id>`, `window-<id>`, `stair-<id>`; IFC has Project/Site/Building/Storey/Space/Wall/Door/Window/Slab/Stair; GLB has one node per floor named `floor-<id>`.
* If an exporter fails, the design is reported as not delivered (EXPORT FAILED) and the last good artifacts are marked stale.
