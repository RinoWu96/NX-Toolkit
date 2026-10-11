# Third-party licenses / 第三方许可证

NX Toolkit's own source code is licensed under the [MIT License](LICENSE).
The packaged exe also contains the third-party components listed below, each under its own license.
Full license texts ship with the exe in the `licenses\` folder (collected by `scripts/collect_licenses.py`).

NX Toolkit 自身的源代码采用 [MIT 许可证](LICENSE)。
打包的 exe 还包含下列第三方组件，各自适用其原有许可证。
完整的许可证原文随 exe 一起放在 `licenses\` 文件夹中（由 `scripts/collect_licenses.py` 收集）。

## 1. Bundled in the exe / exe 内置的组件

### GUI and runtime / 界面与运行时

| Component 组件 | Version 版本 | License 许可证 | Source 来源 |
|---|---|---|---|
| Python runtime (incl. OpenSSL, libffi, expat, bzip2, liblzma, zlib) | 3.11.16 (OpenSSL 3.5.8) | PSF-2.0; bundled libraries under their own licenses, see `licenses/python/LICENSE.txt` | https://www.python.org |
| Microsoft Visual C++ Runtime (`VCRUNTIME140*.dll`) | — | Microsoft Visual C++ Redistributable license | https://learn.microsoft.com/cpp/windows/latest-supported-vc-redist |
| PySide6 / shiboken6, with Qt 6 libraries | 6.12.0 | **LGPL-3.0** (used under LGPL-3.0 of the LGPL-3.0 / GPL-2.0 / GPL-3.0 options) | https://www.qt.io/qt-for-python , Qt source: https://download.qt.io/official_releases/qt/ |
| Pillow | 12.3.0 | MIT-CMU (HPND) | https://github.com/python-pillow/Pillow |
| psutil | 7.2.2 | BSD-3-Clause | https://github.com/giampaolo/psutil |
| setuptools | 84.0.0 | MIT | https://github.com/pypa/setuptools |
| packaging | 26.3 | Apache-2.0 OR BSD-2-Clause | https://github.com/pypa/packaging |

### NSZ / XCZ (nsz and its dependencies / nsz 及其依赖)

| Component 组件 | Version 版本 | License 许可证 | Source 来源 |
|---|---|---|---|
| nsz | 5.0.0 | MIT | https://github.com/nicoboss/nsz |
| zstandard | 0.25.0 | BSD-3-Clause | https://github.com/indygreg/python-zstandard |
| backports.zstd | 1.8.0 | PSF-2.0 | https://github.com/rogdham/backports.zstd |
| pycryptodome / pycryptodomex | 3.24.0 | BSD-2-Clause and Public Domain | https://www.pycryptodome.org |
| enlighten | 1.14.1 | MPL-2.0 | https://github.com/Rockhopper-Technologies/enlighten |
| prefixed | 0.9.0 | MPL-2.0 | https://github.com/Rockhopper-Technologies/prefixed |
| jinxed | 2.1.0 | MPL-2.0 | https://github.com/Rockhopper-Technologies/jinxed |
| ansicon | 1.89.0 | MPL-2.0 | https://github.com/Rockhopper-Technologies/ansicon |
| blessed | 1.50.0 | MIT | https://github.com/jquast/blessed |
| wcwidth | 0.9.2 | MIT | https://github.com/jquast/wcwidth |

### 7z extraction for the tool downloader (py7zr and its dependencies / 工具下载用的 7z 解压)

| Component 组件 | Version 版本 | License 许可证 | Source 来源 |
|---|---|---|---|
| py7zr | 1.1.3 | **LGPL-2.1-or-later** | https://github.com/miurahr/py7zr |
| pybcj | 1.0.8 | **LGPL-2.1-or-later** | https://github.com/miurahr/pybcj |
| pyppmd | 1.3.1 | **LGPL-2.1-or-later** | https://github.com/miurahr/pyppmd |
| inflate64 | 1.0.4 | **LGPL-2.1-or-later** | https://github.com/miurahr/inflate64 |
| multivolumefile | 0.2.3 | **LGPL-2.1-or-later** | https://github.com/miurahr/multivolume |
| brotli | 1.2.0 | MIT | https://github.com/google/brotli |
| texttable | 1.7.0 | MIT | https://github.com/foutaise/texttable |

### Notes on LGPL and MPL components / 关于 LGPL 与 MPL 组件的说明

- All LGPL and MPL components are included **unmodified**. Their source code is available from the links above.
- The Qt / PySide6 libraries and the compiled extension modules ship as separate files (`_internal\PySide6\*.dll`, `*.pyd`) and can be replaced by the user. The pure-Python LGPL modules are stored in the exe's module archive; since NX Toolkit's complete source code and build script (`build.bat`) are published, you can rebuild the exe with a modified version of any of these libraries.
- Full texts: `licenses/LGPL-3.0.txt`, `licenses/GPL-3.0.txt` (referenced by LGPL-3.0), and each package's own license file under `licenses/<package>/`.

- 所有 LGPL 和 MPL 组件均**未经修改**地包含在内，源代码可从上表链接获取。
- Qt / PySide6 库和编译型扩展模块以独立文件形式提供（`_internal\PySide6\*.dll`、`*.pyd`），用户可以自行替换。纯 Python 的 LGPL 模块存放在 exe 的模块归档中；由于 NX Toolkit 的完整源代码和打包脚本（`build.bat`）均已公开，你可以用修改过的库重新打包 exe。
- 许可证全文：`licenses/LGPL-3.0.txt`、`licenses/GPL-3.0.txt`（LGPL-3.0 所引用），以及 `licenses/<包名>/` 下各包自带的许可证文件。

## 2. External tools, NOT bundled / 外部工具（不随程序分发）

NX Toolkit runs these command-line tools as separate programs. They are **not** included in this repository or in the release zip; the optional in-app downloader fetches them from the original SAK release on GitHub. Each tool is governed by its own license.

NX Toolkit 以独立进程的方式调用下列命令行工具。它们**不**包含在本仓库或发布的压缩包中；程序内可选的下载功能会从原版 SAK 的 GitHub 发布包获取它们。各工具适用其自身的许可证。

| Tool 工具 | Authors 作者 | License 许可证 | Source 来源 |
|---|---|---|---|
| 4NXCI | The-4n, SciresM | ISC (per `4nxci_LICENSE` in the SAK release) | https://github.com/The-4n/4NXCI |
| hacBrewPack / hptnacp | The-4n | GPL-2.0 (per `hacbrewpack_LICENSE` in the SAK release) | https://github.com/The-4n/hacBrewPack |
| reNXpack (shipped in SAK, not used) | The-4n, SciresM | ISC (per `renxpack_LICENSE` in the SAK release) | https://github.com/The-4n/reNXpack |
| hactool | SciresM | see upstream / 见上游项目 | https://github.com/SciresM/hactool |
| LibHac / hactoolnet | Thealexbarney | see upstream / 见上游项目 | https://github.com/Thealexbarney/LibHac |
| NSC_BUILDER (squirrel) | julesontheroad | see upstream / 见上游项目 | https://github.com/julesontheroad/NSC_BUILDER |
| nx-hbloader (forwarder builds) | switchbrew; forks by R-YaTian, HookedBehemoth, dezem | see upstream / 见上游项目 | https://github.com/switchbrew/nx-hbloader |
| Switch Army Knife (SAK) | kempa / dezem | no license stated / 未声明许可证 | https://github.com/dezem/SAK |

NX Toolkit contains none of SAK's code; SAK is credited as the inspiration for the feature set and workflow.
NX Toolkit 不包含 SAK 的任何代码；SAK 作为功能划分与流程的灵感来源予以致谢。
