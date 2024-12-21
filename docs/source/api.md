# API Documentation

libWiiPy is divided up into a few subpackages to organize related features.

| Package                              | Description                                                     |
|--------------------------------------|-----------------------------------------------------------------|
| [libWiiPy.archive](/archive/archive) | Used to pack and extract archive formats used on the Wii        |
| [libWiiPy.media](/media/media)       | Used for parsing and manipulating media formats used on the Wii |
| [libWiiPy.nand](/nand/nand)          | Used for working with EmuNANDs and core system files on the Wii |
| [libWiiPy.title](/title/title)       | Used for parsing and manipulating Wii titles                    |

When using libWiiPy in your project, you can choose to either only import the package that you need, or you can use `import libWiiPy` to import the entire package, which each module being available at `libWiiPy.<package>.<module>`.

## Full Package Contents

```{toctree}
:maxdepth: 8

/archive/archive
/media/media
/nand/nand
/title/title
```
