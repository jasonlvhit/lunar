import sys
sys.path.append('path-to-pumpkin')

#from tests.orm import test_database
from tests.template import test_template

def run_test():
	test_template.runtest()


if __name__ == '__main__':
	run_test()