#!/usr/bin/env python3

import sys
import os
import os.path
import argparse
import subprocess
import glob
import locale
import tempfile
import re
from pathlib import Path
from titlecase import titlecase

#-------------------------------------------------------------------------------

def sep():
    print('---------------------------------------------------------------------------')

#-------------------------------------------------------------------------------

def delete_file (file):
    if os.path.isfile(file) and os.access(file, os.R_OK):
        try:
            os.remove(file)
        except OSError as err:
            return False
    return True

#-------------------------------------------------------------------------------

def get_files (file_pattern='*.*', verbose=False):
    """Obtains and return a list of files from an specific file pattern"""
    if verbose:
        print('get_files: file_pattern:({})'.format(file_pattern))

    file_list = []

    for file in glob.glob(file_pattern):
        file_list.append(file)

    if len(file_list) == 0:
        file_list = [file_pattern]

    if verbose:
        print('get_files: file_list:({})'.format(file_list))

    return file_list

#-------------------------------------------------------------------------------

def _filter_out (str_list):
    filtered_list = []
    for item in str_list:
        filtered_list.append(item.strip())
    return filtered_list

#-------------------------------------------------------------------------------

def exec_command (cmd, get_stdout=True, get_stderr=False, file_stdin='', file_stdout='', file_stderr='', exit=False, verbose=False):
    """Executes a given command. Returns the status completion, stdout and stderr of the command"""
    if verbose:
        print('exec:({})'.format(cmd))

    stdin_run = None
    stdout_run = None
    stderr_run = None

    if file_stdin != '':
        stdin_run = open(file_stdin, 'r')

    if file_stdout != '':
        get_stdout = False
        stdout_run = open(file_stdout,'w')

    if get_stdout:
        stdout_run=subprocess.PIPE

    if file_stderr != '':
        get_stderr = False
        stderr_run = open(file_stderr,'w')

    if get_stderr:
        stderr_run=subprocess.PIPE

    cp = subprocess.run(cmd, shell=True, stdin=stdin_run, stdout=stdout_run, stderr=stderr_run)

    if file_stdin != '':
        stdin_run.close()

    if file_stdout != '':
        stdout_run.close()

    if file_stderr != '':
        stderr_run.close()

    if verbose:
        print(cp)

    # Output STDOUT stream if requested
    try:
        str_out = cp.stdout.decode('utf-8', 'replace')
        out = str_out.splitlines()
        out = _filter_out(out)
        if len(out) != 0:
            if out[-1] == '':
                out=out[:-1]
    except:
        out = []

    # Output STDERR stream if requested
    try:
        str_err = cp.stderr.decode('utf-8', 'replace')
        err = str_err.splitlines()
        err = _filter_out(err)
        if len(err) != 0:
            if err[-1] == '':
                err=err[:-1]
    except:
        err = []

    # Output return status
    status = cp.returncode

    if verbose:
        print('status:({})\nstdout:({}, "{}")\nstderr:({}, "{}")'.format(status, out, file_stdout, err, file_stderr))

    if exit:
        if status != 0:
            sys.exit('exec: Error [{}] executing ["{}"]'.format(status, cmd))

    return status, out, err

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
    st, out, err = exec_command(ffprobe_args)

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
        flist = get_files(f)
        files_expanded = files_expanded + flist

    files_out = {}

    # for each file
    for file in files_expanded:
        
        if main:
        	sep()

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
    	sep()

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
