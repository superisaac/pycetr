import distutils.core
import sys

kwargs = {}
distutils.core.setup(
    name='cetr',
    version='0.1.0',
    py_modules=['cetr', 'CustomHTMLParser'],
    author='superisaac',
    author_email='superisaac.ke@gmail.com',
    url='https://github.com/superisaac/pycetr',
    license='http://www.opensource.org/licenses/mit-license.php',
    description='pycetr is the python implementation of Content Extraction via Tag ratios',
    **kwargs
)
