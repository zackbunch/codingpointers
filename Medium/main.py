import logging
from pprint import pprint
from sonarqube.group import Group
from sonarqube.core import Core

def main():
    logging.basicConfig(level=logging.DEBUG)
    core = Core(url='http://localhost:9000', token='')
    group = Group(core=core)
    try:
        res = group.create_group(name='testgroup')
    except Exception as e:
        logging.error(f"Error: {str(e)}")

if __name__ == "__main__":
    main()