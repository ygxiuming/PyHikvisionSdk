# Contributing to PyHikvisionSdk / 贡献指南

Thanks for considering a contribution! 🎉  感谢你愿意为本项目贡献代码！

---

## 🐛 Reporting bugs / 报告 bug

Before opening an issue, please:

1. **Check existing issues** — your problem may already be reported.
2. **Run the test suite**:
   ```bash
   python tests/test_integration.py
   ```
   Include the **full output** in your report.
3. **Provide environment info**:
   - OS (Windows 10/11, Ubuntu version, etc.)
   - Python version (`python --version`)
   - Hikvision device model and firmware (if applicable)
   - Exact error message + traceback

Use the [Bug Report template](.github/ISSUE_TEMPLATE/bug_report.md) when filing.

---

## ✨ Suggesting features / 功能建议

Open a [Feature Request](.github/ISSUE_TEMPLATE/feature_request.md) and describe:

- **What** problem you're solving
- **Why** existing APIs aren't sufficient
- **How** you'd expect the API to look (a code snippet helps a lot)

---

## 🛠️ Pull Requests / 提交 PR

### Setup

```bash
git clone https://github.com/<your-username>/PyHikvisionSdk.git
cd PyHikvisionSdk
pip install -r requirements.txt
python tests/test_integration.py    # must print 22/22 passing
```

### Workflow

1. **Fork** the repo and create a feature branch from `main`:
   ```bash
   git checkout -b feature/awesome-thing
   ```
2. **Write code**:
   - Match the existing style (4-space indent, PEP 8, snake_case).
   - **Add Chinese docstrings** to public classes and methods (this project's audience is bilingual).
   - Use `from __future__ import annotations` at the top of new modules to keep Python 3.8 compatibility.
   - Use the `_logger` from `hikvision_sdk.utils.logging` instead of `print()` for diagnostics.
3. **Add tests** in `tests/test_integration.py` (or a new `tests/test_xxx.py`):
   - Tests must run **without** a physical Hikvision device (use unreachable IPs like `192.0.2.x` for negative-path tests).
4. **Run all tests**:
   ```bash
   python tests/test_integration.py
   ```
5. **Commit** with a clear message:
   - `feat: add ARM64 Linux support`
   - `fix: handle empty SYSHEAD in RTSP SDK backend`
   - `docs: clarify timestamp accuracy in README`
6. **Push** and open a Pull Request.

### Code style / 代码风格

- **Public APIs** must have type hints and Chinese docstrings.
- **Internal helpers** can be terser but still need a one-line purpose comment.
- **Don't introduce new third-party dependencies** without discussion (we currently allow only `numpy` and `opencv-python`).
- **Don't modify** files under `hikvision_sdk/_bindings/_*_official.py` directly — those mirror Hikvision's official Python binding. If you need new ctypes structs, add them to the consuming module (e.g. `stream/playback.py`) instead.

### Areas where help is most welcome / 最需要帮助的领域

- 🎯 **NALU parser** for accurate I/P/B frame type detection in `video_file.py`
- 🎯 **ARM Linux support** (Jetson, Raspberry Pi)
- 🎯 **Async API** (`asyncio`) for stream readers
- 🎯 **macOS support** when Hikvision releases a macOS SDK
- 🎯 **More demos** — face capture, ANPR, ISAPI tunneling, two-way audio
- 🎯 **Documentation** — translation, screenshots, video tutorials

---

## 📜 Licensing of contributions

By submitting a PR, you agree that your contributions will be licensed under
the MIT License (the same as the rest of this repository's Python code).

---

Thanks again, and happy hacking! 🚀
