"""A small Vestack module as ObjectSnapshot values, shaped like the spike model.

Module M1, 6000 x 2500 mm: a two-panel bottom floor (subgroup M1-F1, group
"Plancher bas"), wall M1-W1 along -y with its MOB200 body and studs, wall M1-W2
along +x with a MOB145 body, a cold-roof part M1-TF0, a posts part M1-Poteaux,
a joinery item in W1 that has no subgroup (as most MEX elements do), and a
drilling in group "Usinage". Everything can be rotated and shifted in plan.
"""
import math
from typing import List, Sequence, Tuple

from vestack.object_inventory import ObjectSnapshot

Point3 = Tuple[float, float, float]


def box(x0: float, y0: float, z0: float, x1: float, y1: float, z1: float) -> List[Point3]:
    return [(x, y, z) for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)]


def place(points: Sequence[Point3], degrees: float, shift: Point3) -> Tuple[Point3, ...]:
    a = math.radians(degrees)
    c, s = math.cos(a), math.sin(a)
    return tuple((x * c - y * s + shift[0], x * s + y * c + shift[1], z + shift[2])
                 for x, y, z in points)


def element(element_id: int, vertices: List[Point3], *, name: str = "", group: str = "",
            subgroup: str = "", module: str = "", complex_code: str = "",
            material: str = "", degrees: float = 0.0,
            shift: Point3 = (0.0, 0.0, 0.0)) -> ObjectSnapshot:
    return ObjectSnapshot(element_id=element_id, name=name, group=group, subgroup=subgroup,
                          module_attribute=module, complex_code=complex_code,
                          material=material, vertices=place(vertices, degrees, shift))


def module_m1(degrees: float = 0.0, shift: Point3 = (0.0, 0.0, 0.0)) -> List[ObjectSnapshot]:
    def e(element_id: int, vertices: List[Point3], **kw: str) -> ObjectSnapshot:
        return element(element_id, vertices, degrees=degrees, shift=shift, module="M1", **kw)

    return [
        e(1, box(0, 0, 0, 3000, 2500, 220), name="OSB 9mm", group="Plancher bas",
          subgroup="M1-F1", complex_code="PB-AUX-01", material="OSB-9"),
        e(2, box(3000, 0, 0, 6000, 2500, 220), name="OSB 9mm", group="Plancher bas",
          subgroup="M1-F1", complex_code="PB-AUX-01", material="OSB-9"),
        e(10, box(0, 0, 220, 6000, 212, 2865), name="MOB200", group="MOB", subgroup="M1-W1"),
        e(11, box(0, 6, 220, 45, 206, 2865), name="montant", group="MOB", subgroup="M1-W1",
          material="C24"),
        e(12, box(955, 6, 220, 1000, 206, 2865), name="montant", group="MOB", subgroup="M1-W1",
          material="C24"),
        e(20, box(5855, 212, 220, 6000, 2288, 2865), name="MOB145", group="MOB",
          subgroup="M1-W2"),
        e(30, box(0, 0, 2865, 6000, 2500, 3400), name="fermette", group="Toiture froide",
          subgroup="M1-TF0"),
        e(40, box(2900, 1150, 220, 3100, 1350, 2865), name="poteau", group="MOB",
          subgroup="M1-Poteaux"),
        element(50, box(1000, 0, 310, 2455, 212, 2625), name="MEX type B", group="MEX",
                degrees=degrees, shift=shift),
        e(60, box(100, 0, 0, 110, 10, 10), name="perçage Ø4", group="Usinage",
          subgroup="Usinage PB - Perçages rive"),
    ]
