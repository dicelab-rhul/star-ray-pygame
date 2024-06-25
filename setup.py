from setuptools import setup, find_packages  # ,find_namespace_packages

####  NOTE: ####
# sometimes an error similar to:
# libGL error: MESA-LOADER: failed to open radeonsi: /usr/lib/dri/radeonsi_dri.so: cannot open shared object file: No such file or directory (search paths /usr/lib/x86_64-linux-gnu/dri:\$${ORIGIN}/dri:/usr/lib/dri, suffix _dri)
# libGL error: failed to load driver: radeonsi
# ...
# may occur, I fixed this using:
# echo 'export LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libstdc++.so.6' >> ~/.bashrc
# no idea why this happens, there is a github issue: https://github.com/pygame/pygame/issues/3405

setup(
    name="star_ray_pygame",
    version="0.0.2",
    author="Benedict Wilkins",
    author_email="benrjw@gmail.com",
    description="An optional extra for the `star_ray` package that supports `pygame` as a UI backend.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    url="https://github.com/dicelab-rhul/star_ray_pygame",
    install_requires=[
        "star_ray[xml]",
        "pygame",
        "pywinctl",
        "lxml",
        "cairosvg",
        "numpy",
        "pydantic",
    ],
    python_requires=">=3.10",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python :: 3.10",
    ],
)
