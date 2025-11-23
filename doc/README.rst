Compiling radler document
=========================

Install Sphinx from 
http://www.sphinx-doc.org

In case of mac, use port to install instead of pip.  

::

    sudo port install py314-sphinx
    sudo port select --set python python314
    sudo port select --set sphinx py314-sphinx

Generate target files using Sphinx. 

:: 

    make html
    make latexpdf 

You will find your HTML/LaTeX files under the _build directory. Copy the HTML files to the /docs directory for GitHub Pages at https://sri-csl.github.io/radler/.
