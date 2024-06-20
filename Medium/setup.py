from setuptools import setup, find_packages

setup(
    name='sonarqube',
    version='0.0.1',
    author='Zack Bunch',
    author_email='zackbunch96@gmail.com',
    url='https://www.youtube.com/@codingpointers',
    packages=find_packages(),
    install_requires=[
        'requests',
    ],
    description='A Python package to interact with the SonarQube API',
    # long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)