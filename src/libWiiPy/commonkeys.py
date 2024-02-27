# "commonkeys.py" from libWiiPy by NinjaCheetah

default_key = 'ebe42a225e8593e448d9c5457381aaf7'
korean_key = '63b82bb4f4614e2e13f2fefbba4c9b7e'
vwii_key = '30bfc76e7c19afbb23163330ced7c28d'


def get_default_key():
    """Returns the regular Wii Common Key used to encrypt most content."""
    return default_key


def get_korean_key():
    """Returns the Korean Wii Common Key used to encrypt Korean content."""
    return korean_key


def get_vwii_key():
    """Returns the vWii Common Key used to encrypt vWii-specific content."""
    return vwii_key
