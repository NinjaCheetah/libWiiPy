# Extracting Titles from WAD Files

One of the most common uses for libWiiPy's title subpackage is extracting WAD files so that you can edit their contents. This can open up the doors to modding, like with the [famous DVD image](https://ncxprogramming.com/2023/06/19/wii-dvd-p3.html) in the Wii Menu that actually kicked this project off, or other projects like datamining.

:::{note}
This guide assumes that you already have a WAD file that you'd like to extract, and that this WAD file doesn't use a personalized ticket, as titles with personalized tickets are not as easy to manipulate. WADs like that aren't very common, as most WADs created from the NUS, dumped from a console, or obtained via other methods will not have this type of ticket, so if in doubt, it will probably work fine.

If you don't currently have a WAD file, you may want to skip ahead to <project:#/titles/nus-downloading> first to obtain one for a free title first.
:::

:::{hint}
If you've gotten here, but you're just looking for a tool to do all of this rather than a guide on how to write your own code, you're probably looking for something like [WiiPy](https://github.com/NinjaCheetah/WiiPy). WiiPy is a command line tool that covers all of libWiiPy's features, and is also made by NinjaCheetah.
:::

With all of that out of the way, let's begin!

## Loading the WAD

The first thing we'll do is import libWiiPy and load up our file:
```pycon
>>> import libWiiPy
>>> wad_data = open("file.wad").read()
>>>
```

Then, we can create a new WAD object, and load our data into it:
```pycon
>>> wad = libWiiPy.title.WAD()
>>> wad.load(wad_data)
>>>
```

And viola! We have a WAD object that we can use to get each separate part of our title.

## Picking the WAD Apart

Now that we have our WAD loaded, we need to separate it out into its components. On top of the parts we already established, a WAD also contains a certificate chain, which is used by IOS during official title installations to ensure that a title was signed by Nintendo, and potentially two more areas called the footer and the CRL. Footers aren't a necessary part of a WAD, and when they do exist, they typically only contain the build timestamp and the machine it was built on. CRLs are even less common, and have never actually been found inside any WAD, but we know they exist because of things we've seen that Nintendo would really rather we hadn't. Certificate chains also have a class that we'll cover after the main three components, but the latter two components don't have data we can edit, so they're only ever represented as bytes and do not have their own classes.

### The TMD

To get the TMD, let's create a new TMD object, and then use the method `get_tmd_data()` on our WAD object as the source for our TMD data:
```pycon
>>> tmd = libWiiPy.title.TMD()
>>> tmd.load(wad.get_tmd_data())
>>>
```

And now, just like in our <project:#/usage/getting-started> tutorial, we have a TMD object, and can get all the same data from it!

### The Ticket

Next up, we need to get the Ticket. The process for getting the Ticket is very similar to getting the TMD. We'll create a new Ticket object, and then use the method `get_ticket_data()` to get the data:
```pycon
>>> ticket = libWiiPy.title.Ticket()
>>> ticket.load(wad.get_ticket_data())
>>>
```

Similarly to the TMD, we can use this Ticket object to get all the properties of a Ticket. This includes getting the decrypted version of the Ticket's encrypted Title Key. In fact, why don't we do that know?

We can use a Ticket's `get_title_key()` method to decrypt the Title Key and return it. This uses the Ticket's `title_key_enc`, `common_key_index`, and `title_id` properties to get the IV and common key required to decrypt the Title Key.

```pycon
>>> title_key = ticket.get_title_key()
>>>
```

:::{danger}
If the Ticket contained in your WAD is personalized, this Title Key will be invalid! `get_title_key()` won't return any error, as it has no way of validating the output, but the key will not work to decrypt any content.
:::

### The Contents

Now that we have our TMD and Ticket extracted, we can get to work on extracting and decrypting the content. 

First, we'll need to create a new ContentRegion object, which requires sourcing the raw data of all the WAD's contents (which are stored as one continuous block) using `get_content_data()`, as well as the content records found in our TMD object. We can do this like so:

```pycon
>>> content_region = libWiiPy.title.ContentRegion()
>>> content_region.load(wad.get_content_data(), tmd.content_records)
>>>
```

The content records from the TMD are used by the `content` module to parse the block of data that the contents are stored in so that they can be separated back out into individual files. Speaking of which, let's try extracting one (still in its encrypted form, for now) just to make sure everything is working. For this example, we'll use `get_enc_content_by_index()`, and get the content at index 0:

```pycon
>>> encrypted_content = content_region.get_enc_content_by_index(0)
>>>
```

As long as that's all good, that means our WAD's content has successfully been parsed, and we can start decrypting it!

Let's try getting the same content again, the one at index 0, but this time in its decrypted form. We can use the method `get_content_by_index()` for this, which takes the index of the content we want, and the Title Key that we saved in the last step.
```pycon
>>> decrypted_content = content_region.get_content_by_index(0, title_key)
>>>
```

:::{error}
If you get an error here saying that the hash of your decrypted content doesn't match the expected hash, then something has gone wrong. There are several possibilities, including your Ticket being personalized, causing you to get an invalid Title Key, your WAD having mismatched data, or your content being modified without the hash in the content record having been updated.
:::

If you don't get any errors, then congratulations! You've just extracted your first decrypted content from a WAD!

Now that we know things are working, why don't we speed things up a little by using the content region's `get_contents()` method, which will return a list of all the decrypted content:
```pycon
>>> decrypted_content_list = content_region.get_contents(title_key)
>>>
```

And just like that, we have our TMD, Ticket, and decrypted content all extracted! From here, what you do with them is up to you and whatever program you're working on. For example, to make a simple WAD extractor, you may want to write all these files to an output directory.

### The Certificate Chain

As mentioned at the start of this guide, WADs also contain a certificate chain. We don't necessarily need this data right now, but getting it is very similar to the other components:
```pycon
>>> certificate_chain = libWiiPy.title.CertificateChain()
>>> certificate_chain.load(wad.get_cert_data())
>>>
```

### The Other Data

Also mentioned earlier in this guide, WADs may contain two additional regions of data know as the footer (or "meta"), and the CRL. The procedure for extracting all of these is pretty simple, and follows the same formula as any other data in a WAD:
```pycon
>>> footer = wad.get_meta_data()
>>> crl = wad.get_crl_data()
>>>
```

Beyond getting their raw data, there isn't anything you can directly do with these components with libWiiPy. If one of these components doesn't exist, libWiiPy will simply return an empty bytes object.

:::{note}
Managed to find a WAD somewhere with CRL data? I'd love to hear more, so feel free to email me at [ninjacheetah@ncxprogramming.com](mailto:ninjacheetah@ncxprogramming.com).
:::

<hr>

Now, that might all seem a bit complicated. What if instead there was a way to manage a title using one object that handles all the individual components for you? Well, you're in luck! On top of the fairly low-level way to extract a WAD provided in this guide, libWiiPy also offers a higher-level method through the <project:#libWiiPy.title.title> module. On the next page, we'll dive into the specifics, and how to use this module.
