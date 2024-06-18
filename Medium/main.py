from pprint import pprint
from sonarqube.group import Group
from sonarqube.core import Core


def main():
    core = Core(url='http://localhost:9000', token='squ_dec9222692d39672f14a7e6c68de2170e91867d7')
    group = Group(core=core)
    res = group.create_group(name='zacktenant')
    pprint(res)
    
    

main()

