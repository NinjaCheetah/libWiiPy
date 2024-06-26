# Getting Started
Once you have libWiiPy installed, it's time to write your first code!

As an example, let's say you have a TMD file with a generic name, `title.tmd`, and because of this you need to find out some information about it, so you know what title it belongs to.

First off, let's import `libWiiPy`, and load up our file:
```pycon
>>> import libWiiPy
>>> tmd_file = open("title.tmd", "rb").read()
>>>
```

Then we'll create a new TMD object, and load our file into it:
```pycon
>>> tmd = libWiiPy.title.TMD()
>>> tmd.load(tmd_file)
>>>
```

And ta-da! We now have a new TMD object that can be used to find out whatever we need to know about this TMD.

So, to find out what title this TMD is for, let's try looking at the TMD's `title_id` property, like this:
```pycon
>>> print(tmd.title_id)
0000000100000002

>>>
```

Aha! `0000000100000002`! That means this TMD belongs to the Wii Menu. But what version? Well, we can use the TMD's `title_version` property to check, like so:
```pycon
>>> print(tmd.title_version)
513

>>>
```

513! So now we know that this TMD is from the Wii Menu, and is version 513, which is the version number used for v4.3U.

So now you know how to identify what title and version a TMD file is from! But, realistically, trying to identify a lone unlabeled TMD file is not something you'll ever really need to do, either in your day-to-day life or in whatever program you're developing. In the next chapter, we'll dive in to working with more components of a title, which is a lot more useful for programs that need to manipulate them.

The full documentation on the TMD class can be found here: <project:#libWiiPy.title.tmd>
