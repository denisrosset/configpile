import warnings

from pkg_resources import DistributionNotFound, get_distribution
import sys
from pathlib import Path

project = 'configpile' # Name of the documented package
repository_url = f"https://github.com/denisrosset/{project}"
repository_branch = 'main'
copyright = "2022, Denis Rosset"


# General stuff
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.githubpages",
    "sphinx_autodoc_typehints",
    "sphinx.ext.intersphinx",
    "sphinx.ext.mathjax",
    "myst_nb",
]


try:
    __import__(project)
except ImportError as error:
    package_path = Path(__file__).resolve().parents[2]
    sys.path.append(str(package_path))
    try:
        __import__(project)
    except ImportError as error2:
        warnings.warn(f"Could not import the {project} package")

try:
    __version__ = get_distribution(project).version
except DistributionNotFound:
    __version__ = "unknown version"

source_suffix = ".rst"
master_doc = "index"

# myst_nb
myst_enable_extensions = ["dollarmath", "colon_fence"]
jupyter_execute_notebooks = "force"
execution_timeout = -1

version = __version__
release = __version__
#exclude_patterns = ["_build", "notebooks/build", "notebooks/data", "notebooks/docs", "notebooks/l1periodogram", "notebooks/*.md", "notebooks/*.rst"]

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
    "use_edit_page_button": True,
    "use_issues_button": True,
    "use_repository_button": True,
    "use_download_button": True,
}
