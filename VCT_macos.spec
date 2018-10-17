# -*- mode: python -*-

block_cipher = None


a = Analysis(['vct.py'],
             pathex=['/Users/jgd/repos/conv_to'],
             binaries=[('bin/ffmpeg', 'bin'), ('bin/ffprobe', 'bin')],
             datas=[],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='VCT',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=False , icon='vct.icns')
app = BUNDLE(exe,
             name='VCT.app',
             icon='vct.icns',
             bundle_identifier=None,
             info_plist={
                          'NSPrincipleClass': 'NSApplication',
                          'NSAppleScriptEnabled': False, 
                          'NSHighResolutionCapable': 'True'
                        }
            )