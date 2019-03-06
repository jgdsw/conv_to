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
import vidtag
from pathlib import Path
import types
from cmdscript import ExtendedTimer
import datetime
import psutil
import cmdscript as c

#-------------------------------------------------------------------------------

def _filter_out (str_list):
    filtered_list = []
    for item in str_list:
        filtered_list.append(item.strip())
    return filtered_list

#-------------------------------------------------------------------------------

def kill_proctree (pid=None, include_parent=False, timeout=5):
    me = os.getpid()

    # Defaults to my pid
    if pid == None:
        pid = me

    # I do not want to kill my self
    if pid == me:
        include_parent = False

    parent = psutil.Process(pid)
    children = parent.children(recursive=True)

    for child in children:
        child.kill()

    gone, still_alive = psutil.wait_procs(children, timeout=timeout)

    if include_parent:
        parent.kill()
        parent.wait(timeout)

#-------------------------------------------------------------------------------

def join_input_files (files, f_out, args):
    global ffmpeg_join, info, exit_code

    c.sep()

    # Create temporary file
    tmppath = '.conv_to.join.{}'.format(os.getpid())

    # Remove temporary file
    if c.rm_file(tmppath):
        print('# Temp file:{} removed'.format(f_out))

    # Writing temporary file stream
    tmp = open(tmppath, 'w')
    for f in files:
        print('file \'{}\''.format(f), file=tmp)      
        print('# Registering file [{}]:'.format(f))
        show_file_size(f)
        show_file_duration(f, args)
        c.sep()
    tmp.close()   

    #exec_command ('cat {}'.format(tmppath), get_stdout=True, verbose=True)

    # Remove out file
    if c.rm_file(f_out):
        print('# Output file:{} removed'.format(f_out))
    else:
        print('# Output file:{} do not exist (will be created)'.format(f_out))

    c.sep()

    # ffmpeg progress
    #FFMPEG_PROGRESS = 0.0
    #FFMPEG_DURATION = '00:00:00.000'
    #FFMPEG_SIZE = 0.0

    #T = ExtendedTimer(5, 0, False, timerShowOutputFileSize, f_out)
    #T.start()

    try:
        # Command to join
        join_command = ffmpeg_join.format(args.bin, info[args.verbose], tmppath, f_out)
        st, out, err = c.exec(join_command, verbose=args.verbose)
        exit_code = st
        if exit_code != 0:
            print('!!! ERROR: Excuting command [{}] (exit code {})'.format(join_command, exit_code))
    finally:
        #T.cancel()
        #del T
        pass

    # Remove temporary file
    if not c.rm_file(tmppath):
        print('\n!!! ERROR: Removing temporary file:{}'.format(tmppath))

    c.sep()

    # File Joined
    print('>>> Input files joined to: [{}]'.format(f_out))

    get_file_info(f_out, args)

    c.sep()

#-------------------------------------------------------------------------------

def ToInt (value):
    try:
        ival=int(value)
        return ival
    except:
        return -1

#-------------------------------------------------------------------------------

def ToFloat (value):
    try:
        ival=float(value)
        return ival
    except:
        return 0.0

#-------------------------------------------------------------------------------

def get_video_streams (file, options, args, info=False):
    global ffprobe_video, video_resolution, video_container, stream_video_quality, \
           OV_stream, O_copy, rotate180, video_filters

    ffprobe_args = ffprobe_video.format(args.bin, file)
    st, out, err = c.exec(ffprobe_args, get_stdout=True, verbose=args.verbose)

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
        ffprobe_args = ffprobe_audio.format(args.bin, file)
        st, out, err = c.exec(ffprobe_args, get_stdout=True, verbose=args.verbose)

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
    global subtitles, ffprobe_subs, O_copy, OS_stream, not_OS_stream

    if args.no_subs and not info:
        # Do not copy audio streams
        options.append(subtitles['none'])
        print('# Subtitle[X]: Do not process subtitles streams')
        st = 0

    else:
        # Get audio streams info
        ffprobe_args = ffprobe_subs.format(args.bin, file)
        st, out, err = c.exec(ffprobe_args, get_stdout=True, verbose=args.verbose)

        if st == 0:

            subs=False

            for line in out:

                ignored=False

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

                        # Process Stream
                        stream = not_OS_stream.format(index)
                        options.append(stream)
                        ignored=True

                if subs:
                    # Codec for subtitles streams (MP4)
                    options.append(OS_codec.format(subtitles[args.container]))
                else:
                    if not ignored:
                        # No subtitles inside XVID file
                        options.append(subtitles['none'])

    return st

#-------------------------------------------------------------------------------

def timerShowOutputFileSize (file_out):
    global FFMPEG_PROGRESS, FFMPEG_DURATION, FFMPEG_SIZE

    #date = datetime.datetime.now().strftime("%Y-%m-%d.%H:%M:%S.%f")
    #size = show_file_size(file_out, verbose=False)

    if FFMPEG_SIZE != 0.0:
        print ('# [{}]: Time={}, Progress={:6.2f}%, Size={:.2f}MB'.format(os.path.basename(file_out), FFMPEG_DURATION, FFMPEG_PROGRESS, FFMPEG_SIZE))
    else:
        print ('# [{}]: Time={}, Progress={:6.2f}%'.format(os.path.basename(file_out), FFMPEG_DURATION, FFMPEG_PROGRESS))

#-------------------------------------------------------------------------------

def show_file_size (file, verbose=True):
    f = Path(file)
    try:
        ver2=sys.version_info[1]
        if ver2 >= 6:
            # python 3.6+
            s = os.path.getsize(f)
        else:
            # python pre 3.6
            s = os.path.getsize(file)
        size = ((s/1024)/1024)
    except OSError:
        size = 0
    if verbose:
        print('# Size: {:.2f} MB'.format(size))
    return size

#-------------------------------------------------------------------------------

def show_file_duration (file, args, verbose=True):
    comm = ffprobe_dur.format(args.bin, file)
    st, out, err = c.exec(comm, get_stdout=True, verbose=args.verbose)

    try:
        auxi = out[0]
        auxi = auxi.split(':')
        seconds = (ToFloat(auxi[0])*3600.0) + (ToFloat(auxi[1])*60) + (ToFloat(auxi[2]))
    except:
        seconds = 0.0

    if verbose:
        print ('# Duration: {} ({} seconds)'.format(out, seconds))

    return (seconds)

#-------------------------------------------------------------------------------

# Sample ffmpeg output:
# frame= 9332 fps=1333 q=-1.0 size=   41472kB time=00:06:13.16 bitrate= 910.4kbits/s speed=53.3x
# frame= 9965 fps=1328 q=-1.0 size=   42752kB time=00:06:38.48 bitrate= 878.9kbits/s speed=53.1x
# size=   13056kB time=00:11:04.87 bitrate= 160.9kbits/s speed=53.2x
# size=   13568kB time=00:11:32.69 bitrate= 160.5kbits/s speed=53.3x

def ffmpegProgress (line, seconds=0, filter_line=False, verbose=False):
    global FFMPEG_PROGRESS, FFMPEG_DURATION, FFMPEG_SIZE

    if not filter_line:
        print(line)

    proc_line = line.replace('=',' ')
    proc_line = proc_line.replace('kB','')
    proc_line = proc_line.split()

    i=0
    size=0
    time=0
    for elem in proc_line:
        if elem == "time":
            time = i+1;
        if elem == "size":
            size = i+1
        i+=1

    if size!=0:
        v_size=proc_line[size]
    else:
        v_size = '0.0'
    size_mb = ToFloat(v_size)/1024

    if time!=0:
        v_time=proc_line[time]
    else:
        v_time = '00:00:00.000'
    vt = v_time.split(':')
    time_secs = (ToFloat(vt[0])*3600.0) + (ToFloat(vt[1])*60.0) + (ToFloat(vt[2]))

    if verbose:
        print(time_secs, seconds)

    perc = (time_secs/seconds)*100.0
    if perc > 100.0:
        perc = 100.0

    if perc != 0.0:
        FFMPEG_PROGRESS = perc
    if v_time != '00:00:00.000':
        FFMPEG_DURATION = v_time
    if size_mb != 0.0:
        FFMPEG_SIZE = size_mb

    if verbose:
        if size_mb == 0.0:
            print ('{:6.2f}% time={}'.format(perc, v_time))        
        else:
            print ('{:6.2f}% time={} size={:.2f} MB'.format(perc, v_time, size_mb))

    if USER_EXIT_PROGRESS!=None and USER_EXIT_FILE_ID!=None and USER_EXIT_SENDER!=None:
        USER_EXIT_PROGRESS(USER_EXIT_SENDER, USER_EXIT_FILE_ID, perc)

#-------------------------------------------------------------------------------

def convert_video_file (file, file_out, args):
    global exit_code, info, video_container, video_resolution, FPS, FFMPEG_PROGRESS, FFMPEG_DURATION, FFMPEG_SIZE

    options = []

    if args.fps != 0.0:
        options.append(FPS.format(args.fps))

    st_v = st_a = st_s = 255

    print ('# Converting to Video file')

    show_file_size(file)
    seconds = show_file_duration(file, args)

    st_v = get_video_streams(file, options, args)
    if st_v == 0:
        st_a = get_audio_streams(file, options, args)
    if st_a == 0:
        st_s = get_subs_streams(file, options, args)

    if st_v == 0 and st_a == 0 and st_s == 0:

        # ffmpeg progress
        FFMPEG_PROGRESS = 0.0
        FFMPEG_DURATION = '00:00:00.000'
        FFMPEG_SIZE = 0.0

        # Correct stream data
        # Building FFMPEG command
        options_string = ''
        for opt in options:
            options_string = options_string + opt + ' '
        options_string = options_string.strip()

        T = ExtendedTimer(5, 0, False, timerShowOutputFileSize, file_out)
        T.start()

        # Final command
        try:
            comm = ffmpeg_comm.format(args.bin, info[args.verbose], file, options_string, file_out)
            st, out, err = c.exec(comm, verbose=args.verbose, user_function=ffmpegProgress, seconds=seconds)
            exit_code = st
            if exit_code != 0:
                print('!!! ERROR: Excuting command [{}] (exit code {})'.format(comm, exit_code)) 
        finally:
            T.cancel()
            del T

    else:
        # Error obtaining streams data
        exit_code = 255

#-------------------------------------------------------------------------------

def get_file_info (file, args):
    global exit_code

    options = []

    st_v = st_a = st_s = 255

    show_file_size(file)
    show_file_duration(file, args)

    st_v = get_video_streams(file, options, args, info=True)
    st_a = get_audio_streams(file, options, args, info=True)
    st_s = get_subs_streams(file, options, args, info=True)

    if st_v != 0 or st_a != 0 or st_s != 0:
        # Error obtaining streams data
        exit_code = 255

    comm = ffprobe_info.format(args.bin, file)
    c.exec(comm, verbose=args.verbose)

#-------------------------------------------------------------------------------

def convert_audio_file (file, file_out, args):
    global audio_container, info, exit_code, FFMPEG_PROGRESS, FFMPEG_DURATION, FFMPEG_SIZE

    # ffmpeg progress
    FFMPEG_PROGRESS = 0.0
    FFMPEG_DURATION = '00:00:00.000'
    FFMPEG_SIZE = 0.0

    print ('# Converting to Audio file')

    show_file_size(file)
    seconds = show_file_duration(file, args)

    T = ExtendedTimer(5, 0, False, timerShowOutputFileSize, file_out)
    T.start()

    try:
        audio_command = audio_container[args.container].format(args.bin, info[args.verbose], file, file_out)
        st, out, err = c.exec(audio_command, get_stdout=False, verbose=args.verbose, user_function=ffmpegProgress, seconds=seconds)
        exit_code = st
        if exit_code != 0:
            print('!!! ERROR: Excuting command [{}] (exit code {})'.format(audio_command, exit_code))
    finally:
        T.cancel()
        del T

#-------------------------------------------------------------------------------

def IsVideo (container):
    try:
        return (video[container])
    except:
        return (False)

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
'mp3': '{}ffmpeg -stats -hide_banner -y {} -i "{}" -map_metadata 0 -vcodec png -ac 2 -c:a libmp3lame -b:a 160k -r:a 48000 "{}"',
'm4a': '{}ffmpeg -stats -hide_banner -y {} -i "{}" -map_metadata 0 -vn -ac 2 -c:a aac -b:a 160k -r:a 48000 "{}"',
'ogg': '{}ffmpeg -stats -hide_banner -y {} -i "{}" -map_metadata 0 -vn -ac 2 -c:a libvorbis -b:a 160k -r:a 48000 "{}"'
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
not_OS_stream = '-map -0:{}'
OS_codec = '-c:s {}'
OS_SRT_extraction = 'ffmpeg -stats -hide_banner -y -v error -i "{}" -map 0:{} "{}"'

# FFMPEG commands
ffmpeg_comm = '{}ffmpeg -nostdin -stats -hide_banner -y {} -i "{}" {} -max_muxing_queue_size 1024 "{}"'
ffmpeg_join = '{}ffmpeg -nostdin -safe 0 -stats -hide_banner -y {} -f concat -i "{}" -c copy -max_muxing_queue_size 1024 "{}"'

ffprobe_video = '{}ffprobe -v error -print_format csv -show_streams -select_streams v -show_entries stream=index,codec_name,width,height,bit_rate -i "{}"'
ffprobe_audio = '{}ffprobe -v error -print_format csv -show_streams -select_streams a -show_entries stream=index,codec_name:stream_tags=language -i "{}"'
ffprobe_subs  = '{}ffprobe -v error -print_format csv -show_streams -select_streams s -show_entries stream=index,codec_name:stream_tags=language -i "{}"'
ffprobe_dur   = '{}ffprobe -i "{}" -show_entries format=duration -v error -of csv="p=0" -sexagesimal'
ffprobe_info  = '{}ffprobe -hide_banner -i "{}"'

# Exit status
exit_code = 0

# ffmpeg progress
FFMPEG_PROGRESS = 0.0
FFMPEG_DURATION = '00:00:00.000'
FFMPEG_SIZE = 0.0

USER_EXIT_SENDER = None
USER_EXIT_PROGRESS = None
USER_EXIT_FILE_ID = None

#-------------------------------------------------------------------------------

def run(args, user_exit=None, file_id=None, sender=None):
    global exit_code, USER_EXIT_PROGRESS, USER_EXIT_FILE_ID, USER_EXIT_SENDER

    USER_EXIT_PROGRESS = user_exit
    USER_EXIT_FILE_ID = file_id
    USER_EXIT_SENDER = sender

    out_files = {}
    exit_code = 0

    if len(args.join_to)==0:
        # Info
        if args.info:
            print('*** Show file information:')
        else:
            print('*** Convert to: [{}]'.format(args.container))
            if args.verbose:
                print('*** [Resolution={}, FPS={}, Force_encode={}]'.format(args.resol, args.fps, args.force))
            print('*** [Delete Input Files={}]'.format(args.delete))

        # File wilcards expansion
        # Windows support !!
        files_expanded=[]
        for f in args.files:
            flist = c.get_files(f, verbose=args.verbose)
            files_expanded = files_expanded + flist

        for file in files_expanded:

            c.sep()

            # Test file existence
            if os.path.isfile(file) and os.access(file, os.R_OK):

                # Output filename
                f_path = Path(file)
                file_in = str(f_path)
                file_wext = f_path.with_suffix('')
                file_out = '{}.{}'.format(file_wext, args.container)
                if file_out == file_in:
                    file_out = '{}.ffmpeg.{}'.format(file_wext, args.container)

                # IN/OUT files
                out_files[file]=file_out

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

                        # Delete only if verification is sucessfull!
                        if args.delete and exit_code == 0:
                            if c.rm_file(file):
                                print('>>> Deleted input file [{}]'.format(file))
                            else:
                                print('!!! ERROR: Deleting file [{}]'.format(file))

                        # Check if tagging applies and was requested
                        if video[args.container] and args.tag and exit_code == 0:
                            # Tag Video
                            file_list = []
                            file_list.append(file_out)
                            tag_out = vidtag.set_file_tag(file_list, main=False, bins=args.bin)
                            # IN/OUT files
                            if tag_out[file_out] != '':
                                out_files[file] = tag_out[file_out]

                    else:
                        print('!!! ERROR: Processing File [{}] (exit code {})'.format(file, exit_code))
                        c.rm_file(file_out)
                        if exit_code == 9999:
                            print('')
                            sys.exit ('*** Stopped ***')

            else:
                print('!!! ERROR: File [{}] not exists or is not readable'.format(file))
                exit_code = 255

        c.sep()

    else:
        # Info
        print('>>> Joining input file to: {}'.format(args.join_to))

        join_input_files(args.files, args.join_to, args)

        for file in args.files:
            out_files[file] = args.join_to

        if args.delete:
            for file in args.files:
                if c.rm_file(file):
                    print('>>> Deleted input file [{}]'.format(file))
                else:
                    print('!!! ERROR: Deleting file [{}]'.format(file))

    return exit_code, out_files

#-------------------------------------------------------------------------------

if __name__ == "__main__":

    # Get command line
    parser = argparse.ArgumentParser(prog='conv_to', description='v3.3: Wrapper to ffmpeg video manipulation utility. Default: MP4 (input resolution)')
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

    # Create argument object
    arguments = types.SimpleNamespace()
    arguments.verbose = args.verbose
    arguments.delete = args.delete
    arguments.force = args.force
    arguments.info = args.info
    arguments.no_audio = args.no_audio
    arguments.no_subs = args.no_subs
    arguments.flip = args.flip
    arguments.tag = args.tag
    arguments.fps = args.fps
    arguments.join_to = args.join_to
    arguments.container = args.container
    arguments.resol = args.resol
    arguments.files = args.files
    # conv_to command line tool assumes ffmpeg artifacts available in PATH
    arguments.bin = ''

    run(arguments)
