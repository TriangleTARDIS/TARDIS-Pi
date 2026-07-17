import runpy
import os
import sys

print('Running TARDIS Console Package.')
package_source_path = os.path.dirname(__file__)
sys.path.insert(0, package_source_path)
runpy.run_module('src.console', run_name='__main__')
