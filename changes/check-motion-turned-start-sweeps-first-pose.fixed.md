`check_motion` let a rotation hide a collision at its first pose. With
`allow_seated_contact` set, a sweep skips step 0 as the installed pose, but a
rotation whose `start_deg` is not 0 has no installed pose there. A dragon's
yaw joint swept -12 to +12 degrees with a wing 3 mm3 inside a leg at -12 and
read clear; only the +12 end failed.

A clear-expecting `rotation_motion_collision` that starts turned now sweeps its
first pose like any other and records `seatedSkipRefused`. Stops (`expect:
blocked`) and sweeps that start at 0 degrees keep the skip, and
`motion-manifests.md` says so.
