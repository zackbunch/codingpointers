import logging
from pprint import pprint
from sonarqube.group import Group
from sonarqube.core import Core

def main():
    logging.basicConfig(level=logging.INFO)
    core = Core(url='http://localhost:9000', token='squ_3a51ce4e2e1f8790eaca408e90d820297d05550a')
    group = Group(core=core)
    try:
        res = group.get_group_id(name='za')
        print(res)
    except Exception as e:
        logging.error(f"Error: {str(e)}")

if __name__ == "__main__":
    main()