#!/usr/bin/env python
import sys, re
import math
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
            width = int(elem.get('width', 1))
            height = int(elem.get('height', 1))
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

def extract_content(html, threshold=None):
    '''
    extract content from html by threshold
      html - source data as unicode
      threshold - the value above which a line is considered content
    '''
    title, tag_ratio_list = get_tag_ratio_list(html)
    if threshold is None:
        threshold = AVG_RATE * sum(r[0] for r in tag_ratio_list) // len(tag_ratio_list)

    dp = ContentParser()
    for v, line in tag_ratio_list:
        if v > threshold:
            dp.feed(line)
    yield title
    for chunk in dp.data_list:
        if not chunk:
            continue
        def onimage(m):
            imgid = int(m.group(2))
            src = imgs[imgid]
            return '[img src="%s"]' % src
        chunk = re.sub(r'\[(image)+ (\d+)\]', onimage, chunk)
        yield chunk

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
