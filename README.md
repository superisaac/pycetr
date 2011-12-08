pycetr
======
 - python implementation of Content Extraction via Tag Ratios

To extract Content from HTML Pages, the program is based on the paper http://www.cs.uiuc.edu/~hanj/pdf/www10_tweninger.pdf

Author: Zeng Ke 

Email: superisaac.ke@gmail.com

LICENSE
======
pycetr is licensed under MIT license http://en.wikipedia.org/wiki/MIT_License

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
"pycetr"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

INSTALL and RUN
======

```
% cd pycetr
% sudo python setup.py install
% curl -s 'http://www.nytimes.com/2011/12/02/technology/eu-e-book-sales-hampered-by-tax-structure.html' | python -m cetr
```
