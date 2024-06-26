# Anatomy of a Title

Before we start working with titles, it's important to understand what components make up a title on the Wii, and how each of those components are handled in libWiiPy. If you're here, you likely already understand what a title is in the context of the Wii, but if not, [WiiBrew](https://wiibrew.org/wiki/Main_Page) is a great reference to learn more about the Wii's software.

:::{note}
"Title" can be used to refer to both digital titles preinstalled on the Wii and distributed via the Wii Shop Channel and system updates, as well as games released on discs. libWiiPy does not currently offer methods to interact with most data found on a game disc, so for all intents and purposes, "title" in this documentation is referring to digital titles only unless otherwise specified.
:::

There are three major components of a title: the **TMD**, the **Ticket**, and the **contents**. A brief summary of each is provided below.

## TMD
<project:#libWiiPy.title.tmd>

A **TMD** (**T**itle **M**eta**d**ata) contains basic information about a title, such as its Title ID, version, what IOS and version it's designed to run under, whether it's for the vWii or not, and more related information. The TMD also stores a list of content records that specify the index and ID of each content, as well as the SHA-1 hash of the decrypted content, to ensure that decryption was successful.

In libWiiPy, a TMD is represented by a `TMD()` object, which is part of the `tmd` module in the `title` subpackge, and is imported automatically. A content record is represented by its own `ContentRecord()` object, which is a private class designed to only be used by other modules.

## Ticket
<project:#libWiiPy.title.ticket>

A **Ticket** primarily contains the encrypted Title Key for a title, as well as the information required to decrypt that key. They come in two forms: common tickets, which are freely available from the Nintendo Update Servers, and personalized tickets, which are issued to your console specifically by the Wii Shop Channel (or at least they were before it closed, excluding the free titles still available).

In libWiiPy, a Ticket is represented by a `Ticket()` object, which is part of the `ticket` module in the `title` subpackage, and is imported automatically.

## Content
<project:#libWiiPy.title.content>

**Contents** are the files in a title that contain the actual data, whether that be the main executable or resources required by it. They're usually stored encrypted in a WAD file or on the Nintendo Update Servers, until they are decrypted during installation to a console. The Title Key stored in the Ticket is required to decrypt the contents of a title. Each content has a matching record with its index and Content ID, as well as the SHA-1 hash of its decrypted data. These records are stored in the TMD.

In libWiiPy, contents are represented by a `ContentRegion()` object, which is part of the `content` module in the `title` subpackge, and is imported automatically. A content record is represented by its own `ContentRecord()` object, which is a private class designed to only be used by other modules.
