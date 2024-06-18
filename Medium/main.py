from sonarqube.core import Core



def main():
    core = Core(url='http://localhost:9000', token='sqa_6e48c6f001f0169d732cd7ff8377c3b92464a588')
    
    version = core.get(endpoint='/api/server/version')
    print(version)

main()

