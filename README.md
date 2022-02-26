
# PyGEE-SWToolbox
[![MIT License](https://img.shields.io/apm/l/atomic-design-ui.svg?)](https://github.com/tterb/atomic-design-ui/blob/master/LICENSEs) [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.5664523.svg)](https://doi.org/10.5281/zenodo.5664523)

A Python Jupyter notebook toolbox for interactive surface water mapping and analysis using Google 
Earth Engine.

## Introduction
PyGEE-SWToolbox is Python-Google Earth Engine (GEE) Surface Water Analysis toolbox developed
 in Jupyter notebook for interactive surface water mapping using the GEE cloud computing 
 platform. Conventional use of the GEE platform requires the user to able to write 
 JavaScript codes in the GEE online Code Editor or the use of Python codes using the 
 Python API to perform geospatial processing of datasets. This toolbox provides a graphical 
 user interface (GUI) for surface water analysis and visualization without the user writing 
 a single line of code. The GUI was developed using ipyleaflet and ipywidgets. The toolbox 
 relies on the <b>GEE Python API, geemap, geetools, eemont, hydra-floods, geopandas, and 
 plotly</b> packages.

 The toolbox is intended for researchers, water resource managers, and planners who would
 like to utilize the geospatial datasets and cloud computing power of the GEE platform.
 The toolbox automates the traditional process of downloading satellite imagery, processing,
 atmospheric correction, and application of surface water extraction algorithms. It cuts
 down the time needed to perform these processes.

## Features
The list below shows some of the features available in the toolbox.
- Interactive definition of study area, shapefile upload and study period using the GUI.
- Retrieval of timeseries of satellite imagery for the study area and make them analysis
    ready.
- Extraction of surface water from all retreived satellite imagery using water extraction
    indices such as NDWI, MNDWI, AWEI, and DSWE.
- Generate a timeseries of surface water area dynamics and export timeseries to CSV format.
- Perform water occurency frequency and hydroperiod analysis.
- Export retrieved satellite imagery and surface water maps to Google Drive or download to
    to local computer.

  
## Installation 

To use the PyGEE-SWToolbox, the user must first sign up for a Google Earth Engine account to authenticate 
the use of the GEE API. The user has to clone the project repository using Git Bash as shown 
below:

``` 
  git clone https://github.com/collinsowusu/PyGEE-SWToolbox.git
```
Optionally, on GitHub, navigate to the main page of the [repository](https://github.com/collinsowusu/PyGEE-SWToolbox) 
and above the list of files click <b>Code</b> to download zip or open with GitHub Desktop. 
The project archive can also be downloaded from [Zenodo](https://zenodo.org/record/4910772#.YNpSmzhKiUk).

It is recommended to download and install either [Miniconda](https://docs.conda.io/en/latest/miniconda.html) or
[Anaconda](https://www.anaconda.com/distribution/#download-section) on your computer. Miniconda is recommended since it is 
a minimal version of Anaconda with no third-party binaries. Open the Anaconda Prompt from your programs menu after the 
miniconda or anaconda is installed. 
Create a conda Python environment and install Jupyter notebook with the following commands 
(where SWToolbox is the name of the environment which can be changed to a user-preferred name):

``` 
  conda create -n SWToolbox python=3.8
  conda activate SWToolbox
  conda install -c conda-forge notebook 
```
The required packages can be found in the requirements.txt file in the project directory.
These packages can be installed manually as:

``` 
  pip install <package name>
```
Optionally, you can change to the project directory at the conda prompt and install all 
packages using pip:

``` 
  cd <project directory>
  pip install -r requirements.txt
```
## Usage

In your created conda environmnet, open Jupyter notebook as:

``` 
  jupyter notebook
```

With the notebook running, open the PyGEE-SWToolbox notebook file. The toolbox notebook contains two cells. 
Run the first cell which will import the GEE API and initialize it. The first time run of the notebook will
require you to authenticate the GEE API using your GEE Account. Run the second cell to display the GUI 
of the toolbox.

The toolbox can also be imported into any other jupyter notebook as shown in the second cell of the provided notebook.

Refer to the User Manual in the project directory on how to use the toolbox.

  
## License

This project is licensed under the [MIT](https://choosealicense.com/licenses/mit/) license.

## How to cite
If you find PyGEE-SWToolbox useful, please cite this work as:

Owusu C, Snigdha NJ, Martin MT, Kalyanapu AJ. PyGEE-SWToolbox: A Python Jupyter Notebook Toolbox for Interactive Surface Water Mapping and Analysis Using Google Earth Engine. Sustainability. 2022; 14(5):2557. https://doi.org/10.3390/su14052557

BibTeX if required:

	@article{su14052557,
	author = {Owusu, Collins and Snigdha, Nusrat J and Martin, Mackenzie T and Kalyanapu, Alfred J},
	doi = {10.3390/su14052557},
	issn = {2071-1050},
	journal = {Sustainability},
	mendeley-groups = {Remote Sensing},
	month = {feb},
	number = {5},
	pages = {2557},
	title = {{PyGEE-SWToolbox: A Python Jupyter Notebook Toolbox for Interactive Surface Water Mapping and Analysis Using Google Earth Engine}},
	url = {https://www.mdpi.com/2071-1050/14/5/2557},
	volume = {14},
	year = {2022}
	}
  
## Acknowledgements

This toolbox is based upon work supported by the Natural Resources Conservation Service, 
U.S. Department of Agriculture, and The Nature Conservancy, under award number 
68-5C16-17-015. Any opinions, findings, conclusions, or recommendations 
expressed in this publication are those of the authors and do not necessarily 
reflect the views of the Natural Resources Conservation Service or The Nature Conservancy.
The authors also acknowledge the funding support from the Center for the Management, Utilization, and Protection of Water Resources (TTU Water Center) at
the Tennessee Technological University.

The authors would like to thank the developers of <b>ipywidgets, geemap, eemont, geetools, 
geopandas, and hydrafloods</b> packages.
