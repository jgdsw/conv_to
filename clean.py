#!/usr/bin/env python3

import sys
import cmdscript as c

dirs = ['__pycache__', 'build', 'dist']
spec = 'VCT.spec'
artifacts = {
    'MACOSX':  'VCT*.dmg',
    'LINUX':   'VCT*.tar.gz',
    'WINDOWS': 'VCT*.zip'
}

#-------------------------------------------------------------------------------

def run (clean_artifacts=True):
    platform = c.OS()

    if platform != 'MACOSX':
    	status = c.rm_file(spec)
    	print('* Clean [{}] --> ({})'.format(spec, status))

    if clean_artifacts:
        status = c.rm_file_spec(artifacts[platform])
        print('* Clean [{}] --> ({})'.format(artifacts[platform], status))

    for d in dirs:
        status = c.rm_dirtree(d)
        print('* Clean [{}] --> ({})'.format(d, status))
     
#-------------------------------------------------------------------------------

if __name__ == "__main__":
    try:
        run()
    except Exception as exc:
        print(exc)
        print('*** Exception cleaning !!!')
            
    sys.exit(0)
