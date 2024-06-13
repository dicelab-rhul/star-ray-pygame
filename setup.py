from setuptools import setup, find_packages  # ,find_namespace_packages


from setuptools import setup, find_packages

setup(
    name="star_ray_pygame",
    version="0.0.1",
    author="Benedict Wilkins",
    author_email="benrjw@gmail.com",
    description="An optional extra for the `star_ray` package that supports pygame as a UI backend.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    url="https://github.com/BenedictWilkins/star_ray_pygame",
    install_requires=[
        "pygame",
        "pywinctl",
        "cairosvg",
        "pydantic",
        "numpy",
        "lxml",
        "more_itertools",
    ],
    python_requires=">=3.10",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python :: 3.10",
    ],
)
