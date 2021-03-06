#!/usr/bin/env python3

import sys
import os
import os.path
import argparse
import subprocess
import platform
import glob
import locale
import tempfile
import re
from pathlib import Path
from titlecase import titlecase
import cmdscript as c

#-------------------------------------------------------------------------------

def _filter_out (str_list):
    filtered_list = []
    for item in str_list:
        filtered_list.append(item.strip())
    return filtered_list

#-------------------------------------------------------------------------------

def ToInt (value):
    try:
        ival=int(value)
        return ival
    except:
        return -1

#-------------------------------------------------------------------------------

def get_file_tag (file, bins=''):

    tag=''
    ffprobe_video = '{}ffprobe -v error -print_format csv -show_streams -select_streams v -show_entries stream=index,codec_name,width,height,bit_rate -i "{}"'

    ffprobe_args = ffprobe_video.format(bins, file)
    st, out, err = c.exec(ffprobe_args, get_stdout=True)

    if st == 0:
        for line in out:
            lv = line.split(',')
            if lv[0] == 'stream':

                lv = lv[1:6]
                index = ToInt(lv[0])
                codec = lv[1]
                width = ToInt(lv[2])
                height = ToInt(lv[3])
                bitrate = lv[4]

                # Only the first one is returned
                tag = '[{}x{}-{}]'.format(width, height, codec)
                return st, tag

    return st, tag

#-------------------------------------------------------------------------------

def set_file_tag (files, main=False, bins=''):

    # File wilcards expansion
    # Windows support !!
    files_expanded=[]
    for f in files:
        flist = c.get_files(f)
        files_expanded = files_expanded + flist

    files_out = {}

    # for each file
    for file in files_expanded:

        if main:
        	c.sep()

        # Get file tag
        st, tag = get_file_tag(file, bins)

        if (st == 0):

            # Input filename
            file_in = os.path.abspath(file)
            dirname = os.path.dirname(file_in)
            file_bn = os.path.basename(file_in)

            f_path = Path(file_bn)
            file_wext = f_path.with_suffix('')
            file_ext = f_path.suffix

            # Clean Base filename
            file_base = '{}'.format(file_wext)
            file_base = re.sub(r'\[[^()]*\]', '', file_base)
            file_base = re.sub(r'\.ffmpeg', '', file_base)
            file_base = file_base.replace('..', ' ')
            file_base = file_base.replace('_', ' ')
            file_base = file_base.replace('.', ' ')
            file_base = file_base.replace('  ', ' ')
            file_base = file_base.strip()
            file_base = file_base.lower()
            #file_base = file_base.title()
            # More rebust capitalization
            file_base = titlecase(file_base)
            file_base = file_base.replace(' Iii', ' III')
            file_base = file_base.replace(' Ii', ' II')
            file_base = file_base.replace(' Iv', ' IV')
            file_base = file_base.replace('Hd', 'HD')
            file_base = file_base.replace('Dvd', 'DVD')
            file_base = file_base.replace('Fhd', 'FHD')
            file_base = file_base.replace('Uhd', 'UHD')
            file_base = file_base.replace('Vcd', 'VCD')

            # Output filename
            file_out = '{} {}{}'.format(file_base, tag, file_ext)
            file_out = os.path.join(dirname, file_out)

            # Show results
            print('>>> Tag File: "{}"'.format(file_in))

            files_out[file] = file_out

            # Final rename
            if file_in == file_out:
                print ('>>> No file renaming needed')
            else:
                print('    TAG: {}\n    NAM: "{}"'.format(tag, file_base))
                try:
                	os.rename(file_in, file_out)
                	print('>>> Renamed to: "{}"'.format(file_out))
                except OSError as err:
                    print('!!! ERROR renaming to: "{}"'.format(file_out))
                    files_out[file] = ''

        else:
            print('!!! ERROR Tagging File: "{}"'.format(file))
            files_out[file] = ''

    if main:
    	c.sep()

    return files_out

#-------------------------------------------------------------------------------

if __name__ == "__main__":
    # Get command line
    parser = argparse.ArgumentParser(prog='conv_to', description='v1.4: Insert descriptive tags for video file names')
    parser.add_argument('files', metavar='<FILE>', nargs='+', help='file/s to process')

    # Always show Help with no params
    if len(sys.argv) < 2:
        parser.print_help()
        sys.exit(1)

    # Parse arguments
    args = parser.parse_args()

    # Call action function
    set_file_tag(args.files, main=True)
