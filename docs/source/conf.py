# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

from datetime import date

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'libWiiPy'
copyright = f'{date.today().year}, NinjaCheetah & Contributors'
author = 'NinjaCheetah & Contributors'
version = 'main'
release = 'main'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ['myst_parser', 'sphinx.ext.napoleon', 'sphinx_copybutton', 'sphinx_tippy', 'sphinx_design']

templates_path = ['_templates']
exclude_patterns = ["Thumbs.db", ".DS_Store"]

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_book_theme'
html_static_path = ['_static']
html_logo = "banner.png"
html_title = "libWiiPy API Docs"
html_theme_options = {
    "repository_url": "https://github.com/NinjaCheetah/libWiiPy",
    "use_repository_button": True
}

# MyST Configuration

myst_enable_extensions = ['colon_fence', 'deflist']
