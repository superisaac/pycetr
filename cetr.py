#!/usr/bin/env python
import sys, re
import math
import random
import HTMLParser
import CustomHTMLParser

# Hijack the HTMLParser
sys.modules['HTMLParser'] = sys.modules['CustomHTMLParser']

imgs = []
AVG_RATE = 3.5

class ContentParser(CustomHTMLParser.HTMLParser):
    ''' Extract data content from processed html document
    '''
    def __init__(self, *args, **kw):
        CustomHTMLParser.HTMLParser.__init__(self, *args, **kw)
        self.data_list = []

    def handle_data(self, data):
        data = data.strip()
        self.data_list.append(data)

def prettify(html):
    from BeautifulSoup import BeautifulSoup
    soup = BeautifulSoup(html)
    for scpt in soup.findAll('script'):
        scpt.extract()

    for scpt in soup.findAll('style'):
        scpt.extract()

    for elem in soup.findAll('img'):
        idx = len(imgs)
        imgsrc = elem.get('src', '')
        if imgsrc:
            imgs.append(imgsrc)
            try:
                width = int(elem.get('width', 1))
                height = int(elem.get('height', 1))
            except ValueError:
                width = 1
                height = 1
            if width >= 100 and height >= 100:
                prefix = 'image' * 20
            else:
                prefix = 'image'
            text = '[%s %s]' % (prefix, idx)
            elem.replaceWith(text)

    title = ''
    titleTag = soup.html.head.title
    if titleTag:
        title = titleTag.string
    return title, soup.prettify()

def get_tag_ratio_list(html):
    '''
    A list of smoothed tag ratios
      html - source data as unicode
    '''
    title, html= prettify(html)
    lines = html.split('\n')
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
    return title, smoothed

def extract_content_by_threshold(html, threshold=None):
    '''
    extract content from html by threshold
      html - source data as unicode
      threshold - the value above which a line is considered content
    '''
    title, tag_ratio_list = get_tag_ratio_list(html)
    if threshold is None:
        threshold = AVG_RATE * sum(r[0] for r in tag_ratio_list) // len(tag_ratio_list)

    content_lines = [(v, line) for v, line in tag_ratio_list if v > gthreshold]
    return get_content(content_lines)

def get_content(content_lines):
    dp = ContentParser()
    for v, line in content_lines:
        dp.feed(line)
    for chunk in dp.data_list:
        if not chunk:
            continue
        def onimage(m):
            imgid = int(m.group(2))
            src = imgs[imgid]
            return '[img src="%s"]' % src
        chunk = re.sub(r'\[(image)+ (\d+)\]', onimage, chunk)
        yield chunk

class Point2D:
    def __init__(self, x, y, data=None):
        self.x = x
        self.y = y
        self.data = data

    def set_pos(self, x, y):
        if self.data != 0:
            self.x = x
            self.y = y

    def distance(self, other):
        dx = self.x - other.x
        dy = self.y - other.y
        return dx*dx + dy*dy
    
    def __str__(self):
        return '(%s, %s)' % (self.x, self.y)
    
def boundbox(points):
    minx, miny = None, None
    maxx, maxy = None, None
    for p in points:
        if minx is None:
            minx = p.x
        elif minx > p.x:
            minx = p.x

        if maxx is None:
            maxx = p.x
        elif maxx < p.x:
            maxx = p.x

        if miny is None:
            miny = p.y
        elif miny > p.y:
            miny = p.y

        if maxy is None:
            maxy = p.y
        elif maxy < p.y:
            maxy = p.y
    return (minx, miny, maxx, maxy)
    
def kmean_cluster(html, k=2):
    title, tag_ratio_list = get_tag_ratio_list(html)
    points = []
    ratio_list = [v for v, line in tag_ratio_list]
    for i in xrange(len(ratio_list) - 1):
        nlist = ratio_list[i+1: i+6]
        dv = sum(nlist)/len(nlist) - ratio_list[i]
        if dv < 0:
            dv = -dv
        p = Point2D(ratio_list[i], dv, i)
        points.append(p)        

    minx, miny, maxx, maxy = boundbox(points)
    kernels = []
    for i in xrange(k):
        x = minx + random.random() * (maxx - minx)
        y = miny + random.random() * (maxy - miny)
        p = Point2D(x, y, i)
        kernels.append(p)
    kernels[0].x = 0
    kernels[0].y = 0

    for i in xrange(10):
        groups = [set() for x in range(k)]
        for p in points:
            dist_list = [(p.distance(kernel), n) for n, kernel in enumerate(kernels)]
            dist_list.sort()
            n = dist_list[0][1]
            groups[n].add(p)

        for i, (kernel, g) in enumerate(zip(kernels, groups)):
            sumx, sumy = 0, 0
            for p in g:
                sumx += p.x
                sumy += p.y
            
            if len(g):
                kernel.set_pos(sumx / len(g),
                               sumy / len(g))
    
        #for kernel, g in zip(kernels, groups):
        #    print kernel, len(g)
        #print

    gps = []
    for i, (k, g) in enumerate(zip(kernels, groups)):
        if i == 0:
            continue
        for p in g:
            gps.append((p.data, p))
    gps.sort()
    content_lines = []
    for i, p in gps:
        content_lines.append(tag_ratio_list[i])
    return get_content(content_lines)    

#extract_content = extract_content_by_cluster
extract_content = kmean_cluster

def test():
    import fileinput
    charset = 'utf-8'
    data = ''
    for line in fileinput.input():
        data += unicode(line, charset)
    for chunk in extract_content(data):
        print chunk

if __name__ == '__main__':
    test()
