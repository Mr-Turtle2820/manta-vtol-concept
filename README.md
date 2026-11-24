# Manta VTOL flying wing - concept stage

**Status: work in progress. Concept-stage, simulated/virtual model only; nothing has been built or flown. The 3D mesh was generated with Meshy AI from AI-generated reference images, so it is not dimensionally validated and has known defects (raised fan rims, tail geometry removed). Aerodynamic figures are pre-test estimates from geometry extracted from the mesh, wing only, with fan openings, propwash and boom not modelled. The images in concept_renders_AI are AI-generated concept renders showing the intended look; they are not the analysed geometry. The developer is currently busy with university final exams; refinement, a clean parametric CAD model and hardware tests are planned afterwards.**

Labels used below: **MODEL RESULT** = computed by a script in this repo from the mesh or from AeroSandbox; **ASSUMPTION** = a value I chose, not measured; **NOT MODELLED** = ignored by the analysis.

## What is in this repo

| Folder | Content |
|---|---|
| `model/` | `v0_scaled.stl` (Meshy mesh "v0", scaled), `v0_nofin.stl` / `.glb` (vertical fin removed), scripts + logs + before/after renders of the fin removal |
| `concept_renders_AI/` | 7 AI-generated concept images (copied unchanged). **Not the analysed geometry.** |
| `v0_mesh_views/` | 7 renders of the v0 mesh showing its known defects (raised fan rims, malformed fin) |
| `aero/` | geometry extraction + AeroSandbox scripts, plots, JSON/CSV results, logs |

All scripts have absolute paths for the author's machine at the top (`E:\Sewa_first\manta\...`); edit them to rerun. Python packages: see `requirements.txt`.

## Mesh audit - MODEL RESULT

- v0 mesh: watertight = True, 65,620 faces, 1 component. Span axis Y, nose-to-tail axis X (nose toward -X), up axis Z.
- **ASSUMPTION: uniform scale x1.7008 so that the span is 600 mm.** Meshy meshes have no true scale or tolerances. No dimension in this repo was measured on a real object.
- Fin removed with a boolean cut (`model/scripts/02_remove_fin.py`): removed volume 5450 mm3 in 1 piece, `v0_nofin` watertight = True, 1 component, max deviation of the wing body from the original = 0.0 mm. The upper lobe of the rear motor housing is left as a flat-topped block (cut surface); it is not clean-looking.

## Fan openings and raised rims - MODEL RESULT (mm at the assumed 600 mm span; not modelled in the aero analysis)

- Opening outer diameter 54.5 to 54.8 mm; centres at x = -58.4 mm, y = +82.2 / -82.0 mm.
- Rim height above the surrounding skin: 3.7 to 5.9 mm (mean 4.6 mm; 14 values, top and bottom). Hub protrudes 5.1 to 8.6 mm above the skin.
- One of 8 profile lines was excluded because edge detection locked onto an inner feature: fan_y+1/bottom/spanwise_line.

## Aerodynamic pre-test - wing only (AeroSandbox: VLM + AeroBuildup/NeuralFoil)

**Not modelled:** fan openings and raised rims, propwash, boom / motor / propeller drag, stall and CLmax, Reynolds-number effects at this small size (Re at 15 m/s = 128195 on the MAC; NeuralFoil is low-confidence here), mesh surface roughness, wing twist and the mesh's small droop (planar wing assumed), control surfaces, the last 8 mm of each wingtip (model span 584 mm vs mesh 601 mm). There is no tail and no horizontal stabiliser (fin removed).

**Assumptions:** span 600 mm; design weight 420 g (never weighed); sea-level ISA; airfoil = MH 49 (UIUC), base t/c 0.105, scaled x1.61 (MH 49 is a reflex flying-wing section; thickened to the mesh's outboard t/c = 0.169; the thickened section is unvalidated); CG range 35-45 % of the root chord.

| Quantity | Value | Source |
|---|---|---|
| Planform area (model) | 598.0 cm2 (-1.68 % vs the mesh's projected top-view area) | extraction, 12 stations |
| Span (model) / aspect ratio | 584 mm / 5.70 | extraction |
| MAC / root chord | 124.8 mm / 210.8 mm | extraction |
| CL-alpha | 4.03 /rad (VLM) vs 4.69 /rad (AeroBuildup): they disagree by 16 % | VLM 8x8, AeroBuildup |
| Neutral point | x = -60.2 mm (VLM) / -62.1 mm (AeroBuildup) = 45.9 % / 45.0 % of root chord | two-point slope method |
| Static margin, CG 35 / 40 / 45 % root chord | VLM +18.4 / +9.9 / +1.5 % MAC; AeroBuildup +16.8 / +8.4 / -0.1 % MAC | |
| Stability verdict | stable at 35 and 40 %; at 45 % the two methods disagree about the sign (neutral, about zero margin). A tailless wing this close to neutral is easy to make unstable by moving the CG | |
| CL required, 420 g | 0.50 @ 15 m/s, 0.78 @ 12 m/s, 1.12 @ 10 m/s | W / (q S) |
| Angle of attack for that CL | 7.5 deg @ 15 m/s (AeroBuildup; VLM cross-check 8.3 deg); 13.9 deg @ 12 m/s (in the sections' roll-over region, low confidence); 10 m/s: **not reachable** in this model (sweep max CL 0.92 at 15 m/s, lower at 10 m/s) | |
| Cruise @ 15 m/s | CD = 0.0484, L/D = 10.3, drag = 0.40 N, aerodynamic power = 6.0 W (wing only) | AeroBuildup |
| Best L/D in the 15 m/s sweep | 10.8 at alpha = 9 deg | AeroBuildup |
| Trim (Cm = 0), 15 m/s polar | CG 35 %: alpha 3.7 deg, CL 0.17 (level flight at that CL would need about 25 m/s); CG 40 %: alpha 5.6 deg, CL 0.35 (about 18 m/s); CG 45 %: no trim point (Cm slope ~0) | |
| Cm at the required CL @ 15 m/s | -0.053 / -0.011 / +0.032 for CG 35 / 40 / 45 % (nose-up positive); zero at about 41.2 % root chord (interpolated), static margin there 7.8 % (VLM) / 6.3 % (AeroBuildup) MAC | |

Sensitivity: using per-station thickness instead of one airfoil changes CD at 15 m/s from 0.0484 to 0.0491. VLM resolution 5x5 / 8x8 / 12x10: neutral point spread 0.10 mm, but the zero-lift CL moves from -0.063 to -0.096.

Method B (coarse CFD with OpenFOAM or SU2) was **skipped**: neither is installed and setting it up exceeds the time-box.

Key plots: `aero/plots/planform_overlay.png` (extracted planform over the mesh top view), `aero/plots/aero_summary.png`. Results: `aero/results/`.

## Known problems (not solved, mostly not analysed)

- **Hover yaw torque:** one rear propeller plus two lift fans; yaw control in hover is not designed or analysed.
- **Transition** between hover and wing-borne flight: not analysed.
- **Fan-hole lift loss:** the two open fan holes (diameter about 55 mm at the assumed scale) are expected to cost lift and add drag in cruise; this is not modelled, so the figures above probably over-estimate the real wing's performance.
- **CG balance:** the usable CG band is narrow (neutral point near 45 % root chord, zero-moment CG at cruise near 41 %) and the lift fans sit at x about -58 mm, close to that band.
- **Hover power:** not estimated.
- The mesh has raised fan rims, a thick (about 17 % t/c) AI-shaped wing, and no true dimensions. A clean parametric CAD model is needed before anything is built.
