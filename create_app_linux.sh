VERSION=$1
rm -rf __pycache__ build dist VCT*.dmg VCT.spec *.tar.gz
pyinstaller --onefile --windowed --icon vct.png vct.py -n VCT
mv ./dist/VCT .
rm -rf __pycache__ build dist VCT*.dmg VCT.spec
tar cvzf VCTv${VERSION}-linux-x64.tar.gz VCT
rm VCT
