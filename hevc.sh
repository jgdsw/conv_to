find . -type f -name '*avi' -print0 | xargs -0 conv_to.py -d -t
find . -type f -name '*mkv' -print0 | xargs -0 conv_to.py -d -t
find . -type f -name '*m4v' -print0 | xargs -0 conv_to.py -d -t
find . -type f -name '*mpg' -print0 | xargs -0 conv_to.py -d -t
find . -type f -name '*mov' -print0 | xargs -0 conv_to.py -d -t
find . -type f -name '*flv' -print0 | xargs -0 conv_to.py -d -t
find . -type f -name '*rmvb' -print0 | xargs -0 conv_to.py -d -t 
find . -type f -name '*h264*' -print0 | xargs -0 conv_to.py -d -t