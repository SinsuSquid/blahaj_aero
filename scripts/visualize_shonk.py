#!/usr/bin/env -S pvpython --force-offscreen-rendering
"""
=============================================================================
Blåhaj Aerodynamics - Ultra-Plushy ParaView Visualization Generator (4:3)
=============================================================================
Inspired by the legendary 'Aerodynamics of a Cow' CFD meme:
1. Uses the original, smooth, high-polygon 3D Blåhaj model (125k triangles)
   for an adorable, ultra-plushy appearance (preserving eyes, gills, mouth, fins).
2. Resamples real OpenFOAM CFD fields (pressure p and velocity U) directly onto
   the smooth plushy surface via ParaView's ResampleWithDataset filter.
3. Overlays aerodynamic surface vector arrows (glyphs) showing airflow direction.
4. Clean, family-friendly pure white background with NO wind tunnel floor.
5. Exports in crisp 4:3 aspect ratio (1440x1080) for a 2x2 comparison grid.

Usage:
    pvpython --force-offscreen-rendering scripts/visualize_shonk.py
    (or inside ParaView GUI: View -> Python Shell -> Run Script)

Outputs:
    - ParaView/shonk_plushy_pressure.png (Isometric Surface Pressure)
    - ParaView/shonk_plushy_velocity.png (Isometric Surface Velocity)
    - ParaView/shonk_plushy_side.png     (Side Profile View)
    - ParaView/shonk_plushy_top.png      (Top Planform View)
    - ParaView/shonk.png                 (Hero render for README)
    - ParaView/Shonk_UltraPlush.pvsm     (Real CFD ParaView state file)
=============================================================================
"""

import os
import sys
import paraview.simple as pvs

def main():
    case_path = os.path.abspath("blahaj.foam")
    stl_path = os.path.abspath("constant/triSurface/blahaj.stl")
    output_dir = os.path.abspath("ParaView")
    os.makedirs(output_dir, exist_ok=True)

    if not os.path.isfile(case_path):
        print(f"Error: {case_path} not found. Please run ./Allrun first.", file=sys.stderr)
        sys.exit(1)

    if not os.path.isfile(stl_path):
        print(f"Error: {stl_path} not found.", file=sys.stderr)
        sys.exit(1)

    print("==========================================================")
    print("   BLÅHAJ ULTRA-PLUSHY CFD VISUALIZATION GENERATOR (4:3)")
    print("==========================================================")

    # 1. Create Render View with pure white background (4:3 ratio: 1440x1080)
    view = pvs.CreateRenderView()
    view.ViewSize = [1440, 1080]
    view.Background = [1.0, 1.0, 1.0] # Pure white
    view.Background2 = [1.0, 1.0, 1.0]
    view.OrientationAxesVisibility = 0

    # 2. Load Real OpenFOAM Solution
    print(f"--> [1/6] Loading OpenFOAM CFD solution: {case_path}")
    flow = pvs.OpenFOAMReader(registrationName="OpenFOAM_Solution", FileName=case_path)
    flow.MeshRegions = ["internalMesh"]
    flow.CellArrays = ["U", "p", "k", "nut", "omega"]
    flow.UpdatePipeline()

    # 3. Load Original Smooth High-Resolution Blåhaj Surface Model
    print(f"--> [2/6] Loading smooth original 3D surface model: {stl_path}")
    shonk_stl = pvs.STLReader(registrationName="Blahaj_OriginalMesh", FileNames=[stl_path])
    shonk_stl.UpdatePipeline()

    # 4. Resample CFD Data onto the Smooth 3D Surface
    print("--> [3/6] Resampling OpenFOAM flow fields onto high-res plushy surface...")
    resample = pvs.ResampleWithDataset(
        registrationName="Blahaj_ResampledCFD",
        SourceDataArrays=flow,
        DestinationMesh=shonk_stl
    )
    resample.UpdatePipeline()

    # Surface display properties
    shonk_disp = pvs.Show(resample, view)
    shonk_disp.Representation = "Surface"
    shonk_disp.Ambient = 0.25
    shonk_disp.Diffuse = 0.75
    shonk_disp.Specular = 0.20
    shonk_disp.SpecularPower = 20.0

    # 5. Add Surface Aerodynamic Vector Arrows (Glyphs)
    print("--> [4/6] Generating aerodynamic surface vector glyphs (arrows)...")
    glyphs = pvs.Glyph(
        registrationName="Surface_Vector_Arrows",
        Input=resample,
        GlyphType="Arrow"
    )
    glyphs.OrientationArray = ["POINTS", "U"]
    glyphs.ScaleArray = ["POINTS", "No scale array"]
    glyphs.ScaleFactor = 0.03
    glyphs.GlyphMode = "Uniform Spatial Distribution (Bounds Based)"
    glyphs.MaximumNumberOfSamplePoints = 1800
    glyphs.UpdatePipeline()

    glyph_disp = pvs.Show(glyphs, view)
    glyph_disp.Representation = "Surface"
    glyph_disp.ColorArrayName = ["POINTS", ""]
    glyph_disp.DiffuseColor = [0.12, 0.12, 0.12] # Dark grey/black arrows

    # 6. Save ParaView State (.pvsm)
    state_file = os.path.join(output_dir, "Shonk_UltraPlush.pvsm")
    print(f"--> [5/6] Saving ParaView state file: {state_file}")
    pvs.SaveState(state_file)

    # 7. Render 4-Panel 4:3 Suite (1440x1080)
    print("--> [6/6] Rendering 4:3 high-resolution images for 2x2 diagram...")

    # Color transfers & Colorbars
    p_lut = pvs.GetColorTransferFunction("p")
    p_lut.ApplyPreset("Rainbow Desaturated", True)
    p_bar = pvs.GetScalarBar(p_lut, view)
    p_bar.Title = "Pressure p [m²/s²]"
    p_bar.ComponentTitle = ""
    p_bar.TitleColor = [0.15, 0.15, 0.15]
    p_bar.LabelColor = [0.25, 0.25, 0.25]
    p_bar.Position = [0.80, 0.25]
    p_bar.ScalarBarLength = 0.50

    u_lut = pvs.GetColorTransferFunction("U")
    u_lut.ApplyPreset("Turbo", True)
    u_bar = pvs.GetScalarBar(u_lut, view)
    u_bar.Title = "Velocity |U| [m/s]"
    u_bar.ComponentTitle = ""
    u_bar.TitleColor = [0.15, 0.15, 0.15]
    u_bar.LabelColor = [0.25, 0.25, 0.25]
    u_bar.Position = [0.80, 0.25]
    u_bar.ScalarBarLength = 0.50

    # Panel 1: Isometric Pressure
    pvs.ColorBy(shonk_disp, ("POINTS", "p"))
    p_bar.Visibility = 1
    u_bar.Visibility = 0
    view.CameraPosition = [0.45, -1.10, 0.88]
    view.CameraFocalPoint = [1.50, 0.0, 0.50]
    view.CameraViewUp = [0.20, 0.46, 0.86]
    pvs.Render(view)
    img_pressure = os.path.join(output_dir, "shonk_plushy_pressure.png")
    pvs.SaveScreenshot(img_pressure, view, ImageResolution=[1440, 1080])
    # Also update shonk.png
    pvs.SaveScreenshot(os.path.join(output_dir, "shonk.png"), view, ImageResolution=[1440, 1080])

    # Panel 2: Isometric Velocity Magnitude
    p_bar.Visibility = 0
    u_bar.Visibility = 1
    pvs.ColorBy(shonk_disp, ("POINTS", "U", "Magnitude"))
    pvs.Render(view)
    img_velocity = os.path.join(output_dir, "shonk_plushy_velocity.png")
    pvs.SaveScreenshot(img_velocity, view, ImageResolution=[1440, 1080])

    # Panel 3: Side Profile View
    p_bar.Visibility = 1
    u_bar.Visibility = 0
    pvs.ColorBy(shonk_disp, ("POINTS", "p"))
    view.CameraPosition = [1.50, -1.80, 0.51]
    view.CameraFocalPoint = [1.50, 0.0, 0.51]
    view.CameraViewUp = [0.0, 0.0, 1.0]
    pvs.Render(view)
    img_side = os.path.join(output_dir, "shonk_plushy_side.png")
    pvs.SaveScreenshot(img_side, view, ImageResolution=[1440, 1080])

    # Panel 4: Top Planform View (horizontal: nose left, tail right)
    view.CameraPosition = [1.50, 0.0, 2.20]
    view.CameraFocalPoint = [1.50, 0.0, 0.51]
    view.CameraViewUp = [0.0, 1.0, 0.0]
    pvs.Render(view)
    img_top = os.path.join(output_dir, "shonk_plushy_top.png")
    pvs.SaveScreenshot(img_top, view, ImageResolution=[1440, 1080])

    print("==========================================================")
    print("   2x2 4:3 VISUALIZATION SUITE GENERATED!")
    print(f"   [1/4] Isometric Pressure: {img_pressure}")
    print(f"   [2/4] Isometric Velocity: {img_velocity}")
    print(f"   [3/4] Side Profile View:  {img_side}")
    print(f"   [4/4] Top Planform View:  {img_top}")
    print(f"   State File:               {state_file}")
    print("==========================================================")

if __name__ == "__main__":
    main()
