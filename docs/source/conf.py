import os
import sys
from pathlib import Path

import configpile

project = "configpile"  # Name of the documented package
repository_url = f"https://github.com/denisrosset/{project}"
repository_branch = "main"
copyright = "2022, Denis Rosset"

sys.path.append(str(Path(__file__).parent.parent.parent / "examples"))

print(configpile.__version__)
# General stuff
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",  # Create neat summary tables
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "sphinx.ext.githubpages",
    "sphinx_autodoc_typehints",
    "sphinxcontrib.programoutput",
    "sphinx.ext.mathjax",
    "myst_nb",
    "sphinxarg.ext",
]

# Mappings for sphinx.ext.intersphinx. Projects have to have Sphinx-generated doc! (.inv file)
intersphinx_mapping = {
    "python": ("https://docs.python.org/3/", None),
}
autoclass_content = "class"  # Add __init__ doc (ie. params) to class summaries
html_show_sourcelink = False  # Remove 'view source code' from top of page (for html, not python)
autodoc_inherit_docstrings = True  # If no docstring, inherit from base class
autodoc_typehints = "signature"
autodoc_preserve_defaults = True  # does not work fully, but why not
set_type_checking_flag = True  # Enable 'expensive' imports for sphinx_autodoc_typehints
add_module_names = False  # Remove namespaces from class/method signatures
autosummary_generate = True  # Turn on sphinx.ext.autosummary
templates_path = ["_templates"]
autodoc_class_signature = "separated"
autodoc_member_order = "bysource"
simplify_optional_unions = False
napoleon_include_init_with_doc = True
napoleon_use_rtype = False
napoleon_use_admonition_for_examples = True
# napoleon_preprocess_types = True
napoleon_use_admonition_for_notes = True

napoleon_use_admonition_for_references = True

autodoc_type_aliases = {"Res": "configpile.userr.Res"}
# try:
#     __import__(project)
# except ImportError as error:
#     package_path = Path(__file__).resolve().parents[2]
#     sys.path.append(str(package_path))
#     try:
#         __import__(project)
#     except ImportError as error2:
#         warnings.warn(f"Could not import the {project} package")

# try:
#     __version__ = get_distribution(project).version
# except DistributionNotFound:
#     __version__ = "unknown version"


source_suffix = ".rst"
master_doc = "index"

# autodoc


# myst_nb
myst_enable_extensions = ["dollarmath", "colon_fence"]
jupyter_execute_notebooks = "force"
execution_timeout = -1

version = configpile.__version__
release = configpile.__version__

# HTML theme
html_theme = "sphinx_book_theme"
html_copy_source = True
html_show_sourcelink = True
html_sourcelink_suffix = ""
html_title = project
html_favicon = "_static/favicon.png"
html_static_path = ["_static"]
html_theme_options = {
    "path_to_docs": "docs",
    "repository_url": repository_url,
    "repository_branch": repository_branch,
    "use_edit_page_button": False,
    "use_issues_button": False,
    "use_repository_button": False,
    "use_download_button": False,
}