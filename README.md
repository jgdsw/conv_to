conv_to:

Script for simplifying ffmpeg tasks

Usage:

    $ conv_to [-i <0|1>] [-d <0|1>] [-e <0|1>] [-f <#99>] [-j <output_file>]
              [-c <mp4|avi|mp3|m4a>] [-r <VCD|std|DVD|HD|FHD>] <file1 file2 ... fileN>

    Version: 1.13

    Default parameters:
        -i 0 -d 0 -e 0 -c mp4 
        Convert to MP4 (h264/aac-ac3) / No scaling, no extra info, no forced encoding, no deletion

    -i <0|1> :
        * Info log level:
          0: Normal info log
          1: Extra info log

    -d <0|1> :
        * Delete original input files:
          0: No
          1: Yes

    -e <0|1> :
        * Force re-encoding:
          0: No
          1: Yes

    -f <#99> :
        * Force the output FPS to the given value.

    -j <output_file> :
        * Join all multimedia files and generate the specified output file.
        * Same codec format expected in all files

    -c <mp4|avi|mp3|m4a> :
        * Select output container file format.
        * Not used in join operations.

    -r <VCD|std|DVD|HD|FHD> :
        * Resolutions (not used in join operations):
          std: Max. width limited to 542px
          VCD: Max. width limited to 352px
          DVD: Max. width limited to 720px
          HD:  Max. width limited to 1280px
          FHD: Max. width limited to 1920px (BlueRay)

    Examples:
        * Converting to MP4 or AVI (video):
            $ conv_to -c avi video.flv
            $ conv_to video.mkv
            $ conv_to -i 1 -r VCD v1.mpg v2.mpg
        * Extracting audio from video files:
            $ conv_to -c mp3 Video.m4v
            $ conv_to -c m4a Video.avi
        * Converting to MP3 or M4A (audio):
            $ conv_to -c mp3 audio1.ogg audio2.m4a
            $ conv_to -c m4a audio3.ogg audio4.mp3
        * Joining different files together:
            $ conv_to -j out.avi in1.avi in2.avi in3.avi
            $ conv_to -j out.mp3 in1.mp3 in2.mp3