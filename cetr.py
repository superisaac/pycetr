#!/usr/bin/env python

import re
import math
import fileinput
from HTMLParser import HTMLParser
from cStringIO import StringIO

class TAG:
    def __init__(self, tag, attrs):
        self.tag = tag
        self.attrs = attrs
        self.children = []
        self.depth = 0

    def __unicode__(self):
        #p = ' ' * self.depth
        p = ''
        s = p + '<%s' % self.tag
        s += ''.join(' %s="%s"' % (k, v) for k, v in self.attrs)
        if self.children:
            s += '>'
            sub_tag = False
            for c in self.children:
                if isinstance(c, TAG):
                    sub_tag = True
                    c.depth = self.depth + 1
                    s += u'\n%s' % unicode(c)
                else:
                    s += unicode(c)
            if sub_tag:
                s += p
            s += ('</%s>\n' % self.tag)
        else:
            s += '/>'
        return s

class ContentParser(HTMLParser):
    ''' Extract data content from processed html document
    '''
    title = ''
    def __init__(self, *args, **kw):
        HTMLParser.__init__(self, *args, **kw)
        self.data_list = []
    
    def handle_data(self, data):
        self.data_list.append(data)

class TreeParser(HTMLParser):
    ''' Build HTML document into a tree
    '''
    def __init__(self, *args, **kw):
        HTMLParser.__init__(self, *args, **kw)
        self.state = 'init'
        # put root element
        self.elem_stack = [TAG('root', [])]

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if self.state == 'init':
            if tag == 'script':
                self.state = 'in_script'
                return
            elif tag == 'style':
                self.state = 'in_style'
                return
            elif tag == 'title':
                self.state = 'in_title'
        self.elem_stack.append(TAG(tag, attrs))

    def handle_endtag(self, tag):
        tag = tag.lower()
        if self.state == 'in_script':
            if tag == 'script':
                self.state = 'init'
            return
        elif self.state == 'in_style':
            if tag == 'style':
                self.state = 'init'
            return
        elif self.state == 'in_title':
            if tag == 'title':
                self.state = 'init'
            return
        elif self.state == 'init':
            self.collect_children(tag)

    def collect_children(self, tag):
        matched_element = None
        idx = -1
        for idx in range(len(self.elem_stack) -1, -1, -1):
            if self.elem_stack[idx].tag == tag:
                matched_element = self.elem_stack[idx]
                break
        if matched_element:
            self.elem_stack, children = self.elem_stack[:idx + 1], self.elem_stack[idx + 1:]
            matched_element.children.extend(children)

    def handle_data(self, data):
        if self.state == 'init':
            if self.elem_stack:
                self.elem_stack[-1].children.append(data.strip())
        elif self.state == 'in_title':
            self.title = data.strip()

    def handle_charref(self, name):
        pass

    def handle_entityref(self, name):
        pass

    def handle_comment(self, data):
        pass

def get_tag_ratio_list(html):
    '''
    A list of smoothed tag ratios
      html - source data as unicode
    '''
    p = TreeParser()
    p.feed(html)
    p.collect_children('root')
    tag = p.elem_stack[-1]
    lines = unicode(tag).split('\n')
    lines = [line for line in lines if not re.match(r'^\s*$', line)]
    
    tag_ratio_list = []
    for line in lines:
        data = ''.join(re.split('<.*?>', line))
        if line.find('<') < 0 or len(line) == 0 or len(line) == len(data):
            v = len(line)
        else:
            v = len(data)/ (len(line) - len(data))
        tag_ratio_list.append(v)

    # smooth tag ratios
    smoothed = []
    c1 = math.exp(-1.0/8.0)
    c2 = math.exp(-4.0/8.0)
    for idx in range(2, len(tag_ratio_list) - 2):
        v = (tag_ratio_list[idx - 2] * c2 +
             tag_ratio_list[idx - 1] * c1 +
             tag_ratio_list[idx] +
             tag_ratio_list[idx + 1] * c1 +
             tag_ratio_list[idx + 2] * c2)
        v = v / (2 * c1 + 2 * c2 + 1)
        smoothed.append((v, lines[idx]))
    return p.title, smoothed

def extract_content(html, threshold=None):
    '''
    extract content from html by threshold
      html - source data as unicode
      threshold - the value above which a line is considered content
    '''
    title, tag_ratio_list = get_tag_ratio_list(html)
    if threshold is None:
        threshold = 5.0 * sum(r[0] for r in tag_ratio_list) // len(tag_ratio_list)

    dp = ContentParser()
    for v, line in tag_ratio_list:
        if v > threshold:
            dp.feed(line)
    yield title
    for chunk in dp.data_list:
        yield chunk

def test():
    '''
    Get a url to 
    '''
    import sys
    import urllib, urllib2
    try:
        url = sys.argv[1]
        req = urllib2.Request(url)
        resp = urllib2.urlopen(req, None, 10)
    except:
        print >>sys.stderr, 'Usage: %s <url>' % sys.argv[0]
        raise
    info = resp.info()
    charset = info.getparam('charset')
    ttype = info.gettype()
    assert ttype.startswith('text/html')
    data = resp.read()
    if charset is None:
        # Ad hoc way to find charset from http-equiv
        m = re.search(r'charset=(?P<charset>[\w\-]+)', data)
        if m:
            charset = m.group('charset')
        else:
            charset = 'utf-8'            
    data = unicode(data, charset)
    for chunk in extract_content(data):
        print chunk

if __name__ == '__main__':
    test()
