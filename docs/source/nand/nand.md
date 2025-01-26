# libWiiPy.nand Package

## Description

The `libWiiPy.nand` package contains modules for parsing and manipulating EmuNANDs as well as modules for parsing and editing core system files found on the Wii's NAND.

## Modules

| Module                                 | Description                                                                                                                      |
|----------------------------------------|----------------------------------------------------------------------------------------------------------------------------------|
| [libWiiPy.nand.emunand](/nand/emunand) | Provides support for parsing, creating, and editing EmuNANDs                                                                     |
| [libWiiPy.nand.setting](/nand/setting) | Provides support for parsing, creating, and editing `setting.txt`, which is used to store the console's region and serial number |
| [libWiiPy.nand.sys](/nand/sys)         | Provides support for parsing, creating, and editing `uid.sys`, which is used to store a log of all titles run on a console       |

## Full Package Contents

```{toctree}
:maxdepth: 4

/nand/emunand
/nand/setting
/nand/sys
```
