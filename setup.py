from setuptools import setup

with open('./README.md') as f:
    readme = f.read()

setup(
    name='takiyasha',
    version='0.3.5',
    packages=[
        'takiyasha',
        'takiyasha.app',
        'takiyasha.algorithms',
        'takiyasha.metadata',
        'takiyasha.algorithms.kgm',
        'takiyasha.algorithms.ncm',
        'takiyasha.algorithms.noop',
        'takiyasha.algorithms.qmc',
    ],
    package_data={
        'takiyasha.algorithms.kgm': ['binaries/kgm.v2.mask'],
        'takiyasha.algorithms.qmc': ['binaries/qmc.v1.stream.segment']
    },
    url='https://github.com/nukemiko/takiyasha',
    project_urls={
        'Documentation': 'https://github.com/nukemiko/takiyasha',
        'Source': 'https://github.com/nukemiko/takiyasha'
    },
    license='MIT',
    author='nukemiko',
    description='使用 Python 编写的加密音乐解锁工具',
    long_description=readme,
    long_description_content_type='text/markdown',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
    ],
    keywords=['unlock', 'music', 'audio',
              'qmc', 'ncm', 'mflac', 'mgg', 'kgm', 'vpr',
              'netease', '163', 'qqmusic', 'kugou', 'kgmusic'],
    python_requires='>=3.8',
    install_requires=[
        'click',
        'mutagen',
        'pycryptodomex'
    ],
    entry_points={
        'console_scripts': [
            'takiyasha = takiyasha.app.cli:main',
            'takiyasha-unlocker = takiyasha.app.cli:main',
            'unlocker = takiyasha.app.cli:main'
        ]
    }
)
