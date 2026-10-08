# Astra V3 — simple internal slider lock designer

This repository captures the **October 8, 2026 mesh preview** of the current Astra V3 designer. It is a self-contained browser snapshot of the aircraft context and the center locking mechanism. The preview shows one servo crank, one connecting rod, and one straight sliding bolt inside the battery pod. The bolt indexes the rotating center assembly at 0° and 90°.

## Open the designer

Clone the repository, then open `index.html` in a desktop browser. All required JavaScript and mesh data are in the clone, so an internet connection is not needed for the designer itself. If the browser restricts local files, serve the clone:

```powershell
git clone https://github.com/francoavalosm08/astro_cad.git
cd astro_cad
python -m http.server 8922
```

Then open `http://localhost:8922/index.html`. Stop the server with Ctrl+C. The **Accepted aircraft** link in the page header points to an older local preview server on port 8918; it is optional and will only work when that separate server is running. Use the **Whole aircraft** checkbox to see the aircraft included in this snapshot.

## Use the controls

1. Leave **Pod / battery** and **Cutaway egg** enabled to inspect the internal lock. Turn on **Whole aircraft** for the wider assembly.
2. Click **Retract bolt** before moving the frame. The bolt withdraws 17 mm.
3. Use the frame-angle slider, or the **0°** and **90°** buttons, to rotate the released assembly.
4. Click **Engage bolt** at exactly 0° or 90°. The interface disables engagement at intermediate angles.
5. Use **3D**, **Top**, **Side**, **Front**, **Fit**, +/−, and pointer drag to inspect the geometry. **Cutaway fork** hides the nearer fork cheek. **Magnet assist** displays an optional, untested retaining magnet reference.

Open `report.html` for dimensions and the meaning of the checks. `checks.json` records the sampled mesh and interface checks; `mechanism.json` and `kinematics.json` record the geometric and motion parameters. The PNG files are reference screenshots.

## Verification status

This is **preview geometry**, not manufacturing CAD. The rotating module was checked against the fixed mechanism every **0.5° from 0° to 90°**. The crank, rod, and slider were checked at **61 release positions**; circular meshes use **96 segments**. The recorded checks found no unintended intersections in those sampled pairs, but mesh approximation and unsampled positions leave clearance uncertainty. These checks do not establish continuous collision freedom, joint strength, bearing fit, servo torque, or loss-of-power retention. The full 35 mm bearing/socket conversion remains unfinished. No STEP/STL manufacturing files were created for this revision.

## Files and provenance

- `index.html`, `viewer.js`, `software_view.js`: browser UI, motion, and software 3D rendering.
- `model.js`: local lock/fork mesh parts.
- `context.js`, `pod-outer.js`: cached aircraft, battery, and pod mesh context. These larger files are required by the offline viewer.
- `report.html`, `checks.json`, `mechanism.json`, `kinematics.json`: design record and preview checks.
- `tools/build_simple_internal_lock_20261008.py`, `tools/publish_simple_internal_lock_20261008.py`: original generator scripts, kept for provenance. They reference absolute paths to the earlier `20261008_internal_center_lock_mesh_preview` and need NumPy, trimesh, SciPy, and the manifold boolean engine. The committed browser preview runs without them.

The recorded source hashes are in `checks.json`. This repository is a snapshot of the designer state; keep later design revisions in separate commits so this state remains recoverable.
