#!/bin/bash
# Grabs the metadata for a video from Bilibili.
# borrowed from bilidan.py: https://github.com/m13253/BiliDan/
# Developed by Antonizoon for the Bibliotheca Anonoma.

import sys
import json
import logging
import hashlib
import gzip
import urllib.parse
import urllib.request

# api keys    
USER_AGENT_API = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:6.0.2) Gecko/20100101 Firefox/6.0.2 Fengfan/1.0'
USER_AGENT_PLAYER = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:6.0.2) Gecko/20100101 Firefox/6.0.2 Fengfan/1.0'
APPKEY = '85eb6835b0a1034e'  # The same key as in original Biligrab
APPSEC = '2ad42749773c441109bdc0191257a664'  # Do not abuse please

def bilibili_hash(args):
    '''Calculate API signature hash

    Arguments: {request_paramter: value}

    Return value: hash_value -> str
    '''
    return hashlib.md5((urllib.parse.urlencode(sorted(args.items()))+APPSEC).encode('utf-8')).hexdigest()  # Fuck you bishi

def fetch_url(url, *, user_agent=USER_AGENT_PLAYER, cookie=None, fakeip=None):
    '''Fetch HTTP URL

    Arguments: url, user_agent, cookie

    Return value: (response_object, response_data) -> (http.client.HTTPResponse, bytes)
    '''
    logging.debug('Fetch: %s' % url)
    req_headers = {'User-Agent': user_agent, 'Accept-Encoding': 'gzip, deflate'}
    if cookie:
        req_headers['Cookie'] = cookie
    if fakeip:
        req_headers['X-Forwarded-For'] = fakeip
        req_headers['Client-IP'] = fakeip
    req = urllib.request.Request(url=url, headers=req_headers)
    response = urllib.request.urlopen(req, timeout=120)
    content_encoding = response.getheader('Content-Encoding')
    if content_encoding == 'gzip':
        data = gzip.GzipFile(fileobj=response).read()
    elif content_encoding == 'deflate':
        decompressobj = zlib.decompressobj(-zlib.MAX_WBITS)
        data = decompressobj.decompress(response.read())+decompressobj.flush()
    else:
        data = response.read()
    return response, data

def fetch_video_metadata(vid, p):
    '''Fetch video metadata.

    Arguments: vid, pid

    Return value: {'cid': cid, 'title': title}
    '''
    url_get_metadata = 'http://api.bilibili.com/view?'
    
    req_args = {'type': 'json', 'appkey': APPKEY, 'id': vid, 'page': p}
    req_args['sign'] = bilibili_hash(req_args)
    _, response = fetch_url(url_get_metadata+urllib.parse.urlencode(req_args), user_agent=USER_AGENT_API)
    try:
        response = dict(json.loads(response.decode('utf-8', 'replace')))
    except (TypeError, ValueError):
        raise ValueError('Can not get \'cid\' from %s' % url)
    if 'error' in response:
        logging.error('Error message: %s' % response.get('error'))
    if 'cid' not in response:
        raise ValueError('Can not get \'cid\' from %s' % url)
    return response

# write object to JSON file
def obj2json(obj, json_path):
    with open(json_path, 'w') as f: # write object to JSON, pretty printed
        json.dump(obj, f, sort_keys=True, indent=4, separators=(',', ': '))

def main():
    if len(sys.argv) < 2:
        sys.exit('Usage: %s <video-id>\nYou can find the video-id from the url: http://www.bilibili.com/video/av<video-id>/' % sys.argv[0])
    
    vid = sys.argv[1]
    p = 1 # just use page 1 to get the metadata
    metadata = fetch_video_metadata(vid, p)
    
    # append URL to the metadata
    metadata['url'] = 'http://www.bilibili.com/video/av{vid}/'.format(vid = vid)
    
    # write to JSON file
    obj2json(metadata, 'bilibili-av{vid}-{cid}.json'.format(vid = vid, cid = metadata['cid']))
    
if __name__ == '__main__':
    main()