# Native core build boundary

The optional C++17/OpenMP core is under `core/` and exposes a C ABI consumed
by `ctypes` in `invariantq/core/binding.py`. Linux uses `libinvariantq.so`;
macOS uses `libinvariantq.dylib`; MinGW-compatible Windows builds use
`invariantq.dll` or `libinvariantq.dll`.

On Linux/macOS with `make`, run:

```bash
make -C core
cp core/libinvariantq.so invariantq/core/  # Linux; use the platform artifact on macOS
python -m pytest -q tests/test_core_math.py tests/test_core_diagnostics.py
```

The current Windows environment does not provide `make` or a MinGW toolchain,
so native compilation/runtime is unverified here. The portable implementation
must report `portable-numpy-fallback`; it must never claim native execution.
The CI package/native job is the reproducible Linux validation boundary.
