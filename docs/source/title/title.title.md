# libWiiPy.title.title Module

## Description

The `libWiiPy.title.title` module provides a high-level interface for handling all the components of a digital Wii title through one class. It allows for directly importing a WAD, and will automatically extract the various components and load them into their appropriate classes. Additionally, it provides duplicates of some methods found in those classes that require fewer arguments, as it has the context of the other components and is able to retrieve additional data automatically.

An example of that idea can be seen with the method `get_content_by_index()`. In its original definition, which can be seen at <project:#libWiiPy.title.content.ContentRegion.get_content_by_index>, you are required to supply the Title Key for the title that the content is sourced from. In contrast, when using <project:#libWiiPy.title.title.Title.get_content_by_index>, you do not need to supply a Title Key, as the Title object already has the context of the Ticket and can retrieve the Title Key from it automatically. In a similar vein, this module provides the easiest route for verifying that a title is legitimately signed by Nintendo. The method <project:#libWiiPy.title.title.Title.get_is_signed> is able to access the entire certificate chain, the TMD, and the Ticket, and is therefore able to verify all components of the title by itself.

Because using <project:#libWiiPy.title.title.Title> allows many operations to be much simpler than if you manage the components separately, it's generally recommended to use it whenever possible.

## Module Contents

```{eval-rst}
.. automodule:: libWiiPy.title.title
   :members:
   :undoc-members:
```
