# 6809 implementation

This folder will contain:

- the bit-exact model and training engine;
- optimized fixed-point multiply-accumulate kernels;
- deterministic PRNG and lookup tables;
- the CoCo 1 VDG text and semigraphics front end;
- the CoCo 3 presentation front end;
- CoCo SDC and FujiNet loadable artifacts during development;
- emulator and physical-hardware test procedures.

The learning engine must not depend on CoCo 3 memory banking, GIME video
features, or fast mode. Platform-specific code belongs behind narrow display,
keyboard, timing, and storage interfaces.
