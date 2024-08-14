# "__init__.py" from libWiiPy by NinjaCheetah & Contributors
# https://github.com/NinjaCheetah/libWiiPy
#
# These are the essential submodules from libWiiPy that you'd probably want imported by default.

__all__ = ["archive", "nand", "title"]

from . import archive
from . import nand
from . import title
