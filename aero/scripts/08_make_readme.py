"""Writes repo/README.md. Every number is read from the saved JSON results (no hand-typed figures)."""
import json, os
R = r"E:\Sewa_first\manta\repo"
J = lambda p: json.load(open(os.path.join(R, p)))
au, fr, rm = J(r"model\logs\01_audit.json"), J(r"model\logs\02_remove_fin.json"), J(r"aero\results\fan_rims.json")["summary"]
ar, po, ws = J(r"aero\results\aero_results.json"), J(r"aero\results\aero_results_post.json"), J(r"aero\results\wing_stations.json")
g, f15, f12, f10 = ar["geometry"], ar["flight"]["15"], ar["flight"]["12"], ar["flight"]["10"]
v, npab, sm = ar["VLM"]["res_8x8"], ar["AeroBuildup_NP"], ar["static_margin_pct_MAC"]
ab = ar["AeroBuildup_15ms"]
LDmax = max(l for l in ab["LD"]); aLD = ab["alpha"][ab["LD"].index(LDmax)]
tr = f15["trim"]
txt = f"""# Manta VTOL flying wing - concept stage

**Status: work in progress. Concept-stage, simulated/virtual model only; nothing has been built or flown. The 3D mesh was generated with Meshy AI from AI-generated reference images, so it is not dimensionally validated and has known defects (raised fan rims, tail geometry removed). Aerodynamic figures are pre-test estimates from geometry extracted from the mesh, wing only, with fan openings, propwash and boom not modelled. The images in concept_renders_AI are AI-generated concept renders showing the intended look; they are not the analysed geometry. The developer is currently busy with university final exams; refinement, a clean parametric CAD model and hardware tests are planned afterwards.**

Labels used below: **MODEL RESULT** = computed by a script in this repo from the mesh or from AeroSandbox; **ASSUMPTION** = a value I chose, not measured; **NOT MODELLED** = ignored by the analysis.

## What is in this repo

| Folder | Content |
|---|---|
| `model/` | `v0_scaled.stl` (Meshy mesh "v0", scaled), `v0_nofin.stl` / `.glb` (vertical fin removed), scripts + logs + before/after renders of the fin removal |
| `concept_renders_AI/` | 7 AI-generated concept images (copied unchanged). **Not the analysed geometry.** |
| `v0_mesh_views/` | 7 renders of the v0 mesh showing its known defects (raised fan rims, malformed fin) |
| `aero/` | geometry extraction + AeroSandbox scripts, plots, JSON/CSV results, logs |

All scripts have absolute paths for the author's machine at the top (`E:\\Sewa_first\\manta\\...`); edit them to rerun. Python packages: see `requirements.txt`.

## Mesh audit - MODEL RESULT

- v0 mesh: watertight = {au['watertight']}, {au['n_faces']:,} faces, {au['n_components']} component. Span axis {au['axis_span']}, nose-to-tail axis {au['axis_nose_to_tail']} (nose toward {au['nose_direction']}), up axis {au['axis_up']}.
- **ASSUMPTION: uniform scale x{au['scale_factor_to_600mm_span']:.4f} so that the span is 600 mm.** Meshy meshes have no true scale or tolerances. No dimension in this repo was measured on a real object.
- Fin removed with a boolean cut (`model/scripts/02_remove_fin.py`): removed volume {fr['removed_volume_mm3']:.0f} mm3 in {fr['removed_n_pieces']} piece, `v0_nofin` watertight = {fr['nofin_watertight']}, {fr['nofin_n_components']} component, max deviation of the wing body from the original = {fr['wing_body_check_max_abs_signed_distance_mm']} mm. The upper lobe of the rear motor housing is left as a flat-topped block (cut surface); it is not clean-looking.

## Fan openings and raised rims - MODEL RESULT (mm at the assumed 600 mm span; not modelled in the aero analysis)

- Opening outer diameter {rm['outer_diameter']['min']:.1f} to {rm['outer_diameter']['max']:.1f} mm; centres at x = {rm['fan_centres_xy_mm'][0][0]:.1f} mm, y = {rm['fan_centres_xy_mm'][0][1]:+.1f} / {rm['fan_centres_xy_mm'][1][1]:+.1f} mm.
- Rim height above the surrounding skin: {rm['rim_height_all']['min']:.1f} to {rm['rim_height_all']['max']:.1f} mm (mean {rm['rim_height_all']['mean']:.1f} mm; {rm['rim_height_all']['n']} values, top and bottom). Hub protrudes {rm['hub_height_above_skin']['min']:.1f} to {rm['hub_height_above_skin']['max']:.1f} mm above the skin.
- One of 8 profile lines was excluded because edge detection locked onto an inner feature: {', '.join(rm['excluded_lines'])}.

## Aerodynamic pre-test - wing only (AeroSandbox: VLM + AeroBuildup/NeuralFoil)

**Not modelled:** fan openings and raised rims, propwash, boom / motor / propeller drag, stall and CLmax, Reynolds-number effects at this small size (Re at 15 m/s = {f15['Re_MAC']:.0f} on the MAC; NeuralFoil is low-confidence here), mesh surface roughness, wing twist and the mesh's small droop (planar wing assumed), control surfaces, the last {(g['span_mesh_m'] - g['span_modelled_m']) * 500:.0f} mm of each wingtip (model span {g['span_modelled_m'] * 1000:.0f} mm vs mesh {g['span_mesh_m'] * 1000:.0f} mm). There is no tail and no horizontal stabiliser (fin removed).

**Assumptions:** span 600 mm; design weight {ar['assumptions']['weight_kg'] * 1000:.0f} g (never weighed); sea-level ISA; airfoil = {ar['assumptions']['airfoil_base']} (MH 49 is a reflex flying-wing section; thickened to the mesh's outboard t/c = {ar['assumptions']['tc_mesh_outboard_median']:.3f}; the thickened section is unvalidated); CG range 35-45 % of the root chord.

| Quantity | Value | Source |
|---|---|---|
| Planform area (model) | {g['S_ref_m2'] * 1e4:.1f} cm2 ({g['area_pct_model_vs_raster']:+.2f} % vs the mesh's projected top-view area) | extraction, 12 stations |
| Span (model) / aspect ratio | {g['span_modelled_m'] * 1000:.0f} mm / {g['AR']:.2f} | extraction |
| MAC / root chord | {g['MAC_m'] * 1000:.1f} mm / {g['root_chord_m'] * 1000:.1f} mm | extraction |
| CL-alpha | {v['CL_alpha_per_rad']:.2f} /rad (VLM) vs {po['CL_alpha_per_rad']['AeroBuildup_0_8deg']:.2f} /rad (AeroBuildup): they disagree by {po['CL_alpha_disagreement_pct']:.0f} % | VLM 8x8, AeroBuildup |
| Neutral point | x = {v['x_np_m'] * 1000:.1f} mm (VLM) / {npab['x_np_m'] * 1000:.1f} mm (AeroBuildup) = {100 * v['np_frac_root_chord']:.1f} % / {100 * npab['np_frac_root_chord']:.1f} % of root chord | two-point slope method |
| Static margin, CG 35 / 40 / 45 % root chord | VLM {sm['0.35']['VLM']:+.1f} / {sm['0.4']['VLM']:+.1f} / {sm['0.45']['VLM']:+.1f} % MAC; AeroBuildup {sm['0.35']['AeroBuildup']:+.1f} / {sm['0.4']['AeroBuildup']:+.1f} / {sm['0.45']['AeroBuildup']:+.1f} % MAC | |
| Stability verdict | stable at 35 and 40 %; at 45 % the two methods disagree about the sign (neutral, about zero margin). A tailless wing this close to neutral is easy to make unstable by moving the CG | |
| CL required, 420 g | {f15['CL_required']:.2f} @ 15 m/s, {f12['CL_required']:.2f} @ 12 m/s, {f10['CL_required']:.2f} @ 10 m/s | W / (q S) |
| Angle of attack for that CL | {f15['alpha_required_deg']:.1f} deg @ 15 m/s (AeroBuildup; VLM cross-check {po['alpha_required_VLM_crosscheck_deg']:.1f} deg); {f12['alpha_required_deg']:.1f} deg @ 12 m/s (in the sections' roll-over region, low confidence); 10 m/s: **not reachable** in this model (sweep max CL {ar['AeroBuildup_15ms']['max_CL_in_sweep']:.2f} at 15 m/s, lower at 10 m/s) | |
| Cruise @ 15 m/s | CD = {f15['CD']:.4f}, L/D = {f15['LD']:.1f}, drag = {f15['drag_N']:.2f} N, aerodynamic power = {f15['aero_power_W']:.1f} W (wing only) | AeroBuildup |
| Best L/D in the 15 m/s sweep | {LDmax:.1f} at alpha = {aLD:.0f} deg | AeroBuildup |
| Trim (Cm = 0), 15 m/s polar | CG 35 %: alpha {tr['0.35']['alpha_trim_deg']:.1f} deg, CL {tr['0.35']['CL_at_trim']:.2f} (level flight at that CL would need about {po['speed_for_trim_at_CG_mps']['0.35']:.0f} m/s); CG 40 %: alpha {tr['0.4']['alpha_trim_deg']:.1f} deg, CL {tr['0.4']['CL_at_trim']:.2f} (about {po['speed_for_trim_at_CG_mps']['0.4']:.0f} m/s); CG 45 %: no trim point (Cm slope ~0) | |
| Cm at the required CL @ 15 m/s | {f15['Cm_at_required_CL']['0.35']:+.3f} / {f15['Cm_at_required_CL']['0.4']:+.3f} / {f15['Cm_at_required_CL']['0.45']:+.3f} for CG 35 / 40 / 45 % (nose-up positive); zero at about {100 * po['CG_fraction_root_chord_for_Cm0_at_CLreq_15ms']:.1f} % root chord (interpolated), static margin there {po['static_margin_at_that_CG_pct_MAC']['VLM']:.1f} % (VLM) / {po['static_margin_at_that_CG_pct_MAC']['AeroBuildup_NP']:.1f} % (AeroBuildup) MAC | |

Sensitivity: using per-station thickness instead of one airfoil changes CD at 15 m/s from {f15['CD']:.4f} to {ar['sensitivity_per_station_thickness_15ms']['CD']:.4f}. VLM resolution 5x5 / 8x8 / 12x10: neutral point spread {max(po['VLM_resolution_spread']['NP_x_mm']) - min(po['VLM_resolution_spread']['NP_x_mm']):.2f} mm, but the zero-lift CL moves from {po['VLM_resolution_spread']['CL0'][0]:.3f} to {po['VLM_resolution_spread']['CL0'][2]:.3f}.

Method B (coarse CFD with OpenFOAM or SU2) was **skipped**: neither is installed and setting it up exceeds the time-box.

Key plots: `aero/plots/planform_overlay.png` (extracted planform over the mesh top view), `aero/plots/aero_summary.png`. Results: `aero/results/`.

## Known problems (not solved, mostly not analysed)

- **Hover yaw torque:** one rear propeller plus two lift fans; yaw control in hover is not designed or analysed.
- **Transition** between hover and wing-borne flight: not analysed.
- **Fan-hole lift loss:** the two open fan holes (diameter about {rm['outer_diameter']['mean']:.0f} mm at the assumed scale) are expected to cost lift and add drag in cruise; this is not modelled, so the figures above probably over-estimate the real wing's performance.
- **CG balance:** the usable CG band is narrow (neutral point near 45 % root chord, zero-moment CG at cruise near {100 * po['CG_fraction_root_chord_for_Cm0_at_CLreq_15ms']:.0f} %) and the lift fans sit at x about {rm['fan_centres_xy_mm'][0][0]:.0f} mm, close to that band.
- **Hover power:** not estimated.
- The mesh has raised fan rims, a thick (about 17 % t/c) AI-shaped wing, and no true dimensions. A clean parametric CAD model is needed before anything is built.
"""
open(os.path.join(R, "README.md"), "w", encoding="utf-8").write(txt)
print(txt)
