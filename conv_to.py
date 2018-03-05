#!/usr/bin/env python3

import sys
import os
import os.path
import argparse
import subprocess
import locale
import tempfile
import vidtag
from pathlib import Path


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

def exec_command (cmd, get_output=True, info=True):

    if info:
        print('\n[{}]'.format(cmd))

    # De-construct command in list is not needed if command is going to be
    # passed through the OS shell 
    # cmd = [cmd]

    try:
        if get_output:
            cp = subprocess.check_output(cmd, shell=True)
            status = 0
            str_out = cp.decode(sys.stdout.encoding)
            out = str_out.split('\n')
            if out[-1] == '':
                out=out[:-1]
        else:
            cp = subprocess.call(cmd, shell=True)
            status = cp
            out = []
    except:
        print('')
        print('')
        print('!!! External command failed or aborted')
        print('')

        out = []
        status = 9999

    if info:
        print('')

    return status, out

#-------------------------------------------------------------------------------

def join_input_files (files, f_out, args):
    global ffmpeg_join, info

    sep()

    # Remove out file
    if not delete_file(f_out):
        sys.exit('\n!!! ERROR: Removing output file:{}'.format(f_out))

    # Create temporary file
    tmppath = '.conv_to.join.{}'.format(os.getpid())
 
    # Remove temporary file
    if not delete_file(tmppath):
        sys.exit('\n!!! ERROR: Removing temporary file:{}'.format(tmppath))
 
    # Writing temporary file stream
    tmp = open(tmppath, 'w')
    for f in files:
        print('file \'{}\''.format(f), file=tmp)
        print('>>> Registering file [{}] ...'.format(f))
    tmp.close()

    # Command to join
    join_command = ffmpeg_join.format(info[args.verbose], tmppath, f_out)
    st, out = exec_command(join_command, get_output=False, info=args.verbose)

    # Remove temporary file
    if not delete_file(tmppath):
        sys.exit('\n!!! ERROR: Removing temporary file:{}'.format(tmppath))

    # File Joined
    print('>>> Input files joined to: [{}]'.format(f_out))

    sep()

#-------------------------------------------------------------------------------

def ToInt (value):
    try:
        ival=int(value)
        return ival
    except:
        return -1

#-------------------------------------------------------------------------------

def get_video_streams (file, options, args, info=False):
    global ffprobe_video, video_resolution, video_container, stream_video_quality, \
           OV_stream, O_copy, rotate180, video_filters 

    ffprobe_args = ffprobe_video.format(file)
    st, out = exec_command(ffprobe_args, info=args.verbose)

    header=False

    if st == 0:
        for line in out:

            lv = line.split(',')

            if lv[0] == 'stream':

                lv = lv[1:6]

                index = ToInt(lv[0].strip())
                codec = lv[1].strip()
                width = ToInt(lv[2].strip())
                height = ToInt(lv[3].strip())
                bitrate = lv[4].strip()

                if codec not in ignored_codecs:

                    if info:
                        # Just show information
                        print('# Video[{}]: {}, {}x{}, BR:{}'.format(index, codec, width, height, bitrate))

                    else:
                        # Manage Options
                        print('# Video[{}]: {}, {}x{} --> '.format(index, codec, width, height), end='')
    
                        # Codec patch
                        if codec == 'xvid':
                            codec = 'mpeg4'
                
                        # Smart resize detection
                        resize = False
                        scale_v = ''
                        if args.resol != 'input' and not header:
                            if width > video_resolution[args.resol][0]:
                                scale_v = video_resolution[args.resol][1] 
                                width = video_resolution[args.resol][0]
                                resize = True          
                        
                        # libx264 restriction about odd sizes
                        if not resize and not header:
                            if (width % 2 == 1) or (height % 2 == 1):
                                scale_v = 'scale=trunc(iw/2)*2:trunc(ih/2)*2' 
                                resize = True

                        # Rotate 180
                        flip = False
                        flip_v = ''
                        if args.flip and not header:
                            flip_v = rotate180
                            flip = True

                        # Deal with filter separator if both filters present
                        if resize and flip:
                            filter_sep = ','
                        else:
                            filter_sep = ''
 
                        # Final video filters option
                        if resize or flip:
                            stream_filter = video_filters.format(flip_v, filter_sep, scale_v)
                            options.append(stream_filter)

                        # Container headers
                        if not header:
                            options.append(video_container[args.container][1])
                            header=True

                        # Process Stream
                        if codec != video_container[args.container][0] or \
                           args.fps != 0.0 or resize or flip or args.force:
                            # Reencode streama
                            vr = args.resol + '-' + args.container 
                            stream = OV_stream.format(index, index, stream_video_quality[vr])  
                            print('{}:{}, Resolution:{} (max width={} px)'.format(args.container, 
                                  video_container[args.container][0], args.resol, width))
                        else:
                            # Copy stream
                            stream = OV_stream.format(index, index, O_copy)
                            print('Copy video stream')

                        options.append(stream)

                else:
                    print('# Video[{}]: {}, {}x{}, BR:{} --> Ignored CODEC'.format(index, codec, width, height, bitrate))

    return st

#------------------------------------------------------------------------------

def get_audio_streams (file, options, args, info=False):
    global ffprobe_audio, stream_audio_quality, OA_stream, O_copy
   
    if args.no_audio and not info:
        # Do not copy audio streams
        options.append(stream_audio_quality['none'][1])
        print('# Audio[X]: Do not process audio streams')
        st = 0

    else:
        # Get audio streams info
        ffprobe_args = ffprobe_audio.format(file)
        st, out = exec_command(ffprobe_args, info=args.verbose)

        if st == 0:

            for line in out:

                lsa = line.split(',')

                if lsa[0] == 'stream':

                    la = lsa[1:3]

                    try: 
                        la.append(lsa[15])
                    except:
                        la.append('und')

                    index = ToInt(la[0].strip())
                    codec = la[1].strip()
                    title = la[2].strip()

                    if codec not in ignored_codecs:

                        if info:
                            # Just show file information
                            print('# Audio[{}]: {} ({})'.format(index, codec, title))

                        else:
                            # Process audio stream
                            print('# Audio[{}]: {} ({}) --> '.format(index, codec, title), end='')

                            # Codec patch
                            if codec == 'ac3':
                                codec = 'aac'

                            # Process Stream
                            if codec != stream_audio_quality[args.container][0] or \
                               args.fps != 0.0 or args.force:
                                # Reencode streama
                                stream = OA_stream.format(index, index, stream_audio_quality[args.container][1])
                                print('{}'.format(stream_audio_quality[args.container][0]))
                            else:
                                # Copy stream
                                stream = OA_stream.format(index, index, O_copy)
                                print('Copy audio stream')

                            options.append(stream)

                    else:
                        print('# Audio[{}]: {} ({}) --> Ignored CODEC'.format(index, codec, title))

    return st

#------------------------------------------------------------------------------

def extract_subs_to_SRT (args, file, index, title):
    # Output filename
    f_path = Path(file)
    file_wext = f_path.with_suffix('')
    srt = '{}.{}.{}'.format(file_wext, title, 'srt')
    print('"{}"'.format(srt))

    srt_command = OS_SRT_extraction.format(file, index, srt)
    exec_command(srt_command, get_output=False, info=args.verbose)

#------------------------------------------------------------------------------

def get_subs_streams (file, options, args, info=False):
    global subtitles, ffprobe_subs, O_copy, OS_stream

    if args.no_subs and not info:
        # Do not copy audio streams
        options.append(subtitles['none'])
        print('# Subtitle[X]: Do not process subtitles streams')
        st = 0

    else:
        # Get audio streams info
        ffprobe_args = ffprobe_subs.format(file)
        st, out = exec_command(ffprobe_args, info=args.verbose)

        if st == 0:

            subs=False

            for line in out:

                lss = line.split(',')

                if lss[0] == 'stream':

                    ls = lss[1:3]

                    try:
                        ls.append(lss[15])
                    except:
                        ls.append('und')

                    index = ToInt(ls[0].strip())
                    codec = ls[1].strip()
                    title = ls[2].strip()

                    if codec not in ignored_codecs:

                        if info:
                            # Just show stream info
                            print('# Subtitle[{}]: {} ({})'.format(index, codec, title))

                        else:
                            if args.container != 'avi':
                                # Process stream data
                                print('# Subtitle[{}]: {} ({}) --> '.format(index, codec, title), end='')

                                # Process Stream
                                stream = OS_stream.format(index)
                                print('{}'.format(subtitles[args.container]))

                                options.append(stream)
                                subs = True
                            else:
                                # Stream is text based. An SRT file has to be extracted
                                print('# Subtitle[{}]: {} ({}) --> {}: '.format(index, codec, title, subtitles[args.container]), end='')
                                extract_subs_to_SRT(args, file, index, title)
                    else:
                        print('# Subtitle[{}]: {} ({}) --> Ignored CODEC (only text subtitles supported)'.format(index, codec, title))
 
                if subs:
                    # Codec for subtitles streams (MP4)
                    options.append(OS_codec.format(subtitles[args.container]))
                else:
                    # No subtitles inside XVID file
                    options.append(subtitles['none'])

    return st

#-------------------------------------------------------------------------------

def show_file_size (file):
    f = Path(file)
    try:
        s = os.path.getsize(f)
        size = ((s/1024)/1024)
    except OSError:
        size = 0
    print('# Size: {:.2f} MB'.format(size))

#-------------------------------------------------------------------------------

def convert_video_file (file, file_out, args):
    global exit_code, info, video_container, video_resolution, FPS

    options = []
    
    if args.fps != 0.0:
        options.append(FPS.format(args.fps))

    st_v = st_a = st_s = 255

    show_file_size(file)
    st_v = get_video_streams(file, options, args)
    if st_v == 0:
        st_a = get_audio_streams(file, options, args)
    if st_a == 0:
        st_s = get_subs_streams(file, options, args)

    if st_v == 0 and st_a == 0 and st_s == 0:
        # Correct stream data
        # Building FFMPEG command
        options_string = ''
        for opt in options:
            options_string = options_string + opt + ' '
        options_string = options_string.strip()

        # Final command
        comm = ffmpeg_comm.format(info[args.verbose], file, options_string, file_out)
        st, out = exec_command(comm, get_output=False, info=args.verbose)
        exit_code = st

    else:
        # Error obtaining streams data
        exit_code = 255

#-------------------------------------------------------------------------------

def get_file_info (file, args):

    options = []

    st_v = st_a = st_s = 255

    show_file_size(file)
    st_v = get_video_streams(file, options, args, info=True)
    st_a = get_audio_streams(file, options, args, info=True)   
    st_s = get_subs_streams(file, options, args, info=True)

    if st_v != 0 or st_a != 0 or st_s != 0:
        # Error obtaining streams data
        exit_code = 255

#-------------------------------------------------------------------------------

def convert_audio_file (file, file_out, args):
    global audio_container, info, exit_code

    audio_command = audio_container[args.container].format(info[args.verbose], file, file_out)
    st, out = exec_command(audio_command, get_output=False, info=args.verbose)
    exit_code = st

#-------------------------------------------------------------------------------

# Is the container a video container?
video = {
'mp4': True,
'avi': True,
'mkv': True,
'm4a': False,
'ogg': False,
'mp3': False
}

# FFMPEG command for dealing with audio containers
audio_container = {
'mp3': 'ffmpeg -stats -hide_banner -y {} -i "{}" -map_metadata 0 -vcodec png -ac 2 -c:a libmp3lame -b:a 160k -r:a 48000 "{}"',
'm4a': 'ffmpeg -stats -hide_banner -y {} -i "{}" -map_metadata 0 -vn -ac 2 -c:a aac -b:a 160k -r:a 48000 "{}"',
'ogg': 'ffmpeg -stats -hide_banner -y {} -i "{}" -map_metadata 0 -vn -ac 2 -c:a libvorbis -b:a 160k -r:a 48000 "{}"'
}

# FFMPEG options for video containers general options
video_container = {
'mp4': ('hevc',  '-map_metadata 0 -f mp4 -movflags faststart -pix_fmt yuv420p'),
'mkv': ('hevc',  '-map_metadata 0 -f matroska -pix_fmt yuv420p'),
'avi': ('mpeg4', '-map_metadata 0 -f avi -vtag xvid -pix_fmt yuv420p')
}

# FFMPEG options for scaling video streams
video_resolution = {
'input': (0, ''),
'std':   (512,  'scale=512:trunc(ow/a/2)*2'),
'VCD':   (352,  'scale=352:trunc(ow/a/2)*2'),
'DVD':   (720,  'scale=720:trunc(ow/a/2)*2'),
'HD':    (1280, 'scale=1280:trunc(ow/a/2)*2'),
'FHD':   (1920, 'scale=1920:trunc(ow/a/2)*2'),
'UHD':   (3840, 'scale=1920:trunc(ow/a/2)*2'),
'DCI':   (4096, 'scale=1920:trunc(ow/a/2)*2')
}

# FFMPEG options for video streams in video files
stream_video_quality = {
'input-avi': 'mpeg4 -q:v 0 -g 300 -bf 2 -qscale:v 0',
'input-mp4': 'libx265 -preset ultrafast -x265-params crf=23',
'input-mkv': 'libx265 -preset ultrafast -x265-params crf=23',
'std-avi':   'mpeg4 -q:v 0 -b:v 900k -g 300 -bf 2',   #900k
'std-mp4':   'libx265 -preset ultrafast -x265-params crf=24',
'std-mkv':   'libx265 -preset ultrafast -x265-params crf=24',
'VCD-avi':   'mpeg4 -q:v 0 -b:v 400k -g 300 -bf 2',   #400k
'VCD-mp4':   'libx265 -preset ultrafast -x265-params crf=25',
'VCD-mkv':   'libx265 -preset ultrafast -x265-params crf=25',
'DVD-avi':   'mpeg4 -q:v 0 -b:v 1800k -g 300 -bf 2',  #1800k
'DVD-mp4':   'libx265 -preset ultrafast -x265-params crf=23',
'DVD-mkv':   'libx265 -preset ultrafast -x265-params crf=23',
'HD-avi':    'mpeg4 -q:v 0 -b:v 4000k -g 300 -bf 2',  #4000k
'HD-mp4':    'libx265 -preset ultrafast -x265-params crf=22',
'HD-mkv':    'libx265 -preset ultrafast -x265-params crf=22',
'FHD-avi':   'mpeg4 -q:v 0 -b:v 8500k -g 300 -bf 2',  #8500k
'FHD-mp4':   'libx265 -preset ultrafast -x265-params crf=22:qcomp=0.8:aq-mode=1:aq_strength=1.0:qg-size=16:psy-rd=0.7:psy-rdoq=5.0:rdoq-level=1:merange=44',
'FHD-mkv':   'libx265 -preset ultrafast -x265-params crf=22:qcomp=0.8:aq-mode=1:aq_strength=1.0:qg-size=16:psy-rd=0.7:psy-rdoq=5.0:rdoq-level=1:merange=44',
'UHD-avi':   'mpeg4 -q:v 0 -b:v 10000k -g 300 -bf 2', #10000k
'UHD-mp4':   'libx265 -preset ultrafast -x265-params crf=20:qcomp=0.8:aq-mode=1:aq_strength=1.0:qg-size=16:psy-rd=0.7:psy-rdoq=5.0:rdoq-level=1:merange=44',
'UHD-mkv':   'libx265 -preset ultrafast -x265-params crf=20:qcomp=0.8:aq-mode=1:aq_strength=1.0:qg-size=16:psy-rd=0.7:psy-rdoq=5.0:rdoq-level=1:merange=44',
'DCI-avi':   'mpeg4 -q:v 0 -b:v 12000k -g 300 -bf 2', #12000k
'DCI-mp4':   'libx265 -preset ultrafast -x265-params crf=20:qcomp=0.8:aq-mode=1:aq_strength=1.0:qg-size=16:psy-rd=0.7:psy-rdoq=5.0:rdoq-level=1:merange=44',
'DCI-mkv':   'libx265 -preset ultrafast -x265-params crf=20:qcomp=0.8:aq-mode=1:aq_strength=1.0:qg-size=16:psy-rd=0.7:psy-rdoq=5.0:rdoq-level=1:merange=44'
}

# FFMPEG options for audio streams quality in video files
stream_audio_quality = {
'none': ('', '-an'),
'avi':  ('mp3', 'libmp3lame -q:a 0 -r:a 48000 -ac 2'),
'mp4':  ('aac', 'aac -b:a 160k -r:a 48000 -ac 2'),
'mkv':  ('vorbis', 'libvorbis -b:a 160k -r:a 48000 -ac 2')
}

# FFMPEG options for subtitles
subtitles = {
'none': '-sn', 
'avi':  'SRT File', # It will never be used as codec inside AVI. SRT extraction instead. 
'mp4':  'mov_text',
'mkv':  'subrip'
}

# FFMPEG Options for log level
info = {
True:  '-v info',
False: '-v error'
}

# Problematic codecs to ignore
ignored_codecs = ['mjpeg', 'hdmv_pgs_subtitle', 'xsub', 'dvd_subtitle']

# FFMPEG options
FPS = '-r {}'
rotate180 = 'hflip,vflip'
video_filters = '-vf "{}{}{}"'
O_copy = 'copy'
OV_stream = '-map 0:{} -c:v:{} {}'
OA_stream = '-map 0:{} -c:a:{} {}'
OS_stream = '-map 0:{}'
OS_codec = '-c:s {}'
OS_SRT_extraction = 'ffmpeg -stats -hide_banner -y -v error -i "{}" -map 0:{} "{}"'

# FFMPEG commands
ffmpeg_comm = 'ffmpeg -nostdin -stats -hide_banner -y {} -i "{}" {} -max_muxing_queue_size 1024 "{}"' 
ffmpeg_join = 'ffmpeg -nostdin -safe 0 -stats -hide_banner -y {} -f concat -i "{}" -c copy -max_muxing_queue_size 1024 "{}"'

ffprobe_video = 'ffprobe -v error -print_format csv -show_streams -select_streams v -show_entries stream=index,codec_name,width,height,bit_rate -i "{}"'
ffprobe_audio = 'ffprobe -v error -print_format csv -show_streams -select_streams a -show_entries stream=index,codec_name:stream_tags=language -i "{}"'
ffprobe_subs  = 'ffprobe -v error -print_format csv -show_streams -select_streams s -show_entries stream=index,codec_name:stream_tags=language -i "{}"'

# Exit status
exit_code = 0

# Get command line
parser = argparse.ArgumentParser(prog='conv_to', description='v2.17: Wrapper to ffmpeg video manipulation utility. Default: MP4 (input resolution)')
parser.add_argument('-v', '--verbose', help='show extra log information', action='store_true')
parser.add_argument('-d', '--delete', help='delete/remove original input file/s', action='store_true')
parser.add_argument('-e', '--force', help='force re-encoding of input files', action='store_true')
parser.add_argument('-i', '--info', help='show file information', action='store_true')
parser.add_argument('-na', '--no_audio', help='do not include audio', action='store_true')
parser.add_argument('-ns', '--no_subs', help='do not include subtitles', action='store_true')
parser.add_argument('-fl', '--flip', help='flip video (rotate video 180º)', action='store_true')
parser.add_argument('-t', '--tag', help='tag video files width vidtag', action='store_true')
parser.add_argument('-f', '--fps', metavar='#FPS', help='output FPS value', default=0.0, type=float)
parser.add_argument('-j', '--join_to', metavar='<JOINED_FILE>', help='Joined output file (same codec expected in input files)', default='')
parser.add_argument('-c', '--container', metavar='<mp4|avi|mkv|m4a|mp3|ogg>', 
                    help='output container/codec file format (not used in join operations', 
                    choices=['mp4', 'avi', 'mkv', 'm4a', 'mp3', 'ogg'], default='mp4')
parser.add_argument('-r', '--resol', metavar='<input|std|VCD|DVD|HD|FHD|UHD|DCI>', 
                    help='standard resolution to use (not used in join operations). input=same as input, std=max width 542px, VCD=max width 352px, DVD=max width 720px, HD=max width 1280px, FHD=max width 1920px, UHD=max width 3840px, DCI=max width 4096px',
                    choices=['input', 'std', 'VCD', 'DVD', 'HD', 'FHD', 'UHD', 'DCI'], default='input')  
parser.add_argument('files', metavar='<FILE>', nargs='+', help='file/s to process')

# Always show Help with no params
if len(sys.argv) < 2:
    parser.print_help()
    sys.exit(1)

# Parse arguments
args = parser.parse_args()

if len(args.join_to)==0:
    # Info
    if args.info:
        print('*** Show file information:')
    else:
        print('*** Convert to: [{}]'.format(args.container))
        if args.verbose:
            print('*** [Resolution={}, FPS={}, Force_encode={}]'.format(args.resol, args.fps, args.force))
        print('*** [Delete Input Files={}]'.format(args.delete))

    for file in args.files:

        sep()

        # Test file existence
        if os.path.isfile(file) and os.access(file, os.R_OK):

            # Output filename
            f_path = Path(file)
            file_in = str(f_path)
            file_wext = f_path.with_suffix('')
            file_out = '{}.{}'.format(file_wext, args.container)
            if file_out == file_in:
                file_out = '{}.ffmpeg.{}'.format(file_wext, args.container)

            if args.info:
                print('>>> File: [{}]'.format(file))

                get_file_info(file, args)

                if exit_code != 0:
                    print('!!! ERROR: Reading File [{}] (exit code {})'.format(file, exit_code))

            else:
                print('>>> Converting file [{}]\n                to: [{}]...'.format(file_in,file_out))

                # The file exists
                if video[args.container]:
                    # Video conversion
                    convert_video_file(file, file_out, args)
                else:
                    # Audio conversion
                    convert_audio_file(file, file_out, args)
    
                if exit_code == 0:
                    print('>>> Converted file [{}]\n               to: [{}]'.format(file_in,file_out))

                    # Final file streams
                    get_file_info(file_out, args)
                    if exit_code != 0:
                        print('!!! ERROR: Reading File [{}] (exit code {})'.format(file_out, exit_code))

                    if args.delete:
                        if delete_file(file):
                            print('>>> Deleted input file [{}]'.format(file))
                        else:
                            print('!!! ERROR: Deleting file [{}]'.format(file))

                    # Check if tagging applies and was requested
                    if video[args.container] and args.tag:
                        # Tag Video
                        file_list = []
                        file_list.append(file_out)
                        vidtag.set_file_tag(file_list) 
                
                else:
                    print('!!! ERROR: Processing File [{}] (exit code {})'.format(file, exit_code))
                    delete_file(file_out)
                    if exit_code == 9999:
                        print('')
                        sys.exit ('*** Stopped ***')

        else:
            print('!!! ERROR: File [{}] not exists or is not readable'.format(file))

    sep()

else:
    # Info
    print('>>> Joining input file to: {}'.format(args.join_to))

    join_input_files(args.files, args.join_to, args)

    if args.delete:
        for file in args.files:
            if delete_file(file):
                print('... Deleted input file [{}]'.format(file)) 
            else: 
                print('!!! ERROR: Deleting file [{}]'.format(file))

