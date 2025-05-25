# "title/nus.py" from libWiiPy by NinjaCheetah & Contributors
# https://github.com/NinjaCheetah/libWiiPy
#
# See https://wiibrew.org/wiki/NUS for details about the NUS

import requests
#import hashlib
from typing import Any, List, Protocol
#from urllib.parse import urlparse as _urlparse
from .title import Title
from .tmd import TMD
from .ticket import Ticket

_nus_endpoint = ["http://nus.cdn.shop.wii.com/ccs/download/", "http://ccs.cdn.wup.shop.nintendo.net/ccs/download/"]


class DownloadCallback(Protocol):
    """
    The format of a callable passed to a NUS download function.
    """
    def __call__(self, done: int, total: int) -> Any:
        """
        This function will be called with the current number of bytes downloaded and the total size of the file being
        downloaded.

        Parameters
        ----------
        done : int
            The number of bytes already downloaded.
        total : int
            The total size of the file being downloaded.
        """
        ...


def download_title(title_id: str, title_version: int = None, wiiu_endpoint: bool = False,
                   endpoint_override: str = None, progress: DownloadCallback = lambda done, total: None) -> Title:
    """
    Download an entire title and all of its contents, then load the downloaded components into a Title object for
    further use. This method is NOT recommended for general use, as it has extremely limited verbosity. It is instead
    recommended to call the individual download methods instead to provide more flexibility and output.

    Be aware that you will receive fairly vague feedback from this function if you attach a progress callback. The
    callback will be connected to each of the individual functions called by this function, but there will be no
    indication of which function is currently running, just the progress of its download.

    Parameters
    ----------
    title_id : str
        The Title ID of the title to download.
    title_version : int, optional
        The version of the title to download. Defaults to latest if not set.
    wiiu_endpoint : bool, optional
        Whether the Wii U endpoint for the NUS should be used or not. This increases download speeds. Defaults to False.
    endpoint_override: str, optional
        A custom endpoint URL to use instead of the standard Wii or Wii U endpoints. Defaults to no override, and if
        set entirely overrides the "wiiu_endpoint" parameter.
    progress: DownloadCallback, optional
        A callback function used to return the progress of the downloads. The provided callable must match the signature
        defined in DownloadCallback.

    Returns
    -------
    Title
        A Title object containing all the data from the downloaded title.

    See Also
    --------
    libWiiPy.title.nus.DownloadCallback
    """
    # First, create the new title.
    title = Title()
    # Download and load the certificate chain, TMD, and Ticket.
    title.load_cert_chain(download_cert_chain(wiiu_endpoint, endpoint_override))
    title.load_tmd(download_tmd(title_id, title_version, wiiu_endpoint, endpoint_override, progress))
    title.load_ticket(download_ticket(title_id, wiiu_endpoint, endpoint_override, progress))
    # Download all contents
    title.load_content_records()
    title.content.content_list = download_contents(title_id, title.tmd, wiiu_endpoint, endpoint_override, progress)
    # Return the completed title.
    return title


def download_tmd(title_id: str, title_version: int = None, wiiu_endpoint: bool = False,
                 endpoint_override: str = None, progress: DownloadCallback = lambda done, total: None) -> bytes:
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
    endpoint_override: str, optional
        A custom endpoint URL to use instead of the standard Wii or Wii U endpoints. Defaults to no override, and if
        set entirely overrides the "wiiu_endpoint" parameter.
    progress: DownloadCallback, optional
        A callback function used to return the progress of the download. The provided callable must match the signature
        defined in DownloadCallback.

    Returns
    -------
    bytes
        The TMD file from the NUS.

    See Also
    --------
    libWiiPy.title.nus.DownloadCallback
    """
    # Build the download URL. The structure is download/<TID>/tmd for latest and download/<TID>/tmd.<version> for
    # when a specific version is requested.
    if endpoint_override is not None:
        endpoint_url = _validate_endpoint(endpoint_override)
    else:
        if wiiu_endpoint:
            endpoint_url = _nus_endpoint[1]
        else:
            endpoint_url = _nus_endpoint[0]
    tmd_url = endpoint_url + title_id + "/tmd"
    # Add the version to the URL if one was specified.
    if title_version is not None:
        tmd_url += "." + str(title_version)
    # Make the request.
    try:
        response = requests.get(url=tmd_url, headers={'User-Agent': 'wii libnup/1.0'}, stream=True)
    except requests.exceptions.ConnectionError:
        if endpoint_override:
            raise ValueError("A connection could not be made to the NUS endpoint. Please make sure that your endpoint "
                             "override is valid.")
        else:
            raise Exception("A connection could not be made to the NUS endpoint. The NUS may be unavailable.")
    # Handle a 404 if the TID/version doesn't exist.
    if response.status_code != 200:
        raise ValueError("The requested Title ID or TMD version does not exist. Please check the Title ID and Title"
                         " version and then try again.")
    total_size = int(response.headers["Content-Length"])
    progress(0, total_size)
    # Stream the TMD's data in chunks so that we can post updates to the callback function (assuming one was supplied).
    raw_tmd = b""
    for chunk in response.iter_content(512):
        raw_tmd += chunk
        progress(len(raw_tmd), total_size)
    # Use a TMD object to load the data and then return only the actual TMD.
    tmd_temp = TMD()
    tmd_temp.load(raw_tmd)
    tmd = tmd_temp.dump()
    return tmd


def download_ticket(title_id: str, wiiu_endpoint: bool = False, endpoint_override: str = None,
                    progress: DownloadCallback = lambda done, total: None) -> bytes:
    """
    Downloads the Ticket of the Title specified in the object. This will only work if the Title ID specified is for
    a free title.

    Parameters
    ----------
    title_id : str
        The Title ID of the title to download the Ticket for.
    wiiu_endpoint : bool, option
        Whether the Wii U endpoint for the NUS should be used or not. This increases download speeds. Defaults to False.
    endpoint_override: str, optional
        A custom endpoint URL to use instead of the standard Wii or Wii U endpoints. Defaults to no override, and if
        set entirely overrides the "wiiu_endpoint" parameter.
    progress: DownloadCallback, optional
        A callback function used to return the progress of the download. The provided callable must match the signature
        defined in DownloadCallback.

    Returns
    -------
    bytes
        The Ticket file from the NUS.

    See Also
    --------
    libWiiPy.title.nus.DownloadCallback
    """
    # Build the download URL. The structure is download/<TID>/cetk, and cetk will only exist if this is a free
    # title.
    if endpoint_override is not None:
        endpoint_url = _validate_endpoint(endpoint_override)
    else:
        if wiiu_endpoint:
            endpoint_url = _nus_endpoint[1]
        else:
            endpoint_url = _nus_endpoint[0]
    ticket_url = endpoint_url + title_id + "/cetk"
    # Make the request.
    try:
        response = requests.get(url=ticket_url, headers={'User-Agent': 'wii libnup/1.0'}, stream=True)
    except requests.exceptions.ConnectionError:
        if endpoint_override:
            raise ValueError("A connection could not be made to the NUS endpoint. Please make sure that your endpoint "
                             "override is valid.")
        else:
            raise Exception("A connection could not be made to the NUS endpoint. The NUS may be unavailable.")
    if response.status_code != 200:
        raise ValueError("The requested Title ID does not exist, or refers to a non-free title. Tickets can only"
                         " be downloaded for titles that are free on the NUS.")
    total_size = int(response.headers["Content-Length"])
    progress(0, total_size)
    # Stream the Ticket's data just like with the TMD.
    cetk = b""
    for chunk in response.iter_content(chunk_size=1024):
        cetk += chunk
        progress(len(cetk), total_size)
    # Use a Ticket object to load only the Ticket data from cetk and return it.
    ticket_temp = Ticket()
    ticket_temp.load(cetk)
    ticket = ticket_temp.dump()
    return ticket


def download_cert_chain(wiiu_endpoint: bool = False, endpoint_override: str = None) -> bytes:
    """
    Downloads the signing certificate chain used by all WADs. This uses System Menu 4.3U as the source.

    Parameters
    ----------
    wiiu_endpoint : bool, option
        Whether the Wii U endpoint for the NUS should be used or not. This increases download speeds. Defaults to False.
    endpoint_override: str, optional
        A custom endpoint URL to use instead of the standard Wii or Wii U endpoints. Defaults to no override, and if
        set entirely overrides the "wiiu_endpoint" parameter.

    Returns
    -------
    bytes
        The cert file.
    """
    # Download the TMD and cetk for System Menu 4.3U (v513).
    if endpoint_override is not None:
        endpoint_url = _validate_endpoint(endpoint_override)
    else:
        if wiiu_endpoint:
            endpoint_url = _nus_endpoint[1]
        else:
            endpoint_url = _nus_endpoint[0]
    tmd_url = endpoint_url + "0000000100000002/tmd.513"
    cetk_url = endpoint_url + "0000000100000002/cetk"
    try:
        tmd = requests.get(url=tmd_url, headers={'User-Agent': 'wii libnup/1.0'}, stream=True).content
        cetk = requests.get(url=cetk_url, headers={'User-Agent': 'wii libnup/1.0'}, stream=True).content
    except requests.exceptions.ConnectionError:
        if endpoint_override:
            raise ValueError("A connection could not be made to the NUS endpoint. Please make sure that your endpoint "
                             "override is valid.")
        else:
            raise Exception("A connection could not be made to the NUS endpoint. The NUS may be unavailable.")
    # Assemble the certificate chain.
    cert_chain = b''
    # Certificate Authority data.
    cert_chain += cetk[0x2A4 + 768:]
    # Certificate Policy (TMD certificate) data.
    cert_chain += tmd[0x328:0x328 + 768]
    # XS (Ticket certificate) data.
    cert_chain += cetk[0x2A4:0x2A4 + 768]
    # Since the cert chain is always the same, check the hash to make sure nothing went wildly wrong.
    # This is currently disabled because of the possibility that one may be downloading non-retail certs (gasp!).
    #if hashlib.sha1(cert_chain).hexdigest() != "ace0f15d2a851c383fe4657afc3840d6ffe30ad0":
    #    raise Exception("An unknown error has occurred downloading and creating the certificate.")
    return cert_chain


def download_content(title_id: str, content_id: int, wiiu_endpoint: bool = False,
                     endpoint_override: str = None, progress: DownloadCallback = lambda done, total: None) -> bytes:
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
    endpoint_override: str, optional
        A custom endpoint URL to use instead of the standard Wii or Wii U endpoints. Defaults to no override, and if
        set entirely overrides the "wiiu_endpoint" parameter.
    progress: DownloadCallback, optional
        A callback function used to return the progress of the download. The provided callable must match the signature
        defined in DownloadCallback.

    Returns
    -------
    bytes
        The downloaded content.

    See Also
    --------
    libWiiPy.title.nus.DownloadCallback
    """
    # Build the download URL. The structure is download/<TID>/<Content ID>.
    content_id_hex = hex(content_id)[2:]
    if len(content_id_hex) < 2:
        content_id_hex = "0" + content_id_hex
    if endpoint_override is not None:
        endpoint_url = _validate_endpoint(endpoint_override)
    else:
        if wiiu_endpoint:
            endpoint_url = _nus_endpoint[1]
        else:
            endpoint_url = _nus_endpoint[0]
    content_url = endpoint_url + title_id + "/000000" + content_id_hex
    # Make the request.
    try:
        response = requests.get(url=content_url, headers={'User-Agent': 'wii libnup/1.0'}, stream=True)
    except requests.exceptions.ConnectionError:
        if endpoint_override:
            raise ValueError("A connection could not be made to the NUS endpoint. Please make sure that your endpoint "
                             "override is valid.")
        else:
            raise Exception("A connection could not be made to the NUS endpoint. The NUS may be unavailable.")
    if response.status_code != 200:
        raise ValueError("The requested Title ID does not exist, or an invalid Content ID is present in the"
                         " content records provided.\n Failed while downloading Content ID: 000000" +
                         content_id_hex)
    total_size = int(response.headers["Content-Length"])
    progress(0, total_size)
    # Stream the content just like the TMD/Ticket.
    content = b""
    for chunk in response.iter_content(chunk_size=1024):
        content += chunk
        progress(len(content), total_size)
    return content


def download_contents(title_id: str, tmd: TMD, wiiu_endpoint: bool = False, endpoint_override: str = None,
                      progress: DownloadCallback = lambda done, total: None) -> List[bytes]:
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
    endpoint_override: str, optional
        A custom endpoint URL to use instead of the standard Wii or Wii U endpoints. Defaults to no override, and if
        set entirely overrides the "wiiu_endpoint" parameter.
    progress: DownloadCallback, optional
        A callback function used to return the progress of the downloads. The provided callable must match the signature
        defined in DownloadCallback.

    Returns
    -------
    List[bytes]
        A list of all the downloaded contents.

    See Also
    --------
    libWiiPy.title.nus.DownloadCallback
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
        content = download_content(title_id, content_id, wiiu_endpoint, endpoint_override, progress)
        content_list.append(content)
    return content_list


def _validate_endpoint(endpoint: str) -> str:
    """
    Validate the provided NUS endpoint URL and append the required path if necessary.

    Parameters
    ----------
    endpoint: str
        The NUS endpoint URL to validate.

    Returns
    -------
    str
        The validated NUS endpoint with the proper path.
    """
    # Find the root of the URL and then assemble the correct URL based on that.
    # TODO: Rewrite in a way that makes more sense and un-stub
    #new_url = _urlparse(endpoint)
    #if new_url.netloc == "":
    #    endpoint_url = "http://" + new_url.path + "/ccs/download/"
    #else:
    #    endpoint_url = "http://" + new_url.netloc + "/ccs/download/"
    return endpoint
