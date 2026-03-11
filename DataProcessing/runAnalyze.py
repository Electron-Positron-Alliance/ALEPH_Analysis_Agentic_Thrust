import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'tools', 'python'))
from runAnalyze import main; main(observable_tag='thrust')
