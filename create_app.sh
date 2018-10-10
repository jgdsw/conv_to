VERSION=$1
hdiutil detach "/Volumes/Installer"
hdiutil detach "/Volumes/VCT${VERSION} Installer"
rm -rf __pycache__ build dist *.spec VCT*.dmg
pyinstaller --onefile --windowed --add-binary bin/ffmpeg:bin --add-binary bin/ffprobe:bin --icon vct.icns vct.py
cp ./Installer.dmg.disk tmp.dmg
hdiutil attach ./tmp.dmg
cp -R ./dist/vct.app /Volumes/Installer
diskutil rename "Installer" "VCT${VERSION} Installer"
hdiutil detach "/Volumes/VCT${VERSION} Installer"
rm -rf __pycache__ build dist *.spec
hdiutil convert tmp.dmg -format UDZO -o VCT${VERSION}.dmg
rm -rf tmp.dmg