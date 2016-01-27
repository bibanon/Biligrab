#!/usr/bin/python3
# Bilibili Archiver
# grabs a bilibili video with comments, then uploads it with all metadata to the Internet Archive.
import os
import json
import sys
import re
import docopt
from internetarchive import get_item

__doc__ = """biliup.py - Download a Bilibili video with comments, then upload to the Internet Archive.
If the video has more than 1 part, you can specify them manually to download.
If the download doesn't work at first, set a different source for BiliDan to use (1 is preferred outside China):
0 - API, 1 - CDN Overseas, 2 - Origin Source , 3 - Exper. HTML5, 4 - Flvcd (for Youku), 5 - BilibiliPr, 6 - You-get

Usage:
  biliup.py <url>
  biliup.py <url> [--source <src>]
  biliup.py <url> [--source <src>] [--part <p>]...
  biliup.py -h | --help

Arguments:
  <url>           The Bilibili URL to download, in this format: http://www.bilibili.com/video/av314/

Options:
  -h --help       Show this screen.
  --source <src>  Video Source to download from [default: 0].
  --part <p>      Video part to download [default: 0]
"""

def mkdirs(path):
	"""Make directory, if it doesn't exist."""
	if not os.path.exists(path):
		os.makedirs(path)

def main():
    # parse arguments from file docstring
    args = docopt.docopt(__doc__)
    
    # obtain vid from argument
    url = args['<url>']
    parse = re.search(r'/video/av(\d+)/', url)  # if URL given
    if parse is not None:
        vid = parse.group(1)
    elif re.search(r'^\d+', url) is not None:    # if vid given
        vid = url
    
    # choose source type
    src = args['--source']
    
    # obtain list of parts to grab
    
    # run biligrab to archive the video, set to source 1 for overseas CDN, and download all parts
    for p in args['--part']:
        os.system('python biligrab.py -a {vid} -s {src} -p {p}'.format(vid = vid, src = src, p = int(p)) )

    # download metadata
    os.system('python3 biligrab_metadata.py %s' % vid)
    
    # define working directory and IA identifier
    ident = 'bilibili-av{vid}'.format(vid = vid)
    workdir = ident
    
    # obtain metadata from JSON
    json_fname = os.path.join(workdir, ident + '.json')
    with open(json_fname) as f:    
        metadata = json.load(f)
    
    # gather comma separated tags and replace delimiter with IA compatible semicolon
    tags = metadata['tag'].split(',')
    tags_string = 'bilibili;video;'
    for tag in tags:
        tags_string += '%s;' % tag
    
    # set up metadata
    item = get_item(ident)
    desc = metadata['description'] + ' <b>Note:</b> <i>Comments are in the included .ass subtitle file.</i>'
    meta = dict(vid = metadata['vid'], cid = metadata['cid'], title = "%s - %s" % (ident, metadata['title']), description = desc, tags = tags_string)
    
    # upload items
    print("Uploading to Internet Archive: http://archive.org/details/%s" % ident)
    for file in os.listdir(workdir):
        fname = os.path.join(workdir, file)
        print("Uploading %s..." % fname)
        item.upload(fname, metadata=meta)

if __name__ == '__main__':
    main()