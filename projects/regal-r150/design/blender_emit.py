"""
Warstwa Blendera - zamienia elementy z shelf_model na siatki w scenie.

Dziala dwojako:
  - jako modul obok shelf_model.py  (import ponizej)
  - sklejony z shelf_model.py w jeden plik przez make_blender_script.py
    (wtedy nazwy sa juz w przestrzeni globalnej i import sie nie wykonuje)
"""

try:                       # noqa: SIM105 - sprawdzamy czy jestesmy w wersji sklejonej
    build_parts           # type: ignore[used-before-def]  # noqa: B018
except NameError:
    from shelf_model import (  # noqa: F401
        PARAMS, DERIVED, build_parts, summary, skin_developed_length,
    )

MM = 0.001                 # model liczony w mm, scena Blendera w metrach

COLLECTIONS = {
    "vertical": "01_Piony",
    "shelf": "02_Polki",
    "tenon": "03_Czopy",
    "rib": "04_Zebra_nosa",
    "skin": "05_Poszycie_giete",
    "back": "06_Plecy",
}

COLORS = {
    "vertical": (0.86, 0.72, 0.50, 1.0),
    "shelf": (0.90, 0.78, 0.57, 1.0),
    "tenon": (0.72, 0.55, 0.33, 1.0),
    "rib": (0.80, 0.66, 0.45, 1.0),
    "skin": (0.93, 0.83, 0.65, 1.0),
    "back": (0.62, 0.50, 0.35, 1.0),
}


def _material(bpy, kind):
    name = "regal_%s" % kind
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = COLORS[kind]
            if "Roughness" in bsdf.inputs:
                bsdf.inputs["Roughness"].default_value = 0.65
        mat.diffuse_color = COLORS[kind]        # kolor w trybie Solid
    return mat


def _collection(bpy, root, name):
    col = bpy.data.collections.get(name)
    if col is None:
        col = bpy.data.collections.new(name)
        root.children.link(col)
    return col


def clear_previous(bpy, root_name):
    """Usuwa poprzednia wersje regalu - skrypt jest idempotentny."""
    root = bpy.data.collections.get(root_name)
    if root is None:
        return
    stack = [root]
    seen = []
    while stack:
        col = stack.pop()
        seen.append(col)
        stack.extend(col.children)
    for col in seen:
        for obj in list(col.objects):
            bpy.data.meshes.remove(obj.data, do_unlink=True)
    for col in seen:
        bpy.data.collections.remove(col)


def build_scene(root_name="Regal_R150", with_tenons=True):
    import bpy               # dostepny tylko wewnatrz Blendera
    import bmesh

    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.length_unit = "MILLIMETERS"

    clear_previous(bpy, root_name)

    root = bpy.data.collections.new(root_name)
    scene.collection.children.link(root)

    parts = build_parts()
    made = 0
    for part in parts:
        if part.kind == "tenon" and not with_tenons:
            continue
        verts, faces = part.mesh()

        mesh = bpy.data.meshes.new(part.name)
        mesh.from_pydata([(x * MM, y * MM, z * MM) for x, y, z in verts], [], faces)
        mesh.validate()
        mesh.update()

        # scalenie pokrywajacych sie wierzcholkow na luku + gladkie normalne krawedzi
        bm = bmesh.new()
        bm.from_mesh(mesh)
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.to_mesh(mesh)
        bm.free()

        obj = bpy.data.objects.new(part.name, mesh)
        obj.data.materials.append(_material(bpy, part.kind))
        obj["kind"] = part.kind
        obj["grain"] = part.grain
        obj["material_spec"] = part.material
        obj["thickness_mm"] = part.thickness
        _collection(bpy, root, COLLECTIONS[part.kind]).objects.link(obj)
        made += 1

    return made


def main():
    s = summary()
    n = build_scene()
    p, d = PARAMS, DERIVED
    print("=" * 58)
    print("Regal R150  %.0f x %.0f x %.0f mm" % (p["W"], p["H"], p["D"]))
    print("=" * 58)
    print("  zaoblenie      R%.0f, przedni lewy narozik, cala wysokosc" % p["R"])
    print("  przesla        %d x %.0f mm swiatla" % (p["N_BAYS"], d["bay_clear"]))
    print("  poziomy        %d, swiatlo miedzypolkowe %.1f mm"
          % (p["N_LEVELS"], d["shelf_clear"]))
    print("  zebra nosa     %d w rozstawie %.1f mm" % (p["N_RIBS"], d["rib_pitch"]))
    print("  obiektow       %d" % n)
    print("  srub M6        %d" % s["n_bolts"])
    print("  masa netto     %.1f kg" % s["mass_kg"])
    print("=" * 58)


if __name__ == "__main__":
    main()
