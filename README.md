conv_to.py:

    usage: conv_to [-h] [-v] [-d] [-e] [-i] [-na] [-ns] [-fl] [-f #FPS]
                   [-j <JOINED_FILE>] [-c <mp4|avi|mkv|m4a|mp3|ogg>]
                   [-r <input|std|VCD|DVD|HD|FHD|UHD|DCI>]
                   <FILE> [<FILE> ...]

    v2.6: Wrapper to ffmpeg video manipulation utility. Default: MP4 (input
    resolution)

    positional arguments:
      <FILE>                file/s to process

    optional arguments:
      -h, --help            show this help message and exit
      -v, --verbose         show extra log information
      -d, --delete          delete/remove original input file/s
      -e, --force           force re-encoding of input files
      -i, --info            show file information
      -na, --no_audio       do not include audio
      -ns, --no_subs        do not include subtitles
      -fl, --flip           flip video (rotate vodeo 180º)
      -f #FPS, --fps #FPS   output FPS value
      -j <JOINED_FILE>, --join_to <JOINED_FILE>
                            Joined output file (same codec expected in input
                            files)
      -c <mp4|avi|mkv|m4a|mp3|ogg>, --container <mp4|avi|mkv|m4a|mp3|ogg>
                            output container/codec file format (not used in join
                            operations
      -r <input|std|VCD|DVD|HD|FHD|UHD|DCI>, --resol <input|std|VCD|DVD|HD|FHD|UHD|DCI>
                            standard resolution to use (not used in join
                            operations). input=same as input, std=max width 542px,
                            VCD=max width 352px, DVD=max width 720px, HD=max width
                            1280px, FHD=max width 1920px, UHD=max width 3840px,
                            DCI=max width 4096px

    * Note: When converting subtitles to an AVI container, the original subtitles streams
      (text based) will be extracted to SRT files aside from the resulting AVI file

Examples:

    * Converting video:
        $ conv_to.py -c avi video.flv
        $ conv_to.py -d video1.mkv video2.avi video3.mpg
        $ cont_to.py -ns -na video.avi
        $ conv_to.py -v -r VCD -c mkv v1.mpg v2.mpg

    * Converting and setting FPS:
        $ conv_to.py --fps 25 video.avi

    * Converting and rotating 180º:
        $ conv_to.py --flip video.mkv

    * Extracting audio from video files:
        $ conv_to.py -c mp3 Video.m4v
        $ conv_to.py -c m4a Video.avi
        $ cont_to.py -c ogg Video.mp4

    * Getting file information:
        $ conv_to.py -v -i file.mp3
        $ conv_to.py -i video1.mpg video2.avi video3.mkv

    * Converting audio:
        $ conv_to.py -c mp3 audio1.ogg audio2.m4a
        $ conv_to.py -c m4a audio3.ogg audio4.mp3
        $ conv_to.py -d -c ogg audio1.mp3 audio2.m4a

    * Joining different files together:
        $ conv_to.py -j out.avi in1.avi in2.avi in3.avi
        $ conv_to.py -j out.mp3 in1.mp3 in2.mp3

