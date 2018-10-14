VERSION=$1
hdiutil detach "/Volumes/Installer"
hdiutil detach "/Volumes/VCT${VERSION} Installer"
rm -rf __pycache__ build dist VCT*.dmg
#pyinstaller --onefile --windowed --add-binary bin/ffmpeg:bin --add-binary bin/ffprobe:bin --icon vct.icns vct.py -n VCT
pyinstaller VCT_macos.spec
cp ./Installer.dmg.disk tmp.dmg
hdiutil attach ./tmp.dmg
cp -R ./dist/vct.app /Volumes/Installer
diskutil rename "Installer" "VCT${VERSION} Installer"
hdiutil detach "/Volumes/VCT${VERSION} Installer"
rm -rf __pycache__ build dist
hdiutil convert tmp.dmg -format UDZO -o VCT${VERSION}.dmg
rm -rf tmp.dmg