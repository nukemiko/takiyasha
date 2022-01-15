from setuptools import setup

with open('./README.md') as f:
    readme = f.read()

with open('./requirements.txt') as f:
    dependencies = f.read()
dependencies = dependencies.strip().splitlines()

setup(
    name='takiyasha',
    version='0.2.0',
    packages=['takiyasha', 'takiyasha.app', 'takiyasha.algorithms', 'takiyasha.algorithms.ncm', 'takiyasha.algorithms.qmc'],
    url='https://github.com/nukemiko/takiyasha',
    license='MIT',
    author='nukemiko',
    author_email='',
    description='DRM protected music unlocker',
    long_description=readme,
    python_requires='>=3.8',
    install_requires=dependencies,
    entry_points={
        'console_scripts': [
            'takiyasha = takiyasha.app.cli:main'
        ]
    }
)
