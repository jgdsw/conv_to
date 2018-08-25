rm -rf __pycache__ build dist *.spec *.dmg
pyinstaller --onefile --windowed --add-binary bin/ffmpeg:bin --add-binary bin/ffprobe:bin --add-binary bin/ffplay:bin --icon vct.icns vct.py
rm -rf ./VCT/vct.app
cp -R ./dist/vct.app ./VCT
rm -rf __pycache__ build dist *.spec
hdiutil create tmp.dmg -ov -volname "VCT Installer" -fs HFS+ -srcfolder "./VCT"
hdiutil convert tmp.dmg -format UDZO -o VCT.dmg
rm -rf tmp.dmg ./VCT/vct.app