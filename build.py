#!/usr/bin/env python3

import sys
import argparse
import platform as p
import zipfile as z
import cmdscript as c
import clean

APP = 'VCT'
SRC = 'vct'

#-------------------------------------------------------------------------------

def build_MACOSX (ver):
    c.system('hdiutil detach "/Volumes/Installer"')
    c.system('hdiutil detach "/Volumes/{}v{} Installer"'.format(APP, ver))
    #pyinstaller --onefile --windowed --add-binary bin/ffmpeg:bin --add-binary bin/ffprobe:bin --add-binary bin/ffplay:bin --icon SRC.icns SRC.py -n APP
    c.call('pyinstaller {}_macos.spec'.format(APP))
    c.call('cp ./Installer.dmg.disk tmp.dmg')
    c.call('hdiutil attach ./tmp.dmg')
    c.call('cp -R ./dist/{}.app /Volumes/Installer'.format(APP))
    c.call('diskutil rename "Installer" "{}v{} Installer"'.format(APP, ver))
    c.call('hdiutil detach "/Volumes/{}v{} Installer"'.format(APP, ver))
    c.call('hdiutil convert tmp.dmg -format UDZO -o {}v{}.dmg'.format(APP, ver))
    c.call('rm -rf tmp.dmg')

#-------------------------------------------------------------------------------

def build_LINUX (ver):
    c.call('pyinstaller --onefile --windowed --icon {}.png {}.py -n {}'.format(SRC, SRC, APP))
    c.call('mv ./dist/{} .'.format(APP))
    c.call('tar cvzf {}v{}-{}-{}.tar.gz {}'.format(APP, ver, sys.platform, p.architecture()[0], APP))
    c.call('rm {}'.format(APP))

#-------------------------------------------------------------------------------

def build_WINDOWS (ver):
    arch, wfam = p.architecture()
    exe = '{}.exe'.format(APP)

    OK = True

    if arch == '32bit':
        c.call('pyinstaller --onefile --windowed --add-binary bin_win32\\ffmpeg.exe;bin --add-binary bin_win32\\ffprobe.exe;bin --add-binary bin_win32\\ffplay.exe;bin --icon {}.ico {}.py -n {}'.format(SRC, SRC, APP))
    elif arch == '64bit':
        c.call('pyinstaller --onefile --windowed --add-binary bin_win64\\ffmpeg.exe;bin --add-binary bin_win64\\ffprobe.exe;bin --add-binary bin_win64\\ffplay.exe;bin --icon {}.ico {}.py -n {}'.format(SRC, SRC, APP))
    else:
        OK = False
        print ('*** Error: Unsupported Windows architecture [{}]'.format(arch))

    if OK:
        c.call('copy .\\dist\\{} .'.format(exe))
        zipfile = '{}v{}-{}-{}.zip'.format(APP, ver, wfam, arch)
        try:
            Zip = z.ZipFile (zipfile, mode='w', compression=z.ZIP_DEFLATED)
        except:
            print ('Zlib not available. Switching to uncompressed Zip file.')
            Zip = z.ZipFile (zipfile, mode='w', compression=z.ZIP_STORED)
        
        Zip.write(exe)
        Zip.close()
        c.rm_file(exe)

#-------------------------------------------------------------------------------

build_function = {
    'MACOSX':  build_MACOSX,
    'LINUX':   build_LINUX,
    'WINDOWS': build_WINDOWS    
}

#-------------------------------------------------------------------------------

def run (ver):
    clean.run(True)
    platform = c.OS()
    print ('* Building for [{}]({})...'.format(sys.platform, p.architecture()[0]))
    build_function[platform](ver)
    clean.run(False)
   
#-------------------------------------------------------------------------------

if __name__ == "__main__":
    # Get command line
    parser = argparse.ArgumentParser(prog='build.py', description='build unified script')
    parser.add_argument('ver', metavar='<VERSION>', help='version build identifier')
    
    # Always show Help with no params
    if len(sys.argv) < 2:
        parser.print_help()
        clean.run(False)
        sys.exit(1)
    
    args = parser.parse_args()

    try:
        run(args.ver)
    except Exception as exc:
        print(exc)
        print('*** Exception building artifacts !!!')
            
    sys.exit(0)
