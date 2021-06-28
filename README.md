
# PyGEE-SWToolbox
[![MIT License](https://img.shields.io/apm/l/atomic-design-ui.svg?)](https://github.com/tterb/atomic-design-ui/blob/master/LICENSEs) [![DOI](https://zenodo.org/badge/374874735.svg)](https://zenodo.org/badge/latestdoi/374874735)

A Python Jupyter notebook toolbox for interactive surface water mapping using Google 
Earth Engine.

## Introduction
PyGEE-SWToolbox is Python-Google Earth Engine (GEE) Surface Water Analyzer toolbox developed
 in Jupyter notebook for interactive surface water mapping using the GEE cloud computing 
 platform. Conventional use of the GEE platform requires the user to able to write 
 JavaScript codes in the GEE online Code Editor or the use of Python codes using the 
 Python API to perform geospatial processing of datasets. This toolbox provides a graphical 
 user interface (GUI) for surface water analysis and visualization without the user writing 
 a single line of code. The GUI was developed using ipyleaflet and ipywidgets. The toolbox 
 relies on the <b>GEE Python API, geemap, geetools, eemont, hydrafloods, geopandas, and 
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
- Extract of surface water from all retreived satellite imagery using water extraction
    indices such as NDWI, MNDWI, AWEI, and DSWE.
- Generate a timeseries of surface water area dynamics and export timeseries to CSV format.
- Perform water occurency frequency and hydroperiod analysis.
- Export retrieved satellite imagery and surface water maps to Google Drive or download to
    to local computer.

  
## Installation 

To use the PyGEE-SWToolbox, the user must first sign up for a Google account to authenticate 
the use of the GEE API. The user has to clone the project repository using Git Bash shown 
below:

``` 
  git clone https://github.com/collinsowusu/PyGEE-SWToolbox.git
```
Optionally, on GitHub, navigate to the main page of the [repository](https://github.com/collinsowusu/PyGEE-SWToolbox) 
and above the list of files click <b>Code</b> to download zip or open with GitHub Desktop. 
The project archive can also be downloaded from [Zenodo](https://zenodo.org/record/4910772#.YNpSmzhKiUk).

It is recommended to have [Anaconda](https://www.anaconda.com/distribution/#download-section)
 or [Miniconda](https://docs.conda.io/en/latest/miniconda.html) installed on your computer. 
 You should create a conda Python environment and install Jupyter notebook and geopandas with
 the following commands:

``` 
  conda create -n SWTBX python=3.8
  conda activate SWTBX
  conda install -c conda-forge notebook
  conda install geopandas
```
The required packages can be found in the requirements.txt file in the project directory.
These packages can be installed manually as:

``` 
  conda install <package name>
```
Optionally, you can change to the project directory at the conda prompt and install all 
packages using pip:

``` 
  cd <project directory>
  pip install -r requirements.txt
```
## Usage

```javascript
import Component from 'my-project'

function App() {
  return <Component />
}
```

  
## License

This project is licensed under the [MIT](https://choosealicense.com/licenses/mit/) license.

  
## Acknowledgements

This toolbox is based upon work supported by the Natural Resources Conservation Service, 
U.S. Department of Agriculture, and The Nature Conservancy, under award number 
68-5C16-17-015. Any opinions, findings, conclusions, or recommendations 
expressed in this publication are those of the authors and do not necessarily 
reflect the views of the Natural Resources Conservation Service or The Nature Conservancy.

The authors would like to thank the developers of <b>ipywidgets, geemap, eemont, geetools, 
geopandas, and hydrafloods</b> packages.
## References

- Wu, Q., (2020). geemap: A Python package for interactive mapping with Google Earth Engine. The Journal of Open Source Software, 5(51), 2305. https://doi.org/10.21105/joss.02305
- Wu, Q., Lane, C. R., Li, X., Zhao, K., Zhou, Y., Clinton, N., DeVries, B., Golden, H. E., & Lang, M. W. (2019). Integrating LiDAR data and multi-temporal aerial imagery to map wetland inundation dynamics using Google Earth Engine. Remote Sensing of Environment, 228, 1-13. https://doi.org/10.1016/j.rse.2019.04.015
- Montero, D., (2021). eemont: A Python package that extends Google Earth Engine. Journal of Open Source Software, 6(62), 3168, https://doi.org/10.21105/joss.03168