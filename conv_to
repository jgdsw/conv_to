####################################################################
#
# conv_to:
#
# Script for interfacing ffmpeg/ffprobe tools for audio and video
# format conversion
#
# v.1.13: Force metadata preservation when converting audio files
# v.1.12: If no bitrate is found, then stream is copied
# v-1.11: Option to force resultant FPS
# v-1.10: Small presentation changes
# v-1.9: Forced re-encoding
# v-1.8: Bug fix
# v-1.7: Intelligent re-encoding on selected max width
# v-1.6: Some info added to the no reencoding message
# v-1.5: Fixed AVI quality parameters
# v-1.4: Preserve album artwork where coverting to mp3
# v-1.3: Added the join multimedia files feature
#        Force pixel format for MP4 (yuv420p)
#        Round height to be complaint with MP$ restrictions
# v-1.2: Added ffmpeg exit code management 
# v-1.1: Changed audio default bit rate to 48000Hz
#        Changed default log level to "error"  
# v-1.0: Initial version
#
####################################################################

CONV_TO_VERSION="1.13"

# Defaults
IF_INFO=0
OV_CODEC=h264
OA_CODEC=aac
OV_RESIZE=
OV_MAX_WIDTH="Input"
OV_SCALE=
OV_MP4_Q=18
OV_AVI_BR=
OV_AVI_STR_BR=
OV_AVI_TUNNING="-g 300 -bf 2"
OV_MP4_TUNNING="-preset medium"
OV_ENCODER=libx264
OA_ENCODER=libvo_aacenc
OA_BR="-b:a 160k"
OA_R=48000
OA_ART="-vn"
OS_ENCODER=mov_text
OF_EXT=mp4
OG_FLAGS="-hide_banner -stats -y"
OG_INFO="-v error"
OG_FPS=""
EXE=
EXIT_CODE=0
JOIN_F_OUT=""
JOIN_F_IN=""
FORCE_REENCODING=0
FORCE_DELETE=0

################################################################################
# usage
################################################################################
usage ()
{
    echo ""
    echo "Usage:"
    echo "    $ conv_to [-i <0|1>] [-d <0|1>] [-e <0|1>] [-f <#99>] [-j <output_file>]"
    echo "              [-c <mp4|avi|mp3|m4a>] [-r <VCD|std|DVD|HD|FHD>] <file1 file2 ... fileN>"
    echo ""
    echo "    Version: $CONV_TO_VERSION"
    echo ""
    echo "    Default parameters:"
    echo "        -i 0 -d 0 -e 0 -c mp4 "
    echo "        Convert to MP4 (h264/aac-ac3) / No scaling, no extra info, no forced encoding, no deletion"
    echo ""
    echo "    -i <0|1> :"
    echo "        * Info log level:"
    echo "          0: Normal info log"
    echo "          1: Extra info log"
    echo ""
    echo "    -d <0|1> :"
    echo "        * Delete original input files:"
    echo "          0: No"
    echo "          1: Yes"
    echo ""
    echo "    -e <0|1> :"
    echo "        * Force re-encoding:"
    echo "          0: No"
    echo "          1: Yes"
    echo ""
    echo "    -f <#99> :"
    echo "        * Force the output FPS to the given value."
    echo ""
    echo "    -j <output_file> :"
    echo "        * Join all multimedia files and generate the specified output file."  
    echo "        * Same codec format expected in all files"
    echo ""
    echo "    -c <mp4|avi|mp3|m4a> :"
    echo "        * Select output container file format." 
    echo "        * Not used in join operations."
    echo ""
    echo "    -r <VCD|std|DVD|HD|FHD> :"
    echo "        * Resolutions (not used in join operations):"    
    echo "          std: Max. width limited to 542px"
    echo "          VCD: Max. width limited to 352px"
    echo "          DVD: Max. width limited to 720px"
    echo "          HD:  Max. width limited to 1280px"
    echo "          FHD: Max. width limited to 1920px (BlueRay)"
    echo ""
    echo "    Examples:"
    echo "        * Converting to MP4 or AVI (video):"
    echo "            $ conv_to -c avi video.flv"
    echo "            $ conv_to video.mkv"
    echo "            $ conv_to -i 1 -r VCD v1.mpg v2.mpg"
    echo "        * Extracting audio from video files:"
    echo "            $ conv_to -c mp3 Video.m4v"
    echo "            $ conv_to -c m4a Video.avi"
    echo "        * Converting to MP3 or M4A (audio):"
    echo "            $ conv_to -c mp3 audio1.ogg audio2.m4a"
    echo "            $ conv_to -c m4a audio3.ogg audio4.mp3"
    echo "        * Joining different files together:"
    echo "            $ conv_to -j out.avi in1.avi in2.avi in3.avi"
    echo "            $ conv_to -j out.mp3 in1.mp3 in2.mp3"
    exit 1
}

################################################################################
# conv_audio_file
# 
# The original audio stream always get re-encoded to assure
# compatibility
################################################################################
conv_audio_file ()
{
    EXIT_CODE=0
    if [ $IF_INFO == 1 ]
    then 
        set -x
    fi
    ffmpeg$EXE $OG_FLAGS $OG_INFO -i "$F_IN" -map_metadata 0 $OA_ART -ac 2 -c:a $OA_ENCODER $OA_BR -r:a $OA_R -c:v copy "$F_OUT"
    status=$?
    set +x
    EXIT_CODE=$status
    echo "# ffmpeg exit code [$EXIT_CODE] "

    if [ $EXIT_CODE == 0 ]
    then
        if [ $FORCE_DELETE == 1 ]
        then
           echo "# Removing [$F_IN]..."
           rm -rf "$F_IN"
           echo "# Removed"
        fi
    fi
}

################################################################################
# join_files
################################################################################
join_files ()
{
    EXIT_CODE=0
    if [ $IF_INFO == 1 ]
    then
        set -x
    fi    
    ffmpeg$EXE $OG_FLAGS $OG_INFO -f concat -i $JOIN_F_IN -c copy "$JOIN_F_OUT"
    status=$?
    set +x
    EXIT_CODE=$status
    echo "# ffmpeg exit code [$EXIT_CODE] "
}

################################################################################
# conv_video_file  
################################################################################
conv_video_file ()
{
    # Video

    #set -x        
    STREAMS=$(ffprobe$EXE -v quiet -print_format csv -show_streams -select_streams v -show_entries stream=index,codec_name,width,height,bit_rate -i "$F_IN" | tr '[ ]' '_' | tr '[,]' ' ')
    #set +x
    #echo "-->$STREAMS"

    OV_STREAMS=""
    OV_HEADER=0
    while read -r tag IV_IDX IV_CODEC IV_W IV_H IV_BR dummy 
    do
        #set -x
        if [ "$IV_IDX" != "" ]
        then
            if [ "$IV_BR" != "N/A" ]
            then
                OV_RECODE=""
                OV_ENCODING=""
    
                if [ "$OV_AVI_BR" == "" ]; then
                    OV_AVI_STR_BR="$IV_BR"
                else
                    OV_AVI_STR_BR="$OV_AVI_BR"
                fi
        
                if [ "$IV_CODEC" == "xvid" ]; then
                    IV_CODEC=mpeg4
                fi
    
                if [ $FORCE_REENCODING == 1 ]; then
                   IV_CODEC="$IV_CODEC:Force-ReEnc"
                fi
    
                # Smart resize detection
                if [ -n "$OV_RESIZE" ]; then
                    if [ $IV_W -gt $OV_MAX_WIDTH ]; then
                        OV_STREAMS="$OV_STREAMS -vf scale=${OV_SCALE}"
                        OV_RECODE="$OV_RESIZE"
                    else
                        OV_RECODE=""
                    fi
                fi
        
                if [ $OV_HEADER == 0 ]; then
                    case "${OV_CODEC}" in
                        h264)
                            OV_STREAMS="$OV_STREAMS -f mp4 -movflags faststart -pix_fmt yuv420p"
                            OV_ENCODING="$OV_CODEC -crf $OV_MP4_Q $OV_MP4_TUNNING"
                        ;;
                        mpeg4)
                            OV_STREAMS="$OV_STREAMS -f avi -vtag xvid"
                            # v1.4: OV_ENCODING="$OV_CODEC -b:v:$IV_IDX $OV_AVI_STR_BR $OV_AVI_TUNNING"
                            OV_ENCODING="$OV_CODEC -q:v 0 $OV_AVI_TUNNING"
                        ;;
                    esac
                    OV_HEADER=1
                fi 
            
                OV_VIDEO_REQS="${OV_CODEC}${OV_RECODE}"                                             
                if  [ "$IV_CODEC" == "$OV_VIDEO_REQS" ]
                then
                    # Copy stream
                    echo "# V.Stream [${IV_IDX}]: No re-encoding needed! ${IV_W}x${IV_H}, $IV_BR bitrate ([${IV_CODEC}] -> [${OV_CODEC}, Max.W=$OV_MAX_WIDTH])"
                    OV_STREAMS="$OV_STREAMS -map 0:$IV_IDX -c:v:$IV_IDX copy"
                else
                    # Re-encode stream
                    echo "# V.Stream [${IV_IDX}]: Re-encoding needed: ${IV_W}x${IV_H}, $IV_BR bitrate ([$IV_CODEC] -> [${OV_CODEC}, Max.W=$OV_MAX_WIDTH])"
                    OV_STREAMS="$OV_PREFFIX $OV_STREAMS -map 0:$IV_IDX -c:v:${IV_IDX} ${OV_ENCODING}"
                fi
            else
                echo "# V.Stream [${IV_IDX}]: No Valid Bitrate Found! ${IV_W}x${IV_H}, $IV_BR bitrate ([${IV_CODEC}]) -> Copying..."
                OV_STREAMS="$OV_STREAMS -map 0:$IV_IDX -c:v:$IV_IDX copy"
            fi
        fi
        #set +x
    done <<< "$STREAMS"

    # Audio
    STREAMS=$(ffprobe$EXE -v quiet -print_format csv -show_streams -select_streams a -show_entries stream=index,codec_name -i "$F_IN" | tr '[ ]' '_' | tr '[,]' ' ')
    #echo "-->$STREAMS"

    OA_STREAMS=""
    while read -r tag IA_IDX IA_CODEC dummy
    do
        if [ "$IA_IDX" != "" ]
        then
            # Ugly patch for deeling with AC3 / AAC audio stream copy in MP4 files
            if [ "$IA_CODEC" == "ac3" ]; then
                IA_CODEC=aac
                if [ "$OA_CODEC" == "aac" ]; then
                    OA_STREAMS="$OA_STREAMS -c:a copy"
                fi
            fi
            if [ "$IA_CODEC" == "aac" ]; then
                if [ "$OA_CODEC" == "aac" ]; then
                    OA_STREAMS="$OA_STREAMS -c:a copy"
                fi
            fi

            if [ $FORCE_REENCODING == 1 ]; then
               IA_CODEC="$IA_CODEC:Force-ReEnc"
            fi
    
            if  [ "$IA_CODEC" == "$OA_CODEC" ]
            then
                # Copy stream
                echo "# A.Stream [${IA_IDX}]: No re-encoding needed! ([${IA_CODEC}] -> [${OA_CODEC}])"
                OA_STREAMS="$OA_STREAMS -map 0:$IA_IDX -c:a:${IA_IDX} copy"
            else
                # Re-encode stream
                echo "# A.Stream [${IA_IDX}]: Re-encoding needed: [$IA_CODEC] -> [$OA_CODEC]"
                OA_STREAMS="$OA_STREAMS -map 0:$IA_IDX -c:a:${IA_IDX} $OA_ENCODER $OA_BR -r:a $OA_R -ac 2"
            fi      
        fi
    done <<< "$STREAMS"

    # Subtitles
    STREAMS=$(ffprobe$EXE -v quiet -print_format csv -show_streams -select_streams s -show_entries stream=index,codec_name -i "$F_IN" | tr '[ ]' '_' | tr '[,]' ' ')
    #echo "-->$STREAMS"

    OS_STREAMS=""
    while read -r tag IS_IDX IS_CODEC dummy
    do
        if [ "$IS_IDX" != "" ]
        then
            if  [ "$OV_CODEC" == "h264" ]
            then
                echo "# S.Stream [${IS_IDX}]: Forcing Re-encoding: [$IS_CODEC] -> [mov_text]"
                OS_STREAMS="$OS_STREAMS -map 0:$IS_IDX"
            else
                echo "# S.Stream [${IS_IDX}]: Skipping [$IS_CODEC] subtitles for the AVI container"
            fi
        fi
    done <<< "$STREAMS"

    case "${OV_CODEC}" in
        h264)
            OS_STREAMS="$OS_STREAMS -c:s mov_text"
            ;;
        mpeg4)
            OS_STREAMS="-sn"
            ;;
    esac

    EXIT_CODE=0
    if [ $IF_INFO == 1 ]
    then
        set -x
    fi
    ffmpeg$EXE $OG_FLAGS $OG_INFO -i "$F_IN" $OG_FPS $OV_STREAMS $OA_STREAMS $OS_STREAMS "$F_OUT"
    status=$?
    set +x
    EXIT_CODE=$status
    echo "# ffmpeg exit code [$EXIT_CODE] "

    if [ $EXIT_CODE == 0 ]
    then
        if [ $FORCE_DELETE == 1 ]
        then
           echo "# Removing [$F_IN]..."
           rm -rf "$F_IN"
           echo "# Removed"
        fi 
    fi
}

################################################################################
# Main thread
################################################################################                                                                                

if [ "$OS" == "Windows_NT" ]; then
    EXE=".exe"
fi

format=default
reso=default
info=0

while getopts ":i:d:j:e:f:c:r:" option; do
    case "${option}" in
        i)
            info=${OPTARG}
            case "${info}" in
                0)
                    IF_INFO=0
                    OG_INFO="-v warning"
                    ;;
                1)
                    IF_INFO=1
                    OG_INFO="-v info"
                    ;;
            esac
            ;;
        d)
            info=${OPTARG}
            case "${info}" in
                0)
                    FORCE_DELETE=0
                    ;;
                1)
                    FORCE_DELETE=1
                    ;;
            esac
            ;;
        j)
            JOIN_F_OUT=${OPTARG}
            ;;
        e)
            info=${OPTARG}
            case "${info}" in
                0)
                    FORCE_REENCODING=0
                    ;;
                1)
                    FORCE_REENCODING=1
                    ;;
            esac
            ;;
        f)
            FPS=${OPTARG}
            FORCE_REENCODING=1
            OG_FPS="-r ${FPS}"
            ;;
        c)
            format=${OPTARG}
            case "${format}" in
                mp4)
                    OV_CODEC=h264
                    OV_ENCODER=libx264
                    OA_CODEC=ac3
                    OA_ENCODER=ac3
                    OS_ENCODER=mov_text
                    OF_EXT=mp4
                    ;;
                avi)
                    OV_CODEC=mpeg4
                    OV_ENCODER=mpeg4
                    OA_CODEC=mp3
                    OA_ENCODER=libmp3lame
                    OA_BR="-q:a 0"
                    OS_ENCODER=xsub
                    OF_EXT=avi
                    ;;
                mp3)
                    OV_CODEC=
                    OV_ENCODER=
                    OA_CODEC=mp3
                    OA_ENCODER=libmp3lame
                    OA_BR="-q:a 0"
                    OA_ART="-vcodec png"
                    OF_EXT=mp3
                    ;;
                m4a)
                    OV_CODEC=
                    OV_ENCODER=
                    OA_CODEC=aac
                    OA_ENCODER=libvo_aacenc
                    OA_ART="-vn"
                    OF_EXT=m4a
                    ;;
                *)
                    usage
                    ;;
            esac
            ;;
        r)
            reso=${OPTARG}
            case "${reso}" in
                std)
                    OV_RESIZE=":max_width:542"
                    OV_MAX_WIDTH=542
                    OV_SCALE="'if(gt(iw,542),542,iw)':trunc(ow/a/2)*2"
                    OV_AVI_BR=900k
                    OV_MP4_Q=19
                    OV_MP4_TUNNING="-preset medium"
                    ;;
                VCD)
                    OV_RESIZE=":max_width:352"
                    OV_MAX_WIDTH=352
                    OV_SCALE="'if(gt(iw,352),352,iw)':trunc(ow/a/2)*2"
                    OV_AVI_BR=400k
                    OV_MP4_Q=20
                    OV_MP4_TUNNING="-preset medium -tune film"
                    ;;
                DVD)
                    OV_RESIZE=":max_width:720"
                    OV_MAX_WIDTH=720
                    OV_SCALE="'if(gt(iw,720),720,iw)':trunc(ow/a/2)*2"
                    OV_AVI_BR=1800k
                    OV_MP4_Q=18
                    OV_MP4_TUNNING="-preset medium -tune film"
                    ;;
                HD)
                    OV_RESIZE=":max_width:1280"
                    OV_MAX_WIDTH=1280
                    OV_SCALE="'if(gt(iw,1280),1280,iw)':trunc(ow/a/2)*2"
                    OV_AVI_BR=4000k
                    OV_MP4_Q=17
                    OV_MP4_TUNNING="-preset medium -tune film"
                    ;;
                FHD)
                    OV_RESIZE=":max_width:1920"
                    OV_MAX_WIDTH=1920
                    OV_SCALE="'if(gt(iw,1920),1920,iw)':trunc(ow/a/2)*2"
                    OV_AVI_BR=8500k
                    OV_MP4_Q=16
                    OV_MP4_TUNNING="-preset medium -tune film"
                    ;;
                *)
                    usage
                    ;;
            esac
            ;;
        *)
            usage
            ;;
    esac
done
shift $((OPTIND-1))

# Is there any file?
ARG_FILES="${@}"
if [ "$ARG_FILES" == "" ]; then
    usage
fi

# Extra info
if [ $IF_INFO == 1 ]; then
    echo "--------------------------------------------------------------------------------"
    if [ "$JOIN_F_OUT" == "" ]; then
        echo "Convert to Format: ${format}"
        if [ -n "${OV_CODEC}" ]; then
            echo "* [Video:CODEC=${OV_CODEC}/CRF=${OV_MP4_Q}/BitRate=${OV_AVI_BR}/ENCODER=${OV_ENCODER}]"
            echo "* [Resolution: SIZE=${reso}]"
        fi
        echo "* [Audio:CODEC=${OA_CODEC}/ENCODER=${OA_ENCODER}/BR=${OA_BR}]"
    else
        echo "Joining input multimedia file to: $JOIN_F_OUT"
    fi
fi

echo "--------------------------------------------------------------------------------"

if  [ "$JOIN_F_OUT" == "" ]
then
    # Format conversion operation
    for f in "$@";
    do 
        F_IN="${f}"
        F_OUT="${f%.*}.${OF_EXT}"

        # We do not want to overwrite the input file
        if [ "${F_IN}" == "${F_OUT}" ]; then
            F_OUT="${f%.*}.ffmpeg.${OF_EXT}"
        fi
    
        if [ -r "$F_IN" ]
        then
            # File exists
            echo ">>> Converting file [$F_IN] ..."
            echo ""
            
            #if [ $IF_INFO == 1 ]; then
            #    ffprobe -v quiet -pretty -print_format flat -show_streams -show_entries stream -i "$F_IN"
            #    echo "..."
            #fi
    
            if [ -z "${OV_CODEC}" ]; 
            then
                # Convert Audio (MP3/M4A)  
                conv_audio_file
            else
                # Convert Video + Audio (MP4/AVI)
                conv_video_file 
            fi 
        
            echo ""
            if [ $EXIT_CODE == 0 ]; then
                echo ">>> Converted file [$F_IN] to [$F_OUT]"
            else
                echo "!!! File [$F_IN] NOT converted !!!"
                # Just in case
                rm -f "$F_OUT" >/dev/null 2>&1         
            fi    
        else
            # File not exists
            echo "!!! File [$F_IN] not exists or it is not readable !!!"
        fi

        echo ""
        echo "--------------------------------------------------------------------------------"

    done
else
    # Join operation
    DIR=`pwd`
    JOIN_F_IN="ffmpeg.concat.$$"
    for f in "$@"
    do
        JF="${f}"
        printf "file '%s/%s'\n" "$DIR" "$JF" >> $JOIN_F_IN
    done

    echo "# Files sequence:"
    cat "$JOIN_F_IN"
    echo ""

    # Join files
    join_files

    # Remove aux. file
    rm -f $JOIN_F_IN >/dev/null 2>&1

    if [ $EXIT_CODE == 0 ]
    then
        if [ $FORCE_DELETE == 1 ]
        then    
            for f in "$@"
            do
                JF="${f}"
                echo "# Removing [$JF]..."
                rm -rf "$JF"
                echo "# Removed"
            done 
        fi 
    fi  

    echo ""
    if [ $EXIT_CODE == 0 ]; then
        echo ">>> Files joined to [$JOIN_F_OUT]"
    else
        echo "!!! File [$F_IN] NOT converted !!!"
        # Just in case
        rm -f "$JOIN_F_OUT" >/dev/null 2>&1
    fi

    echo "--------------------------------------------------------------------------------"
fi
