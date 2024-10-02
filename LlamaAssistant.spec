# -*- mode: python -*-
# vim: ft=python

from PyInstaller.utils.hooks import collect_data_files, get_package_paths
import os, sys

sys.setrecursionlimit(5000)  # required on Windows

# Get the package path
package_path = get_package_paths('llama_cpp')[0]

# Collect data files
datas = collect_data_files('llama_cpp')

# Append the additional .dll or .so file
if os.name == 'nt':  # Windows
    for l in ["ggml", "llama", "llava"]:
        dll_path = os.path.join(package_path, 'llama_cpp', 'lib', f'{l}.dll')
        datas.append((dll_path, 'llama_cpp/lib'))
elif sys.platform == 'darwin':  # Mac
    for l in ["ggml", "llama", "llava"]:
        dylib_path = os.path.join(package_path, 'llama_cpp', 'lib', f'lib{l}.dylib')
        datas.append((dylib_path, 'llama_cpp/lib'))
elif os.name == 'posix':  # Linux
    for l in ["ggml", "llama", "llava"]:
        so_path = os.path.join(package_path, 'llama_cpp', 'lib', f'lib{l}.so')
        datas.append((so_path, 'llama_cpp/lib'))

datas += [
    ('llama_assistant/resources/*.onnx', 'llama_assistant/resources'),
    ('llama_assistant/resources/*.png', 'llama_assistant/resources'),
]

a = Analysis(
    ['llama_assistant/main.py'],
    pathex=['llama_assistant'],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
)
pyz = PYZ(a.pure, a.zipped_data)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name='LlamaAssistant',
    debug=False,
    strip=False,
    upx=False,
    runtime_tmpdir=None,
    console=False,
    icon='llama_assistant/resources/icon.icns',
)
app = BUNDLE(
    exe,
    name='LlamaAssistant.app',
    icon='llama_assistant/resources/icon.icns',
    bundle_identifier=None,
    info_plist={'NSHighResolutionCapable': 'True'},
)
