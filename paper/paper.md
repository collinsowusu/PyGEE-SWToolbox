---
title: 'PyGEE-SWToolbox: A Python Jupyter notebook toolbox for interactive surface water mapping using Google Earth Engine'
tags:
  - Python
  - Google Earth Engine
  - Jupyter notebook
  - surface water mapping
  - geemap
authors:
  - name: Collins Owusu
    orcid: 0000-0001-6754-9311
    affiliation: "1"
  - name: Nusrat J. Snigdha
    orcid: 0000-0002-9444-1469
    affiliation: "1"
  - name: Mackenzie T. Martin
    orcid: 0000-0002-7744-2080
    affiliation: "1"
  - name: Alfred J. Kalyanapu
    orcid: 0000-0002-7746-3121
    affiliation: "1"
affiliations:
 - name: Civil and Environmental Engineering Department, Tennessee Technological University
   index: 1
date: 29 June 2021
bibliography: paper.bib
---

# Summary

PyGEE-SWToolbox is Python-Google Earth Engine (GEE) [@gorelick2017google] Surface Water Analysis toolbox 
developed in Jupyter notebook for interactive surface water mapping using the GEE cloud computing platform.
This toolbox provides a graphical user interface (GUI) for surface water extraction, water occurrence frequency 
and hydroperiod analysis, time series analysis, and visualization using GEE without the user writing a single 
line of JavaScript or Python code. The GUI was developed using ipyleaflet and ipywidgets. The toolbox relies 
on the <b>GEE Python API, geemap [@Wu2020], geetools, eemont [@Montero2021], hydra-floods, geopandas, and 
plotly</b> packages. The toolbox provides users an easy way to analyze and visualize GEE datasets for water resource
applications.


# Statement of need

The GEE platform has been applied in various aspects of water resource monitoring such as wetland inundation 
dynamics [@Wu2019], flood monitoring [@DeVries2020], satellite-derived bathymetry [@Casal2020], and 
gap-filling of time series [@Walker2020]. Conventional use of the GEE platform requires the user to 
able to write JavaScript codes in the GEE online Code Editor or the use of Python codes using the Python 
API to perform geospatial processing of datasets. This is sometimes problematic for some researchers and 
water resource managers who have no knowledge in programming or are not used to the languages needed to 
communicate with the GEE platform. This toolbox provides a simple GUI as a solution to some of the challenges 
faced by non-programmers in utilizing the GEE platform for water resources monitoring.

# Audience

The toolbox is intended for researchers, water resource managers, and planners who would 
like to utilize the geospatial datasets and cloud computing power of the GEE platform to
monitor changes in water resources with little to no knowledge on the use of the platform and it's 
coding requirements. The toolbox is currently being used by a team of civil engineering and biology researchers 
monitoring the hydrology of wetlands under the Wetland Reserve Program (WRP) which are being monitored 
to assess the effectiveness of wetland restoration practices implemented by the Natural Resources 
Conservation Service (NRCS) in West Tennessee and West Kentucky

# Functionality

PyGEE-SWToolbox can:
- Retrieve  a time series of Landsat, Sentinel-1, and Sentinel-2 satellite imagery for a study area.
- Extract surface water from all retreived satellite imagery using water extraction
    indices such as NDWI [@McFEETERS1996], MNDWI [@Xu2006], AWEI [@FEYISA201423], and DSWE [@Walker2020].
- Generate a timeseries of surface water area dynamics and export timeseries to CSV format.
- Perform water occurency frequency and hydroperiod analysis.
- Export retrieved satellite imagery, surface water and frequency maps to Google Drive or download to
    to local computer for use in other GIS environments.



# Acknowledgements

This toolbox is based upon work supported by the Natural Resources Conservation Service, 
U.S. Department of Agriculture, and The Nature Conservancy, under award number 
68-5C16-17-015. Any opinions, findings, conclusions, or recommendations 
expressed in this publication are those of the authors and do not necessarily 
reflect the views of the Natural Resources Conservation Service or The Nature Conservancy.

# References
