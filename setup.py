import setuptools

setuptools.setup(
    name='web_app',
    version='0.0',
    packages=setuptools.find_packages(),
    author='Yuki Wada',
    author_email='yuki.w.228285@gmail.com',
    description='',
    zip_safe=False,
    license='',
    keywords='',
    url='',
    install_requires=[
        'numpy',
        'pandas==0.25.3',
        'nlp_model',
        'search_engine',
        'flask==1.1.1',
        'gevent==1.4.0',
        'gevent-websocket==0.10.1',
        'flask-cors==3.0.8'
    ],
    dependency_links=[
        'https://github.com/Yuki-Wada/nlp_model/tarball/master#egg=nlp_model',
        'https://github.com/Yuki-Wada/search_engine/tarball/master#egg=search_engine'
    ]
)
