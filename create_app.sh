rm -rf __pycache__ build dist *.spec
pyinstaller --onefile --windowed --add-binary bin/ffmpeg:bin --add-binary bin/ffprobe:bin --add-binary bin/ffplay:bin --icon vct.icns vct.py
