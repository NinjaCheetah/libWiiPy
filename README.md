# libWiiPy
libWiiPy is a port of the project [libWiiSharp](https://github.com/TheShadowEevee/libWiiSharp), originally created by `Leathl`, now maintained by [@TheShadowEevee](https://github.com/TheShadowEevee), back to Python after it was created by porting [Wii.py](https://github.com/grp/Wii.py) to C#.

### Why port this again instead of just updating Wii.py?
This is a really good question. Frankly, a lot of it comes from the fact that I am inexperienced with all of this Wii stuff. Attempting to recreate the features of libWiiSharp in Python with all of the freedom to do that however I see fit makes it a lot easier for someone like me to make this work. The code for Wii.py is also on the older side and is just written in a way that I can't easily understand. It's helpful as a reference here and there, but I mostly want to write this library in a unique way.

I also want to package this as a proper PyPI package, and starting with a clean slate will make that a lot easier as well.

# Building
To build this package locally, the steps are quite simple, and should apply to all platforms. Make sure you've set up your `venv` first!

First, install the dependencies from `requirements.txt`:
```py
pip install -r requirements.txt
```

Then, build the package using the Python `build` module:
```py
python -m build
```

And that's all! You'll find your compiled pip package in `dist/`.

# Special Thanks
This project wouldn't be possible without the amazing people behind its predecessors and all of the people who have contributed to the documentation of the Wii's inner workings over at [Wiibrew](https://wiibrew.org).

## Special Thanks from libWiiSharp
- Xuzz, SquidMan, megazig, Matt_P, Omega and The Lemon Man for Wii.py
- megazig for his bns conversion code (bns.py)
- SquidMan for Zetsubou
- Arikado and Lunatik for Dop-Mii
- Andre Perrot for gbalzss
- Leathl for creating libWiiSharp
- TheShadowEevee for maintaining libWiiSharp

## Special Thanks to Wiibrew Contributors
Thank you to all of the contributors to the documentation on the Wiibrew pages that make this all understandable! Some of the key articles referenced are as follows:
- [Title metadata](https://wiibrew.org/wiki/Title_metadata), for the documentation on how a TMD is structured
- [WAD files](https://wiibrew.org/wiki/WAD_files), for the documentation on how a WAD is structured
- [IOS history](https://wiibrew.org/wiki/IOS_history), for the documentation on IOS TIDs and how IOS is versioned
