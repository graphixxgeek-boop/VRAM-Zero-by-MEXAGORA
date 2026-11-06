# Changelog

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versions follow [Semantic Versioning](https://semver.org/).

## [2.0.1] - 2026-11-06

Maintenance release: safety and reliability fixes only, no new feature.

### Fixed
- A failed `nvidia-smi` call was displayed as "VRAM available / no process". The display now distinguishes valid, partial and unavailable data.
- Before terminating, each process is re-read and its PID and name compared; a PID reused by another program is skipped, and nothing is terminated if the list cannot be re-read.
- Termination runs outside the interface thread, with a 10-second limit per process; the window no longer freezes.
- Windows refusals (insufficient rights), timeouts and already-closed processes are reported explicitly.
- The confirmation now shows the PID of every process.
- Critical system names are checked before AI keywords.
- The report uses the last collected data with its timestamp instead of calling `nvidia-smi` from the interface; the legend no longer calls AI tools "risk-free".
- README wording about network and disk now describes the application itself.

### Changed
- Unrecognized programs are shown in grey instead of being hidden as critical; unreadable names (`[Insufficient Permissions]`) are labelled as not identifiable. Neither is ever included in "Terminate all" or "Terminate AI".
- Fixed list of processes never included in "Terminate all": Claude, Docker, WSL.

### Added
- Unit tests without a GPU (`tests/`), run by the build workflow before compilation.

## [2.0.0] - 2026-10-21

### Changed
- Project renamed from VRAM Cleaner to **VRAM Zero**.
- Source moved to `src/vram_zero.pyw`; icons and images moved to `assets/`.
- Process classification now compares executable names instead of loose substrings of the full path. Critical entries are checked before non-essential ones.

### Added
- Windows installer (Inno Setup script in `installer/`).
- Executable metadata (publisher, product, version).
- Automated build with GitHub Actions.
- Support for several NVIDIA GPUs (totals are summed).
- Illustration in the About window.

### Fixed
- Console windows flashing at each refresh.
- Selection lost on every refresh.
- Interface freezing while `nvidia-smi` runs (refresh now runs in the background).
- Duplicate refresh at startup and one redundant `nvidia-smi` call per cycle.
- Process names containing commas not being parsed.

## [1.3] - VRAM Cleaner

Initial public version.
