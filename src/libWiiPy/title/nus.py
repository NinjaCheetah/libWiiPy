# "title/nus.py" from libWiiPy by NinjaCheetah & Contributors
# https://github.com/NinjaCheetah/libWiiPy
#
# See https://wiibrew.org/wiki/NUS for details about the NUS

import requests
import hashlib
from typing import List
from .title import Title
from .tmd import TMD
from .ticket import Ticket

_nus_endpoint = ["http://nus.cdn.shop.wii.com/ccs/download/", "http://ccs.cdn.wup.shop.nintendo.net/ccs/download/"]


def download_title(title_id: str, title_version: int = None, wiiu_endpoint: bool = False) -> Title:
    """
    Download an entire title and all of its contents, then load the downloaded components into a Title object for
    further use. This method is NOT recommended for general use, as it has absolutely no verbosity. It is instead
    recommended to call the individual download methods instead to provide more flexibility and output.

    Parameters
    ----------
    title_id : str
        The Title ID of the title to download.
    title_version : int, option
        The version of the title to download. Defaults to latest if not set.
    wiiu_endpoint : bool, option
        Whether the Wii U endpoint for the NUS should be used or not. This increases download speeds. Defaults to False.

    Returns
    -------
    Title
        A Title object containing all the data from the downloaded title.
    """
    # First, create the new title.
    title = Title()
    # Download and load the TMD, Ticket, and certs.
    title.load_tmd(download_tmd(title_id, title_version, wiiu_endpoint))
    title.load_ticket(download_ticket(title_id, wiiu_endpoint))
    title.wad.set_cert_data(download_cert(wiiu_endpoint))
    # Download all contents
    title.load_content_records()
    title.content.content_list = download_contents(title_id, title.tmd, wiiu_endpoint)
    # Return the completed title.
    return title


def download_tmd(title_id: str, title_version: int = None, wiiu_endpoint: bool = False) -> bytes:
    """
    Downloads the TMD of the Title specified in the object. Will download the latest version by default, or another
    version if it was manually specified in the object.

    Parameters
    ----------
    title_id : str
        The Title ID of the title to download the TMD for.
    title_version : int, option
        The version of the TMD to download. Defaults to latest if not set.
    wiiu_endpoint : bool, option
        Whether the Wii U endpoint for the NUS should be used or not. This increases download speeds. Defaults to False.

    Returns
    -------
    bytes
        The TMD file from the NUS.
    """
    # Build the download URL. The structure is download/<TID>/tmd for latest and download/<TID>/tmd.<version> for
    # when a specific version is requested.
    if wiiu_endpoint is False:
        tmd_url = _nus_endpoint[0] + title_id + "/tmd"
    else:
        tmd_url = _nus_endpoint[1] + title_id + "/tmd"
    # Add the version to the URL if one was specified.
    if title_version is not None:
        tmd_url += "." + str(title_version)
    # Make the request.
    tmd_request = requests.get(url=tmd_url, headers={'User-Agent': 'wii libnup/1.0'}, stream=True)
    # Handle a 404 if the TID/version doesn't exist.
    if tmd_request.status_code != 200:
        raise ValueError("The requested Title ID or TMD version does not exist. Please check the Title ID and Title"
                         " version and then try again.")
    # Save the raw TMD.
    raw_tmd = tmd_request.content
    # Use a TMD object to load the data and then return only the actual TMD.
    tmd_temp = TMD()
    tmd_temp.load(raw_tmd)
    tmd = tmd_temp.dump()
    return tmd


def download_ticket(title_id: str, wiiu_endpoint: bool = False) -> bytes:
    """
    Downloads the Ticket of the Title specified in the object. This will only work if the Title ID specified is for
    a free title.

    Parameters
    ----------
    title_id : str
        The Title ID of the title to download the Ticket for.
    wiiu_endpoint : bool, option
        Whether the Wii U endpoint for the NUS should be used or not. This increases download speeds. Defaults to False.

    Returns
    -------
    bytes
        The Ticket file from the NUS.
    """
    # Build the download URL. The structure is download/<TID>/cetk, and cetk will only exist if this is a free
    # title.
    if wiiu_endpoint is False:
        ticket_url = _nus_endpoint[0] + title_id + "/cetk"
    else:
        ticket_url = _nus_endpoint[1] + title_id + "/cetk"
    # Make the request.
    ticket_request = requests.get(url=ticket_url, headers={'User-Agent': 'wii libnup/1.0'}, stream=True)
    if ticket_request.status_code != 200:
        raise ValueError("The requested Title ID does not exist, or refers to a non-free title. Tickets can only"
                         " be downloaded for titles that are free on the NUS.")
    # Save the raw cetk file.
    cetk = ticket_request.content
    # Use a Ticket object to load only the Ticket data from cetk and return it.
    ticket_temp = Ticket()
    ticket_temp.load(cetk)
    ticket = ticket_temp.dump()
    return ticket


def download_cert(wiiu_endpoint: bool = False) -> bytes:
    """
    Downloads the signing certificate used by all WADs. This uses System Menu 4.3U as the source.

    Parameters
    ----------
    wiiu_endpoint : bool, option
        Whether the Wii U endpoint for the NUS should be used or not. This increases download speeds. Defaults to False.

    Returns
    -------
    bytes
        The cert file.
    """
    # Download the TMD and cetk for the System Menu 4.3U.
    if wiiu_endpoint is False:
        tmd_url = _nus_endpoint[0] + "0000000100000002/tmd.513"
        cetk_url = _nus_endpoint[0] + "0000000100000002/cetk"
    else:
        tmd_url = _nus_endpoint[1] + "0000000100000002/tmd.513"
        cetk_url = _nus_endpoint[1] + "0000000100000002/cetk"
    tmd = requests.get(url=tmd_url, headers={'User-Agent': 'wii libnup/1.0'}, stream=True).content
    cetk = requests.get(url=cetk_url, headers={'User-Agent': 'wii libnup/1.0'}, stream=True).content
    # Assemble the certificate.
    cert = b''
    # Certificate Authority data.
    cert += cetk[0x2A4 + 768:]
    # Certificate Policy data.
    cert += tmd[0x328:0x328 + 768]
    # XS data.
    cert += cetk[0x2A4:0x2A4 + 768]
    # Since the cert is always the same, check the hash to make sure nothing went wildly wrong.
    if hashlib.sha1(cert).hexdigest() != "ace0f15d2a851c383fe4657afc3840d6ffe30ad0":
        raise Exception("An unknown error has occurred downloading and creating the certificate.")
    return cert


def download_content(title_id: str, content_id: int, wiiu_endpoint: bool = False) -> bytes:
    """
    Downloads a specified content for the title specified in the object.

    Parameters
    ----------
    title_id : str
        The Title ID of the title to download content from.
    content_id : int
        The Content ID of the content you wish to download.
    wiiu_endpoint : bool, option
        Whether the Wii U endpoint for the NUS should be used or not. This increases download speeds. Defaults to False.

    Returns
    -------
    bytes
        The downloaded content.
    """
    # Build the download URL. The structure is download/<TID>/<Content ID>.
    content_id_hex = hex(content_id)[2:]
    if len(content_id_hex) < 2:
        content_id_hex = "0" + content_id_hex
    if wiiu_endpoint is False:
        content_url = _nus_endpoint[0] + title_id + "/000000" + content_id_hex
    else:
        content_url = _nus_endpoint[1] + title_id + "/000000" + content_id_hex
    # Make the request.
    content_request = requests.get(url=content_url, headers={'User-Agent': 'wii libnup/1.0'}, stream=True)
    if content_request.status_code != 200:
        raise ValueError("The requested Title ID does not exist, or an invalid Content ID is present in the"
                         " content records provided.\n Failed while downloading Content ID: 000000" +
                         content_id_hex)
    content_data = content_request.content
    return content_data


def download_contents(title_id: str, tmd: TMD, wiiu_endpoint: bool = False) -> List[bytes]:
    """
    Downloads all the contents for the title specified in the object. This requires a TMD to already be available
    so that the content records can be accessed.

    Parameters
    ----------
    title_id : str
        The Title ID of the title to download content from.
    tmd : TMD
        The TMD that matches the title that the contents being downloaded are from.
    wiiu_endpoint : bool, option
        Whether the Wii U endpoint for the NUS should be used or not. This increases download speeds. Defaults to False.

    Returns
    -------
    List[bytes]
        A list of all the downloaded contents.
    """
    # Retrieve the content records from the TMD.
    content_records = tmd.content_records
    # Create a list of Content IDs to download.
    content_ids = []
    for content_record in content_records:
        content_ids.append(content_record.content_id)
    # Iterate over that list and download each content in it, then add it to the array of contents.
    content_list = []
    for content_id in content_ids:
        # Call self.download_content() for each Content ID.
        content = download_content(title_id, content_id, wiiu_endpoint)
        content_list.append(content)
    return content_list
