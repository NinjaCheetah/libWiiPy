# libWiiPy.title Package

## Modules
The `libWiiPy.title` package contains modules for interacting with Wii titles. This is the most complete package in libWiiPy, and therefore offers the most functionality.

| Module                                         | Description                                                                                                                   |
|------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------|
| [libWiiPy.title.cert](/title/cert)             | Provides support for parsing and validating the certificates used for title verification                                      |
| [libWiiPy.title.commonkeys](/title/commonkeys) | Provides easy access to all common encryption keys                                                                            |
| [libWiiPy.title.content](/title/content)       | Provides support for parsing and editing content included as part of digital titles                                           |
| [libWiiPy.title.crypto](/title/crypto)         | Provides low-level cryptography functions used to handle encryption in other modules                                          |
| [libWiiPy.title.iospatcher](/title/iospatcher) | Provides an easy interface to apply patches to IOSes                                                                          |
| [libWiiPy.title.nus](/title/nus)               | Provides support for downloading TMDs, Tickets, encrypted content, and the certificate chain from the Nintendo Update Servers |
| [libWiiPy.title.ticket](/title/ticket)         | Provides support for parsing and editing Tickets used for content decryption                                                  |
| [libWiiPy.title.title](/title/title.title)     | Provides high-level support for parsing and editing an entire title with the context of each component                        |
| [libWiiPy.title.tmd](/title/tmd)               | Provides support for parsing and editing TMDs (Title Metadata)                                                                |
| [libWiiPy.title.util](/title/util)             | Provides some simple utility functions relating to titles                                                                     |
| [libWiiPy.title.wad](/title/wad)               | Provides support for parsing and editing WAD files, allowing you to load each component into the other available classes      |

### libWiiPy.title Package Contents

```{toctree}
:maxdepth: 4

/title/cert
/title/commonkeys
/title/content
/title/crypto
/title/iospatcher
/title/nus
/title/ticket
/title/title.title
/title/tmd
/title/util
/title/wad
```
