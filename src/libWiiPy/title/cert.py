# "title/cert.py" from libWiiPy by NinjaCheetah & Contributors
# https://github.com/NinjaCheetah/libWiiPy
#
# See https://wiibrew.org/wiki/Certificate_chain for details about the Wii's certificate chain

import io
from enum import IntEnum as _IntEnum
from ..shared import _align_value, _pad_bytes
from .ticket import Ticket
from .tmd import TMD
from Crypto.Hash import SHA1
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15


class CertificateType(_IntEnum):
    RSA_4096 = 0x00010000
    RSA_2048 = 0x00010001
    ECC = 0x00010002


class CertificateSignatureLength(_IntEnum):
    RSA_4096 = 0x200
    RSA_2048 = 0x100
    ECC = 0x3C


class CertificateKeyType(_IntEnum):
    RSA_4096 = 0x00000000
    RSA_2048 = 0x00000001
    ECC = 0x00000002


class CertificateKeyLength(_IntEnum):
    RSA_4096 = 0x200
    RSA_2048 = 0x100
    ECC = 0x3C


class Certificate:
    """
    A Certificate object used to parse a certificate used for the Wii's content verification.

    Attributes
    ----------
    type: CertificateType
        The type of the certificate, either RSA-2048, RSA-4096, or ECC.
    signature: bytes
        The signature data of the certificate.
    issuer: str
        The certificate that issued this certificate.
    pub_key_type: CertificateKeyType
        The type of public key contained in the certificate, either RSA-2048, RSA-4096, or ECC.
    child_name: str
        The name of this certificate.
    pub_key_id: int
        The ID of this certificate's public key.
    pub_key_modulus: int
        The modulus of this certificate's public key. Combined with the exponent to get the full key.
    pub_key_exponent: int
        The exponent of this certificate's public key. Combined with the modulus to get the full key.
    """
    def __init__(self):
        self.type: CertificateType | None = None
        self.signature: bytes = b''
        self.issuer: str = ""
        self.pub_key_type: CertificateKeyType | None = None
        self.child_name: str = ""
        self.pub_key_id: int = 0
        self.pub_key_modulus: int = 0
        self.pub_key_exponent: int = 0

    def load(self, cert: bytes) -> None:
        """
        Loads certificate data into the Certificate object, allowing you to parse the certificate.

        Parameters
        ----------
        cert: bytes
            The data for the certificate to load.
        """
        with io.BytesIO(cert) as cert_data:
            # Read the first 4 bytes of the cert to get the certificate's type.
            try:
                self.type = CertificateType.from_bytes(cert_data.read(0x4))
            except ValueError:
                raise ValueError("Invalid Certificate Type!")
            cert_length = CertificateSignatureLength[self.type.name]
            self.signature = cert_data.read(cert_length.value)
            cert_data.seek(0x40 + cert_length.value)
            self.issuer = str(cert_data.read(0x40).replace(b'\x00', b'').decode())
            try:
                cert_data.seek(0x80 + cert_length.value)
                self.pub_key_type = CertificateKeyType.from_bytes(cert_data.read(0x4))
            except ValueError:
                raise ValueError("Invalid Certificate Key type!")
            cert_data.seek(0x84 + cert_length.value)
            self.child_name = str(cert_data.read(0x40).replace(b'\x00', b'').decode())
            cert_data.seek(0xC4 + cert_length.value)
            self.pub_key_id = int.from_bytes(cert_data.read(0x4))
            key_length = CertificateKeyLength[self.pub_key_type.name]
            cert_data.seek(0xC8 + cert_length.value)
            self.pub_key_modulus = int.from_bytes(cert_data.read(key_length.value))
            if self.pub_key_type == CertificateKeyType.RSA_4096 or self.pub_key_type == CertificateKeyType.RSA_2048:
                self.pub_key_exponent = int.from_bytes(cert_data.read(0x4))

    def dump(self) -> bytes:
        """
        Dump the certificate object back into bytes.

        Returns
        -------
        bytes:
            The certificate file as bytes.
        """
        cert_data = b''
        cert_data += int.to_bytes(self.type.value, 4)
        cert_data += self.signature
        cert_data = _pad_bytes(cert_data)
        # Pad out the issuer name with null bytes.
        issuer = self.issuer.encode()
        while len(issuer) < 0x40:
            issuer += b'\x00'
        cert_data += issuer
        cert_data += int.to_bytes(self.pub_key_type.value, 4)
        # Pad out the child cert name with null bytes
        child_name = self.child_name.encode()
        while len(child_name) < 0x40:
            child_name += b'\x00'
        cert_data += child_name
        cert_data += int.to_bytes(self.pub_key_id, 4)
        cert_data += int.to_bytes(self.pub_key_modulus, CertificateKeyLength[self.pub_key_type.name])
        if self.pub_key_type == CertificateKeyType.RSA_4096 or self.pub_key_type == CertificateKeyType.RSA_2048:
            cert_data += int.to_bytes(self.pub_key_exponent, 4)
        # Pad out the certificate data to a multiple of 64.
        cert_data = _pad_bytes(cert_data)
        return cert_data


class CertificateChain:
    """
    A CertificateChain object used to parse the chain of certificates stored in a WAD that are used for the Wii's
    content verification. The certificate chain is the format that the certificates are stored in as part of every WAD.

    Attributes
    ----------
    ca_cert: Certificate
        The CA certificate from the chain.
    tmd_cert: Certificate
        The CP (TMD) certificate from the chain.
    ticket_cert: Certificate
        The XS (Ticket) certificate from the chain.
    """
    def __init__(self):
        self.ca_cert: Certificate = Certificate()
        self.tmd_cert: Certificate = Certificate()
        self.ticket_cert: Certificate = Certificate()

    def load(self, cert_chain: bytes) -> None:
        """
        Loads certificate chain data into the CertificateChain object, allowing you to parse the individual
        certificates stored in the chain.

        Parameters
        ----------
        cert_chain: bytes
            The data for the certificate chain to load.
        """
        with (io.BytesIO(cert_chain) as cert_chain_data):
            # Read the two fields that denote different length sections of the certificate, so that we know how long
            # this certificate is in total.
            offset = 0x0
            for _ in range(3):
                cert_chain_data.seek(offset)
                cert_type = CertificateType.from_bytes(cert_chain_data.read(0x4))
                cert_chain_data.seek(offset + 0x80 + CertificateSignatureLength[cert_type.name].value)
                key_type = CertificateKeyType.from_bytes(cert_chain_data.read(0x4))
                cert_size = _align_value(0xC8 + CertificateSignatureLength[cert_type.name].value +
                                               CertificateKeyLength[key_type.name].value)
                cert_chain_data.seek(offset + 0x0)
                cert = Certificate()
                cert.load(cert_chain_data.read(cert_size))
                if cert.issuer == "Root":
                    self.ca_cert = cert
                elif cert.issuer.find("Root-CA") != -1:
                    if cert.child_name.find("CP") != -1:
                        self.tmd_cert = cert
                    elif cert.child_name.find("XS") != -1:
                        self.ticket_cert = cert
                    else:
                        raise ValueError("Unknown certificate in chain!")
                else:
                    raise ValueError("Unknown certificate in chain!")
                offset += cert_size

    def dump(self) -> bytes:
        """
        Dumps the full certificate chain back into bytes. This chain will always be formatted with the CA cert first,
        followed by the CP (TMD) cert, then finally the XS (Ticket) cert.

        Returns
        -------
        bytes
            The full certificate chain as bytes.
        """
        cert_chain_data = b''
        cert_chain_data += self.ca_cert.dump()
        cert_chain_data += self.tmd_cert.dump()
        cert_chain_data += self.ticket_cert.dump()
        return cert_chain_data


def verify_ca_cert(ca_cert: Certificate) -> bool:
    """
    Verify a Wii CA certificate using the root public key. The retail or development root key will be automatically
    selected based off of the name of the CA certificate provided.

    Parameters
    ----------
    ca_cert: Certificate
        The CA certificate to verify.

    Returns
    -------
    bool
        Whether the certificate is valid or not.
    """
    if ca_cert.issuer != "Root" or ca_cert.child_name.find("CA") == -1:
        raise ValueError("The provided certificate is not a CA certificate!")
    if ca_cert.child_name == "CA00000001":
        root_key_modulus = \
            (b'\xf8$lX\xba\xe7P\x03\x01\xfb\xb7\xc2\xeb\xe0\x01\x05q\xda\x92#x\xf0QN\xc0\x03\x1d\xd0\xd2\x1e\xd3\xd0~'
             b'\xfc\x85 i\xb5\xde\x9b\xb9Q\xa8\xbc\x90\xa2D\x92m7\x92\x95\xae\x946\xaa\xa6\xa3\x02Q\x0c{\x1d\xed\xd5'
             b'\xfb \x86\x9d\x7f0\x16\xf6\xbee\xd3\x83\xa1m\xb32\x1b\x955\x18\x90\xb1p\x02\x93~\xe1\x93\xf5~\x99\xa2GN'
             b'\x9d8$\xc7\xae\xe3\x85A\xf5g\xe7Q\x8cz\x0e8\xe7\xeb\xafA\x19\x1b\xcf\xf1{B\xa6\xb4\xed\xe6\xce\x8d\xe71'
             b'\x8f\x7fR\x04\xb3\x99\x0e"gE\xaf\xd4\x85\xb2D\x93\x00\x8b\x08\xc7\xf6\xb7\xe5k\x02\xb3\xe8\xfe\x0c\x9d'
             b'\x85\x9c\xb8\xb6\x82#\xb8\xab\'\xee_e8\x07\x8b-\xb9\x1e*\x15>\x85\x81\x80r\xa2;m\xd92\x81\x05Oo\xb0\xf6'
             b'\xf5\xad(>\xca\x0bz\xf3TU\xe0=\xa7\xb6\x83&\xf3\xec\x83J\xf3\x14\x04\x8a\xc6\xdf \xd2\x85\x08g<\xabb\xa2'
             b'\xc7\xbc\x13\x1aS>\x0bf\x80k\x1c0fK7#1\xbd\xc4\xb0\xca\xd8\xd1\x1e\xe7\xbb\xd9(UH\xaa\xec\x1ff\xe8!\xb3'
             b'\xc8\xa0Gi\x00\xc5\xe6\x88\xe8\x0c\xce<a\xd6\x9c\xbb\xa17\xc6`Ozr\xdd\x8c{>=Q)\r\xaajY{\x08\x1f\x9d63'
             b'\xa3Fz5a\t\xac\xa7\xdd}./\xb2\xc1\xae\xb8\xe2\x0fH\x92\xd8\xb9\xf8\xb4oN<\x11\xf4\xf4}\x8bu}\xfe\xfe\xa3'
             b'\x89\x9c3Y\\^\xfd\xeb\xcb\xab\xe8A>:\x9a\x80<i5n\xb2\xb2\xad\\\xc4\xc8XE^\xf5\xf7\xb3\x06D\xb4|d\x06\x8c'
             b'\xdf\x80\x9fv\x02Z-\xb4F\xe0=|\xf6/4\xe7\x02E{\x02\xa4\xcf]\x9d\xd5<\xa5:|\xa6)x\x8cg\xca\x08\xbf\xec'
             b'\xcaC\xa9W\xad\x16\xc9N\x1c\xd8u\xca\x10}\xce~\x01\x18\xf0\xdfk\xfe\xe5\x1d\xdb\xd9\x91\xc2n`\xcdHX\xaa'
             b'Y,\x82\x00u\xf2\x9fRl\x91|o\xe5@>\xa7\xd4\xa5\x0c\xec;s\x84\xde\x88n\x82\xd2\xebMNB\xb5\xf2\xb1I\xa8\x1e'
             b'\xa7\xceqD\xdc)\x94\xcf\xc4N\x1f\x91\xcb\xd4\x95')
    elif ca_cert.child_name == "CA00000002":
        root_key_modulus = \
            (b'\x00\xd0\x1f\xe1\x00\xd45V\xb2KV\xda\xe9q\xb5\xa5\xd3\x84\xb90\x03\xbe\x1b\xbf(\xa20[\x06\x06EF}[\x02Q'
             b'\xd2V\x1a\'O\x9e\x9f\x9c\xecdaP\xab=*\xe36hf\xac\xa4\xba\xe8\x1a\xe3\xd7\x9a\xa6\xb0J\x8b\xcb\xa7\xe6'
             b'\xfbd\x89E\xeb\xdf\xdb\x85\xba\t\x1f\xd7\xd1\x14\xb5\xa3\xa7\x80\xe3\xa2.n\xcd\x87\xb5\xa4\xc6\xf9\x10'
             b'\xe4\x03"\x08\x81K\x0c\xee\xa1\xa1}\xf79i_a~\xf65(\xdb\x94\x967\xa0V\x03\x7f{2A8\x95\xc0\xa8\xf1\x98.'
             b'\x15e\xe3\x8e\xed\xc2.Y\x0e\xe2g{\x86\t\xf4\x8c.0?\xbc@\\\xac\x18\x04/\x82 \x84\xe4\x93h\x03\xda\x7fA4'
             b'\x92HV+\x8e\xe1/x\xf8\x03$c0\xbc{\xe7\xeerJ\xf4X\xa4r\xe7\xabF\xa1\xa7\xc1\x0c/\x18\xfa\x07\xc3\xdd\xd8'
             b'\x98\x06\xa1\x1c\x9c\xc10\xb2G\xa3<\x8dG\xdeg\xf2\x9eUw\xb1\x1cCI=[\xbav4\xa7\xe4\xe7\x151\xb7\xdfY\x81'
             b'\xfe$\xa1\x14UL\xbd\x8f\x00\\\xe1\xdb5\x08\\\xcf\xc7x\x06\xb6\xde%@h\xa2l\xb5I-E\x80C\x8f\xe1\xe5\xa9'
             b'\xedu\xc5\xedE\x1d\xcex\x949\xcc\xc3\xba(\xa21*\x1b\x87\x19\xef\x0fs\xb7\x13\x95\x0c\x02Y\x1atb\xa6\x07'
             b'\xf3|\n\xa7\xa1\x8f\xa9C\xa3mu*_A\x92\xf0\x13a\x00\xaa\x9c\xb4\x1b\xbe\x14\xbe\xb1\xf9\xfci/\xdf\xa0\x94'
             b'F\xdeZ\x9d\xde,\xa5\xf6\x8c\x1c\x0c!B\x92\x87\xcb-\xaa\xa3\xd2cu/s\xe0\x9f\xafDy\xd2\x81t)\xf6\x98\x00'
             b'\xaf\xdekY-\xc1\x98\x82\xbd\xf5\x81\xcc\xab\xf2\xcb\x91\x02\x9e\xf3\\L\xfd\xbb\xffI\xc1\xfa\x1b/\xe3\x1d'
             b'\xe7\xa5`\xec\xb4~\xbc\xfe2B[\x95o\x81\xb6\x99\x17H~;x\x91Q\xdb.x\xb1\xfd.\xbe~bk>\xa1e\xb4\xfb\x00\xcc'
             b'\xb7Q\xafPs)\xc4\xa3\x93\x9e\xa6\xdd\x9cP\xa0\xe78k\x01EykA\xafa\xf7\x85U\x94O;\xc2-\xc3\xbd\r\x00\xf8y'
             b'\x8aB\xb1\xaa\xa0\x83 e\x9a\xc79Z\xb4\xf3)')
    else:
        raise ValueError("The provided CA certificate is not valid!")
    root_key_exponent = 0x00010001
    cert_hash = SHA1.new(ca_cert.dump()[576:])
    public_key = RSA.construct((int.from_bytes(root_key_modulus), root_key_exponent))
    try:
        pkcs1_15.new(public_key).verify(cert_hash, ca_cert.signature)
        return True
    except ValueError:
        return False


def verify_cert_sig(ca_cert: Certificate, target_cert: Certificate) -> bool:
    """
    Verify a TMD or Ticket certificate using a CA certificate.

    Parameters
    ----------
    ca_cert: Certificate
        The CA certificate to use for verification.
    target_cert: Certificate
        The target certificate to verify.

    Returns
    -------
    bool
        Whether the certificate's signature is valid or not.
    """
    if ca_cert.issuer != "Root" or ca_cert.child_name.find("CA") == -1:
        raise ValueError("The provided certificate is not a CA certificate!")
    # The issuer of the TMD/Ticket certs is Root-CA0000000X, so prepend "Root-" to the CA cert child name. If these
    # don't match, then there's probably a mismatch between retail and development certs.
    if f"Root-{ca_cert.child_name}" != target_cert.issuer:
        raise ValueError("The certificate you are trying to verify does not match the provided CA certificate!")
    cert_hash = SHA1.new(target_cert.dump()[320:])
    public_key = RSA.construct((ca_cert.pub_key_modulus, ca_cert.pub_key_exponent))
    try:
        pkcs1_15.new(public_key).verify(cert_hash, target_cert.signature)
        return True
    except ValueError:
        return False


def verify_tmd_sig(tmd_cert: Certificate, tmd: TMD) -> bool:
    """
    Verify the signature of a TMD file using a TMD certificate.

    Parameters
    ----------
    tmd_cert: Certificate
        The TMD certificate to use for verification.
    tmd: TMD
        The TMD to verify.

    Returns
    -------
    bool
        Whether the TMD's signature is valid or not.
    """
    if tmd_cert.issuer.find("Root-CA") == -1 or tmd_cert.child_name.find("CP") == -1:
        raise ValueError("The provided TMD certificate is not valid!")
    if f"{tmd_cert.issuer}-{tmd_cert.child_name}" != tmd.signature_issuer:
        raise ValueError("The signature you are trying to verify was not created with the provided TMD certificate!")
    tmd_hash = SHA1.new(tmd.dump()[320:])
    public_key = RSA.construct((tmd_cert.pub_key_modulus, tmd_cert.pub_key_exponent))
    try:
        pkcs1_15.new(public_key).verify(tmd_hash, tmd.signature)
        return True
    except ValueError:
        return False


def verify_ticket_sig(ticket_cert: Certificate, ticket: Ticket) -> bool:
    """
    Verify the signature of a Ticket file using a Ticket certificate.

    Parameters
    ----------
    ticket_cert: Certificate
        The Ticket certificate to use for verification.
    ticket: Ticket
        The Ticket to verify.

    Returns
    -------
    bool
        Whether the Ticket's signature is valid or not.
    """
    if ticket_cert.issuer.find("Root-CA") == -1 or ticket_cert.child_name.find("XS") == -1:
        raise ValueError("The provided Ticket certificate is not valid!")
    if f"{ticket_cert.issuer}-{ticket_cert.child_name}" != ticket.signature_issuer:
        raise ValueError("The signature you are trying to verify was not created with the provided Ticket certificate!")
    ticket_hash = SHA1.new(ticket.dump()[320:])
    public_key = RSA.construct((ticket_cert.pub_key_modulus, ticket_cert.pub_key_exponent))
    try:
        pkcs1_15.new(public_key).verify(ticket_hash, ticket.signature)
        return True
    except ValueError:
        return False
