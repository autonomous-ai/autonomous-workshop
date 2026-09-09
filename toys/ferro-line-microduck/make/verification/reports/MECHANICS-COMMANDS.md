Run from the Workshop workspace using the managed CAD Python:

```sh
<HOME>/.local/share/autonomous-workshop-python/bin/python artifacts/make/r0001/product/cad/measure/check_fit.py > artifacts/make/r0001/fit-current.json
<HOME>/.local/share/autonomous-workshop-python/bin/python artifacts/make/r0001/product/cad/measure/check_drive.py > artifacts/make/r0001/drive-current.json
<HOME>/.local/share/autonomous-workshop-python/bin/python artifacts/make/r0001/product/cad/measure/motion.py
<HOME>/.local/share/autonomous-workshop-python/bin/python .agents/skills/cad/scripts/check_motion artifacts/make/r0001/product/cad --manifest artifacts/make/r0001/product/cad/measure/motion.json > artifacts/make/r0001/motion-current.txt
<HOME>/.local/share/autonomous-workshop-python/bin/python artifacts/make/r0001/product/cad/measure/export_motion_states.py > artifacts/make/r0001/states-current.json
```

`motion.json` derives its paths, movers, obstacles and kinematics from `motion.py`. The operating path uses a direct1:1 rotor/D-wheel rotation; rear idlers follow10/6 only under the expressly stated ground rolling assumption. Cosmetic installation order is constrained: left shin before left wheel, neck skin before bill. Other forward-facing skins can be installed with the listed other components present. Adhesive bonds are not proven by rigid motion sweeps.

Each CAD change requires rerunning these evidence generators and the presentation generator before treating their hashes as current. Each motion-manifest change requires regenerating the states provenance and the motion presentation even when the underlying kinematics remain the same.

Presentation STL states apply the same rotations and then translate every part by (0,−10θ,0) mm in stationary ground coordinates. Positive X rotation cancels negative Y translation at the bottom contact. One revolution illustrates 62.832 mm under no slip; the body-coordinate collision audit is invariant under this common translation.
