from setuptools import find_packages, setup
setup(
    name='clickupmethods',
    packages=find_packages(include=['clickupmethods']),
    version='0.1.0',
    description='Clickup lib',
    author='Suhas Hoysala',
    license='MIT',
    install_requires=[],
    setup_requires=['pytest-runner'],
    tests_require=['pytest==4.4.1'],
    test_suite='tests',
)