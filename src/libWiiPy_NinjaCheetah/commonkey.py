from .shared import hex_string_to_byte_array


class CommonKey:
    def __init__(self):
        self.default_key = "ebe42a225e8593e448d9c5457381aaf7"
        self.korean_key = "63b82bb4f4614e2e13f2fefbba4c9b7e"
        self.vwii_key = "30bfc76e7c19afbb23163330ced7c28d"

    def get_default_key(self):
        return hex_string_to_byte_array(self.default_key)

    def get_korean_key(self):
        return hex_string_to_byte_array(self.korean_key)

    def get_vwii_key(self):
        return hex_string_to_byte_array(self.vwii_key)
