![banner](https://github.com/user-attachments/assets/eb30a500-6d27-42f1-bded-24221930a8e3)
# libWiiPy
libWiiPy is a modern Python 3 library for handling the various files and formats found on the Wii. It aims to be simple to use, well maintained, and offer as many features as reasonably possible in one library, so that a newly-written Python program could do 100% of its Wii-related work with just one library. It also aims to be fully cross-platform, so that any tools written with it can also be cross-platform.

libWiiPy is inspired by [libWiiSharp](https://github.com/TheShadowEevee/libWiiSharp), which was originally created by `Leathl` and is now maintained by [@TheShadowEevee](https://github.com/TheShadowEevee). If you're looking for a Wii library that isn't in Python, then go check it out!


# Features
This list will expand as libWiiPy is developed, but these features are currently available:
- TMD and Ticket parsing/editing (`.tmd`, `.tik`)
- Title parsing/editing, including content encryption/decryption (both retail and development)
- WAD file parsing/editing (`.wad`)
- Downloading titles from the NUS
- Packing and unpacking U8 archives (`.app`, `.arc`)
- Decompressing ASH files (`.ash`, both the standard variants and the variants found in My Pokémon Ranch)
- IOS patching
- NAND-related functionality:
  - EmuNAND title management (currently requires an existing EmuNAND)
  - `content.map` parsing/editing
  - `uid.sys` parsing/editing
- Assorted miscellaneous features used to make the other core features possible

For a more detailed look at what's available in libWiiPy, check out our [API docs](https://ninjacheetah.github.io/libWiiPy).

# Usage
The easiest way to get libWiiPy for your project is to install the latest version of the library from PyPI, as shown below. 
```sh
pip install -U libWiiPy
```
Our PyPI project page can be found [here](https://pypi.org/project/libWiiPy/).

Because libWiiPy is very early in development, you may want to use the latest version of the package via git instead, so that you have the latest features available. You can do that like this:
```sh
pip install -U git+https://github.com/NinjaCheetah/libWiiPy
```
Please be aware that because libWiiPy is in a very early state right now, many features may be subject to change, and methods and properties available now have the potential to disappear in the future.
                               
For more tips on getting started, see our guide [here](https://ninjacheetah.github.io/libWiiPy/usage/installation.html).

# Building
To build this package locally, the steps are quite simple, and should apply to all platforms. Make sure you've set up your `venv` first!

First, install the dependencies from `requirements.txt`:
```sh
pip install -r requirements.txt
```

Then, build the package using the Python `build` module:
```sh
python -m build
```

And that's all! You'll find your compiled pip package in `dist/`.

# Special Thanks
This project wouldn't be possible without the amazing people behind its predecessors and all of the people who have contributed to the documentation of the Wii's inner workings over at [WiiBrew](https://wiibrew.org).

## Special Thanks to People Behind Related Projects
- Xuzz, SquidMan, megazig, Matt_P, Omega and The Lemon Man for creating Wii.py
- Leathl for creating libWiiSharp
- TheShadowEevee for maintaining libWiiSharp

## Special Thanks to WiiBrew Contributors
Thank you to all of the contributors to the documentation on the WiiBrew pages that make this all understandable! Some of the key articles referenced are as follows:
- [Title metadata](https://wiibrew.org/wiki/Title_metadata), for the documentation on how a TMD is structured
- [WAD files](https://wiibrew.org/wiki/WAD_files), for the documentation on how a WAD is structured
- [IOS history](https://wiibrew.org/wiki/IOS_history), for the documentation on IOS TIDs and how IOS is versioned

### One additional special thanks to [@DamiDoop](https://github.com/DamiDoop)!
She made the very cool banner you can see at the top of this README, and has also helped greatly with my sanity throughout debugging this library.

**Note:** While libWiiPy is directly inspired by libWiiSharp and aims to have feature parity with it, no code from either libWiiSharp or Wii.py was used in the making of this library. All code is original and is written by [@NinjaCheetah](https://github.com/NinjaCheetah), [@rvtr](https://github.com/rvtr), and any other GitHub contributors.

