import json, os, numpy as np, aerosandbox as asb, warnings; warnings.filterwarnings("ignore")
WORK = r"E:\Sewa_first\manta\v0_work"
S = json.load(open(os.path.join(WORK, "aero", "wing_stations.json")))
af = asb.Airfoil("mh49")
st = [s for s in S["stations"] if s["y"] != 12.0]
xs = [asb.WingXSec(xyz_le=[s["x_le"] / 1000, s["y"] / 1000, 0], chord=s["chord"] / 1000, twist=0, airfoil=af) for s in st]
wing = asb.Wing(name="w", symmetric=True, xsecs=xs)
print("wing S_ref %.5f m2, b %.4f, c_ref %.4f, AR %.3f" % (wing.area(), wing.span(), wing.mean_aerodynamic_chord(), wing.aspect_ratio()))
for xref in (-0.080, -0.060):
    ap = asb.Airplane(name="a", xyz_ref=[xref, 0, 0], wings=[wing])
    for a in (0.0, 4.0):
        op = asb.OperatingPoint(atmosphere=asb.Atmosphere(altitude=0), velocity=15, alpha=a)
        v = asb.VortexLatticeMethod(airplane=ap, op_point=op, spanwise_resolution=6, chordwise_resolution=6).run()
        b = asb.AeroBuildup(airplane=ap, op_point=op).run()
        print("xref %.3f a %.0f | VLM CL %.4f CD %.4f Cm %.4f | AB CL %.4f CD %.4f Cm %.4f" % (xref, a, v["CL"], v["CD"], v["Cm"], b["CL"], b["CD"], b["Cm"]))
