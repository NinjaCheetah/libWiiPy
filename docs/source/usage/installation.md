# Installation
The first thing you'll want to do to get set up is to install the `libWiiPy` package. This can be done one of two ways.

**For a more stable experience,** you can install the latest release from PyPI just like any other Python package:
```shell
pip install libWiiPy
```

**If you prefer to live on the edge** (or just want to use features currently in development), you can also build the latest version from git:
```shell
pip install git+https://github.com/NinjaCheetah/libWiiPy
```

If you'd like to check the latest release, our PyPI page can be found [here](https://pypi.org/project/libWiiPy/). Release notes and build files for each release can be found over on our [GitHub releases page](https://github.com/NinjaCheetah/libWiiPy/releases/latest).

:::{caution}
libWiiPy is under heavy active development! While we try our hardest to not make breaking changes, things move quickly and that sometimes can cause problems.
:::

For those who are truly brave and want to experiment with the latest features, you can try building from an alternative branch. However, if you're going to do this, please be aware that features on branches other than `main` are likely very incomplete, and potentially completely broken. New features are only merged into `main` once they've been proven to at least work for their intended purpose. This does not guarantee a bug-free experience, but you are significantly less likely to run into show-stopping bugs.
