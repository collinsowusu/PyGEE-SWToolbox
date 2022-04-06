import ee
# Initialize the GEE API
# try:
#     ee.Initialize()
# except Exception as e:
#     ee.Authenticate()
#     ee.Initialize()

# geemap:A Python package for interactive mapping with Google Earth Engine, ipyleaflet, and ipywidgets
# Documentation: https://geemap.org
import geemap
from geemap import ml
import pickle
# from geemap import ee_basemaps

import matplotlib.pyplot as plt

import numpy as np

#eemont
import eemont

# import developed utilities
# import Utilities as ut
from Utilities import *

# geetols: Google earth engine tools
# https://github.com/gee-community/gee_tools
import geetools
from geetools import tools

# hydrafloods: Hydrologic Remote Sensing Analysis for Floods
#https://github.com/Servir-Mekong/hydra-floods
import hydrafloods as hf
from hydrafloods import geeutils

# Ipywidgets for GUI design
import ipywidgets as ipw
from IPython.display import display
from ipywidgets import HBox, VBox, Layout

# A simple Python file chooser widget for use in Jupyter/IPython in conjunction with ipywidgets
# https://pypi.org/project/ipyfilechooser/
from ipyfilechooser import FileChooser

# Plotly Python API for interactive graphing
import plotly
import plotly.express as px
import plotly.graph_objects as go

# Pandas -  Python Data Analysis Library for data analysis and manipulation
import pandas as pd

# Miscellaneous Python modules
from datetime import datetime, timedelta
import os


class Toolbox:
       
    def __init__(self):
        #----------------------------------------------------------------------------------------------------

        """ UI Design"""
        #---------------------------------------------------------------------------------------------------
        # Program Title
        Title_text =  ipw.HTML(
            "<h3 class= 'text-center'><font color = 'blue'>Python-GEE Surface Water Analysis Toolbox v.1.0.3</font>")
        style = {'description_width': 'initial'}

        # Image Processing Tab
        #************************************************************************************************
        # Image Parameters UI
        dataset_description = ipw.HTML(value = f"<b><font color='blue'>{'Satellite Imagery Parameters:'}</b>")

        dataset_Label = ipw.Label('Select Dataset:', layout=Layout(margin='5px 0 0 5px')) #top right bottom left

        Platform_options = ['Landsat-Collection 1', 'Landsat-Collection 2','Sentinel-1', 'Sentinel-2', 'USDA NAIP' ]

        self.Platform_dropdown = ipw.Dropdown(options = Platform_options, value = None,
                                           layout=Layout(width='150px', margin='5px 0 0 5px'))
        
        filtering_Label = ipw.Label('Speckle filter:', layout=Layout(margin='5px 0 0 5px'))
        
        filtering_options = ['Refined-Lee', 'Perona-Malik', 'P-median', 'Lee Sigma', 'Gamma MAP','Boxcar Convolution']
        
        
        self.filter_dropdown = ipw.Dropdown(options = filtering_options, value = 'Refined-Lee',
                                           layout=Layout(width='150px', margin='5px 0 0 15px'))
        
        self.filter_dropdown.disabled = True
        
        PlatformType = HBox([dataset_Label, self.Platform_dropdown])
        FilterType = HBox([filtering_Label, self.filter_dropdown])
        

        # Study period definition
        #************************************************************************************************
        # Start date picker
        lbl_start_date = ipw.Label('Start Date:', layout=Layout(margin='5px 0 0 5px'))

        self.start_date = ipw.DatePicker(value = datetime.now()-timedelta(7), disabled=False, 
                                    layout=Layout(width='150px', margin='5px 0 0 30px'))

        start_date_box = HBox([lbl_start_date, self.start_date])

        # End date picker
        lbl_end_date = ipw.Label('End Date:', layout=Layout(margin='5px 0 0 5px'))

        self.end_date = ipw.DatePicker(value = datetime.now(), disabled=False, 
                                  layout=Layout(width='150px', margin='5px 0 0 34px'))

        end_date_box = HBox([lbl_end_date, self.end_date])

        datePickers = VBox([start_date_box, end_date_box])


        # Cloud threshold for filtering data
        #************************************************************************************************
        # Set cloud threshold
        self.cloud_threshold = ipw.IntSlider(description = 'Cloud Threshold:', orientation = 'horizontal',
                                         value = 50, step = 5, style = style)

        imageParameters = VBox([dataset_description, PlatformType, FilterType, datePickers, self.cloud_threshold], 
                           layout=Layout(width='305px', border='solid 2px black'))


        # Study Area definition
        #************************************************************************************************
        # Option to use a map drawn boundary or upload shapefile
        StudyArea_description = ipw.HTML(value = f"<b><font color='blue'>{'Study Area Definition:'}</b>")

        self.user_preference = ipw.RadioButtons(options=['Map drawn boundary','Upload boundary'], value='Map drawn boundary')

        self.file_selector = FileChooser(description = 'Upload', filter_pattern = ["*.shp"], use_dir_icons = True)

        # Retrieve and process satellite images
        #***********************************************************************************************
        # Button to retrieve and process satellite images from the GEE platform
        self.imageProcessing_Button = ipw.Button(description = 'Process images',
                                            tooltip='Click to process images', button_style = 'info',
                                           layout=Layout(width='150px', margin='5px 0 0 50px', border='solid 2px black'))

        # Study area UI and process button container
        # ************************************************************************************************
        StudyArea = VBox(children = [StudyArea_description, self.user_preference, self.imageProcessing_Button], 
                           layout=Layout(width='300px', border='solid 2px black', margin='0 0 0 10px'))



        # Results UI for displaying number and list of files
        #*****************************************************************************************************
        lbl_results = ipw.HTML(value = f"<b><font color='blue'>{'Processing Results:'}</b>")

        lbl_images = ipw.Label('No. of processed images:')

        self.lbl_RetrievedImages = ipw.Label()

        display_no_images = HBox([lbl_images, self.lbl_RetrievedImages])

        lbl_files = ipw.Label('List of files:')

        self.lst_files = ipw.Select(layout=Layout(width='360px', height='100px'))

        image_Results = VBox([lbl_results, display_no_images, lbl_files, self.lst_files], 
                           layout=Layout(width='400px', border='solid 2px black', margin='0 0 0 10px'))


        # Container for Image Processing Tab
        #************************************************************************************************
        imageProcessing_tab = HBox([imageParameters, StudyArea, image_Results])


        # Water Extraction Tab
        #*************************************************************************************************
        # Water extraction indices
        water_index_options = ['NDWI','MNDWI','DSWE', 'AWEInsh', 'AWEIsh']

        lbl_indices = ipw.Label('Water Index:', layout=Layout(margin='5px 0 0 5px'))

        self.water_indices = ipw.Dropdown(options = water_index_options, value = 'NDWI',
                                    layout=Layout(width='100px', margin='5px 0 0 63px'))

        display_indices = HBox([lbl_indices, self.water_indices])

        # Color widget for representing water
        lbl_color = ipw.Label('Color:', layout=Layout(margin='5px 0 0 5px'))

        self.index_color =  ipw.ColorPicker(concise = False, value = 'blue',layout=Layout(width='100px', margin='5px 0 0 101px'))

        display_color_widget = HBox([lbl_color, self.index_color])

        # Water index threshold selection
        threshold_options = ['Simple','Otsu']

        lbl_threshold_method = ipw.Label('Thresholding Method:', layout=Layout(margin='5px 0 0 5px'))

        self.threshold_dropdown = ipw.Dropdown(options = threshold_options,value = 'Simple',
                                    layout=Layout(width='100px', margin='5px 0 0 10px'))

        display_thresholds = HBox([lbl_threshold_method, self.threshold_dropdown])


        lbl_threshold = ipw.Label('Threshold value:', layout=Layout(margin='5px 0 5px 5px'))

        self.threshold_value = ipw.BoundedFloatText(value=0.000, min = -1.0, max = 1.0, step = 0.050,
                                               layout=Layout(width='100px', margin='5px 0 0 40px'))

        display_threshold_widget = HBox([lbl_threshold, self.threshold_value])

        water_index_Box = VBox([display_indices, display_thresholds, display_threshold_widget, display_color_widget],
                              layout=Layout(width='250px', border='solid 2px black'))

        self.extractWater_Button = ipw.Button(description = 'Extract Water', tooltip='Click to extract surface water', 
                                        button_style = 'info', 
                                         layout=Layout(width='150px', margin='5px 0 0 20px', border='solid 2px black'))

        Extraction_tab = HBox([water_index_Box, self.extractWater_Button])
        self.extractWater_Button.disabled = True

        # Spatial Analysis Tab
        #**************************************************************************************************

        self.water_Frequency_button = ipw.Button(description = 'Compute Water Frequency',
                                            tooltip='Click to compute water occurence frequency',
                                            button_style = 'info', 
                                            layout=Layout(width='200px', border='solid 2px black',margin='5 0 0 50px'))
        self.water_Frequency_button.disabled = True

        self.Depths_Button = ipw.Button(description = 'Compute Depth Map',
                                        tooltip='Click to generate depth maps', button_style = 'info',
                                        layout=Layout(width='200px', border='solid 2px black',margin='5 0 0 50px'))
        self.Depths_Button.disabled = True

        self.elevData_options = ipw.Dropdown(options=['NED','SRTM','User DEM'], value='NED', description='Elev. Dataset:',
                                        layout=Layout(width='210px', margin='0 0 0 10px'), style = style)
        self.elevData_options.disabled = False
        
#         self.elev_Methods = ipw.Dropdown(options=['Random Forest','Mod_Stumpf','Mod_Lyzenga','FwDET'], value='Random Forest',
#                             description='Depth method:',
#                             layout=Layout(width='210px', margin='0 0 0 10px'), style = style)
        
        self.elev_Methods = ipw.Dropdown(options=['Experimental','FwDET'], value='FwDET',
                            description='Depth method:',
                            layout=Layout(width='210px', margin='0 0 0 10px'), style = style)
        
        self.elev_Methods.disabled = True

        self.userDEM = ipw.Dropdown(description='Select GEE asset:', 
                          layout=Layout(width='300px', margin='0 0 0 10px'), style = style)

        lbl_Elev = ipw.Label('Elevation Dataset:', layout=Layout(margin='0 0 0 10px'))

        elev_Box = HBox([self.Depths_Button, self.elev_Methods, self.elevData_options])

        self.zonalAnalysis_Button = ipw.Button(description = 'Zonal Analysis',
                                        tooltip='Click to remove clouds', button_style = 'info',
                                       layout=Layout(width='200px', border='solid 2px black',margin='5 0 0 50px'))

        # Spatial_Analysis_Tab = VBox([water_Frequency_button, elev_Box, zonalAnalysis_Button])
        Spatial_Analysis_Tab = VBox([self.water_Frequency_button, elev_Box])


        # Ploting and Statistics Tab
        #***************************************************************************************************
        lbl_Area_Plotting = ipw.HTML(value = f"<b><font color='blue'>{'Surface Water Area Computation:'}</b>")
        self.area_unit = ipw.Dropdown(options = ['Square m','Square Km', 'Hectares', 'Acre'], value = 'Square m',
                                    description = 'Unit for water surface area:', style=style,
                                    tooltip='Select unit for areas')

        self.plot_button = ipw.Button(description = 'Compute and Plot Areas', tooltip='Click to plot graph', button_style = 'info',
                                layout=Layout(width='170px', margin='10 0 0 200px', border='solid 2px black'))
        self.plot_button.disabled = True

        # lbl_depth_Plotting = ipw.Label(value ='Plot depth hydrograph at a location:', layout=Layout(margin='10px 0 0 0'))
        lbl_depth_Plotting = ipw.HTML(value = f"<b><font color='blue'>{'Plot depth hydrograph at a location:'}</b>")

        self.point_preference = ipw.RadioButtons(options=['Map drawn point','Enter coordinates'], 
                                            value='Map drawn point')

        self.coordinates_textbox = ipw.Text(layout=Layout(width='200px'))
        lbl_coordinates = ipw.Label(value='Enter Long, Lat in decimal degrees')

        # point_selector = FileChooser(description = 'Upload point', filter_pattern = ["*.shp"], use_dir_icons = True)

        self.depth_plot_button = ipw.Button(description = 'Plot depths', tooltip='Click to plot depth hydrograph', button_style = 'info',
                                layout=Layout(width='170px', margin='10 0 0 100px', border='solid 2px black'))
        self.depth_plot_button.disabled = True

        depth_box = VBox(children = [lbl_depth_Plotting,self.point_preference, self.depth_plot_button])

        plotting_box = VBox([lbl_Area_Plotting, self.area_unit, self.plot_button, depth_box], 
                            layout=Layout(width='310px', border='solid 2px black'))

        lbl_Stats = ipw.HTML(value = f"<b><font color='blue'>{'Summary Statistics:'}</b>")
        self.lbl_Max_Area = ipw.Label(value ='', layout=Layout(width='100px')) #top right bottom left
        self.lbl_Min_Area = ipw.Label(value ='', layout=Layout(width='100px'))
        self.lbl_Avg_Area = ipw.Label(value ='', layout=Layout(width='100px'))
        self.lbl_Max_Depth = ipw.Label(value ='', layout=Layout(width='100px'))
        self.lbl_Min_Depth = ipw.Label(value ='', layout=Layout(width='100px'))
        self.lbl_Avg_Depth = ipw.Label(value ='', layout=Layout(width='100px'))

        self.cap_Max_Area = ipw.Label(value ='Max. Area:')
        self.cap_Min_Area = ipw.Label(value ='Min. Area:')
        self.cap_Avg_Area = ipw.Label(value ='Avg. Area:')
        self.cap_Max_Depth = ipw.Label(value ='Max. Depth:')
        self.cap_Min_Depth = ipw.Label(value ='Min. Depth:')
        self.cap_Avg_Depth = ipw.Label(value ='Avg. Depth:')

        max_box = HBox([self.cap_Max_Area,self.lbl_Max_Area, self.cap_Max_Depth,self.lbl_Max_Depth])
        min_box = HBox([self.cap_Min_Area,self.lbl_Min_Area, self.cap_Min_Depth,self.lbl_Min_Depth])
        avg_box = HBox([self.cap_Avg_Area,self.lbl_Avg_Area, self.cap_Avg_Depth,self.lbl_Avg_Depth])

        stats_box = VBox([lbl_Stats, max_box, min_box, avg_box])

        self.file_selector1 = FileChooser(description = 'Select folder and filename', filter_pattern = "*.csv", use_dir_icons = True)

        self.file_selector1.title = 'Select Folder and Filename'

        self.file_selector1.default_path = os.getcwd()

        self.save_data_button = ipw.Button(description = 'Save Data',tooltip='Click to save computed areas to file',button_style = 'info',
                                       layout=Layout(width='100px', border='solid 2px black',margin='5 0 0 50px'))

        lbl_Save = ipw.HTML(value = f"<b><font color='blue'>{'Save Data:'}</b>")

        stats_save_box = VBox(children=[stats_box, lbl_Save, self.file_selector1, self.save_data_button],
                       layout=Layout(width='550px', border='solid 2px black', margin='0 0 0 10px'))

        plot_stats_tab = HBox(children=[plotting_box, stats_save_box])

        # Downloads Tab
        #***************************************************************************************************
        self.files_to_download = ipw.RadioButtons(options=['Satellite Images', 'Water Mask', 'Water Frequency', 'Depth Maps',
                                                      'DSWE Images'], value='Satellite Images', 
                                             description='Files to download:', style = style)

        self.download_location = ipw.RadioButtons(options=['Google Drive', 'Local Disk'], 
                                             value='Google Drive', description='Download Location:', style = style)

        self.folder_name = ipw.Text(description='Folder Name:')

        self.folder_selector = FileChooser(description = 'Select Folder', show_only_dirs = True, use_dir_icons = True)

        self.folder_selector.title = '<b>Select a folder</b>'

        self.folder_selector.default_path = os.getcwd()

        self.download_button = ipw.Button(description = 'Download',
                                            tooltip='Click to plot download water images', button_style = 'info')
        self.download_button.disabled = True


        download_settings = VBox(children=[self.files_to_download, self.download_location, self.folder_name])

        download_tab = HBox([download_settings, self.download_button])
        
        # variable to hold the random forest classifier
        self.rf_ee_classifier = None
        self.WaterMasks = None
        self.visParams = None
        self.freqParams = None
        self.filtered_Collection = None
        self.filtered_landsat = None
        self.clipped_images = None
        self.imageType = None
        self.dates = None
        self.site = None
        self.img_scale = None
        self.file_list = None
        self.StartDate = None
        self.EndDate = None
        self.water_images = None
        self.dswe_images = None
        self.index_images = None
        self.dswe_viz = None
        self.depth_maps = None
        self.filtered_Water_Images =  None
        self.depthParams = None

        # Functions to control UI changes and parameter settings
        #****************************************************************************************************
        def platform_index_change(change):
            """
            Function to set image visualization parameters, hide or show some UI componets and
            show water indices that are applicable to the type of satellite image selected

            args:
                None

            returns:
                None
            """
            try:

                if self.Platform_dropdown.value == 'Landsat-Collection 1':
                    self.visParams = {'bands': ['red', 'green', 'blue'],
                          'min': 0,
                          'max': 3000,
                          'gamma':1.4
                          }
                    self.cloud_threshold.disabled = False
                    self.water_indices.disabled = False
                    self.index_color.disabled = False
                    self.threshold_value.disabled = False
                    self.water_indices.options = ['NDWI','MNDWI','DSWE','AWEInsh', 'AWEIsh']
                    self.threshold_dropdown.options = ['Simple','Otsu']
                    self.filter_dropdown.disabled = True
                elif self.Platform_dropdown.value == 'Landsat-Collection 2':
                    self.visParams = {'bands': ['red', 'green', 'blue'],
                          'min': 0,
                          'max': 0.3,
                          }
                    self.cloud_threshold.disabled = False
                    self.water_indices.disabled = False
                    self.index_color.disabled = False
                    self.threshold_value.disabled = False
                    self.water_indices.options = ['NDWI','MNDWI','DSWE','AWEInsh', 'AWEIsh']
                    self.threshold_dropdown.options = ['Simple','Otsu']
                    self.filter_dropdown.disabled = True

                elif self.Platform_dropdown.value == 'Sentinel-1':
                    self.visParams = {'min': -25,'max': 0}
                    self.cloud_threshold.disabled = True
                    self.water_indices.options = ['VV','VH']#,'NDPI','NVHI', 'NVVI']
                    self.index_color.disabled = False
                    self.threshold_value.disabled = True
                    self.threshold_dropdown.options = ['Otsu']
                    self.filter_dropdown.disabled = False
                elif self.Platform_dropdown.value == 'Sentinel-2':
                    self.visParams = {'bands': ['red', 'green', 'blue'],
                      'min': 0.0,
                      'max': 3000}
                    self.cloud_threshold.disabled = False
                    self.water_indices.disabled = False
                    self.index_color.disabled = False
                    self.threshold_value.disabled = False
                    self.water_indices.options = ['NDWI','MNDWI']
                    self.threshold_dropdown.options = ['Simple','Otsu']
                    self.filter_dropdown.disabled = True
                elif self.Platform_dropdown.value == 'USDA NAIP':
                    self.visParams = {'bands': ['R', 'G','B'],
                                'min': 0.0,
                                'max': 255.0}
                    self.threshold_value.disabled = False
                    self.water_indices.disabled = False
                    self.index_color.disabled = False
                    self.water_indices.options = ['NDWI']
                    self.threshold_dropdown.options = ['Simple','Otsu']
                    self.filter_dropdown.disabled = True
            except Exception as e:
                     print(e)

        # Link widget to function
        self.Platform_dropdown.observe(platform_index_change, 'value')

        def showFileSelector(button):
            """
            Function to show or hide shapefile upload widget

            args:
                None

            returns:
                None
            """
            if button['new']:
                StudyArea.children = [StudyArea_description, self.user_preference, self.file_selector, self.imageProcessing_Button]
            else:
                StudyArea.children = [StudyArea_description, self.user_preference,self.imageProcessing_Button]

        # Link widget to file selector function
        self.user_preference.observe(showFileSelector, names='index')

        def showLocationSelector(button):
            """
            Function to show or hide folder selector

            args:
                None

            returns:
                None
            """
            if button['new']:
                download_settings.children = [self.files_to_download, self.download_location, self.folder_selector]
            else:
                download_settings.children = [self.files_to_download, self.download_location, self.folder_name]

        # Link widget to folder selector function
        self.download_location.observe(showLocationSelector, names='index')

        def pointOptions_selector(button):
            """
            Function to show or hide folder selector

            args:
                None

            returns:
                None
            """
            if button['new']:
                depth_box.children = [lbl_depth_Plotting,self.point_preference, lbl_coordinates, self.coordinates_textbox, 
                                      self.depth_plot_button]
            else:
                depth_box.children = [lbl_depth_Plotting,self.point_preference, self.depth_plot_button]


        # Link widget to folder selector function
        self.point_preference.observe(pointOptions_selector, names='index')

        def indexSelection(change):
            if self.water_indices.value =='DSWE':
                self.threshold_value.min = 1.0
                self.threshold_value.max = 4.0
                self.threshold_value.step = 1.0
                self.threshold_value.value = 4.0
                self.threshold_dropdown.options = ['Simple']
            else:
                self.threshold_value.min = -1.0
                self.threshold_value.max = 1.0
                self.threshold_value.step = 0.050
                self.threshold_value.value = 0.0
                self.threshold_dropdown.options = ['Simple','Otsu']

        self.water_indices.observe(indexSelection, 'value')

        def thresholdSelection(change):
            if self.threshold_dropdown.value =='Otsu':
                self.threshold_value.disabled = True
            else:
                self.threshold_value.disabled = False

        # Link widget to threshold method selection function
        self.threshold_dropdown.observe(thresholdSelection, 'value')
        
        def depthMethodSelection(change):
            if self.elev_Methods.value == 'FwDET' or self.elev_Methods.value == 'Experimental':
                self.elevData_options.disabled = False
            else:
                self.elevData_options.disabled = True
                elev_Box.children = [self.Depths_Button, self.elev_Methods, self.elevData_options]

        # Link widget to threshold method selection function
        self.elev_Methods.observe(depthMethodSelection, 'value')

        def demSelection(change):
            if self.elevData_options.value == 'User DEM':
                folder = ee.data.getAssetRoots()[0]['id']
                assets = ee.data.listAssets({'parent':folder})
                # filter only image assets
                filtered_asset = list(filter(lambda asset: asset['type'] == 'IMAGE', assets['assets']))
                # create a list of image assets
                list_assets = [sub['id'] for sub in filtered_asset]
                elev_Box.children = [self.Depths_Button, self.elev_Methods, self.elevData_options, self.userDEM]
                self.userDEM.options = list_assets # set dropdown options to list of image assets
            else:
                elev_Box.children = [self.Depths_Button, self.elev_Methods, self.elevData_options]

        # Link widget to function
        self.elevData_options.observe(demSelection, 'value')

        #****************************************************************************************************

        # Full UI
        #***************************************************************************************************
        tab_children = [imageProcessing_tab, Extraction_tab, Spatial_Analysis_Tab, plot_stats_tab, download_tab]

        tab = ipw.Tab()
        tab.children = tab_children

        # changing the title of the first and second window
        tab.set_title(0, 'Image Processing')
        tab.set_title(1, 'Water Extraction')
        tab.set_title(2, 'Spatial Analysis')
        tab.set_title(3, 'Plotting & Stats')
        tab.set_title(4, 'Download & Export')


        # Plotting outputs and feedback to user
        #***************************************************************************************************

        self.feedback = ipw.Output()
#         OUTPUTS = VBox([self.feedback])

        # create map instance
        self.Map =  geemap.Map()
        self.Map.add_basemap('HYBRID')

        GUI = VBox([Title_text,tab,self.Map])
        display(GUI)
        self.fig = go.FigureWidget()
        self.fig.update_layout(title = '<b>Surface Water Area Hydrograph<b>', 
                                      title_x = 0.5, title_y = 0.90, title_font=dict(family="Arial",size=24),
                                      template = "plotly_white",
                                      xaxis =dict(title ='<b>Date<b>', linecolor = 'Black'),
                                      yaxis=dict(title='Area (sq m)', linecolor = 'Black'),
                                      font_family="Arial")
        # display plotly figure
        display(self.fig)
        display(self.feedback)
        
        # Widget-Function connections
        self.imageProcessing_Button.on_click(self.process_images)
        self.extractWater_Button.on_click(self.Water_Extraction)
        self.plot_button.on_click(self.plot_areas)
        self.save_data_button.on_click(self.save_data)
        self.Depths_Button.on_click(self.calc_depths)
        self.download_button.on_click(self.dowload_images)
        self.water_Frequency_button.on_click(self.water_frequency)
        self.depth_plot_button.on_click(self.plot_depths)
        

    # Function to clip images
    def clipImages(self,img):
        """
        Function to clip images

        args:
            Image

        returns:
            Clipped image
        """
        orig = img
        clipped_image = img.clip(self.site).copyProperties(orig, orig.propertyNames())
        return clipped_image    


    def process_images(self, b):
        """
        Function to retrieve and process satellite images from GEE platform

        args:
            None

        returns:
            None
        """
        with self.feedback:
            self.feedback.clear_output()
            try:

                self.fig.data = [] # clear existing plot

                self.lbl_RetrievedImages.value = 'Processing....'
                cloud_thresh = self.cloud_threshold.value

                # Define study area based on user preference
                if self.user_preference.index == 1:
                    file = self.file_selector.selected  
                    self.site = load_boundary(file)
                    self.Map.addLayer(self.site, {}, 'AOI')
                    self.Map.center_object(self.site)
                else:
                    self.site = ee.FeatureCollection(self.Map.draw_last_feature)

                # get widget values
                self.imageType = self.Platform_dropdown.value
                filterType = self.filter_dropdown.value
                self.StartDate = ee.Date.fromYMD(self.start_date.value.year,self.start_date.value.month,self.start_date.value.day)
                self.EndDate = ee.Date.fromYMD(self.end_date.value.year,self.end_date.value.month,self.end_date.value.day)

                boxcar = ee.Kernel.circle(**{'radius':3, 'units':'pixels', 'normalize':True})

                def filtr(img):
                    return img.convolve(boxcar)

                # filter image collection based on date, study area and cloud threshold(depends of datatype)
                if self.imageType == 'Landsat-Collection 1':
                    self.filtered_landsat = load_Landsat_Coll_1(self.site, self.StartDate, self.EndDate, cloud_thresh)
#                     self.filtered_Collection = self.filtered_landsat.map(maskLandsatclouds)
                    self.filtered_Collection = self.filtered_landsat.map(cloudMaskL457)
                elif self.imageType == 'Landsat-Collection 2':
                    self.filtered_landsat = load_Landsat_Coll_2(self.site, self.StartDate, self.EndDate, cloud_thresh)
                    self.filtered_Collection = self.filtered_landsat.map(maskLandsatclouds)
                elif self.imageType == 'Sentinel-2':
                    Collection_before = load_Sentinel2(self.site, self.StartDate, self.EndDate, cloud_thresh)
                    self.filtered_Collection = Collection_before.map(maskS2clouds)
                elif self.imageType == 'Sentinel-1':
                    Collection_before = load_Sentinel1(self.site, self.StartDate, self.EndDate)
                    # apply speckle filter algorithm or smoothing
                    if filterType == 'Gamma MAP':
                        corrected_Collection = Collection_before.map(slope_correction)
                        self.filtered_Collection = corrected_Collection.map(hf.gamma_map)
                    elif filterType == 'Refined-Lee':
                        corrected_Collection = Collection_before.map(slope_correction)
                        self.filtered_Collection = corrected_Collection.map(hf.refined_lee)
                    elif filterType == 'Perona-Malik':
                        corrected_Collection = Collection_before.map(slope_correction)
                        self.filtered_Collection = corrected_Collection.map(hf.perona_malik)
                    elif filterType == 'P-median':
                        corrected_Collection = Collection_before.map(slope_correction)
                        self.filtered_Collection = corrected_Collection.map(hf.p_median)
                    elif filterType == 'Boxcar Convolution':
                        corrected_Collection = Collection_before.map(slope_correction)
                        self.filtered_Collection = corrected_Collection.map(filtr)
                    elif filterType == 'Lee Sigma':
    #                         corrected_Collection = Collection_before.map(ut.slope_correction) # slope correction before lee_sigma fails
                        self.filtered_Collection = Collection_before.map(hf.lee_sigma)
                elif self.imageType == 'USDA NAIP':
                    self.filtered_Collection = load_NAIP(self.site, self.StartDate, self.EndDate)

                # Clip images to study area
                self.clipped_images = self.filtered_Collection.map(self.clipImages)

                # Mosaic same day images
                self.clipped_images = tools.imagecollection.mosaicSameDay(self.clipped_images)

                # Add first image in collection to Map
                first_image = self.clipped_images.first()
                if self.imageType == 'Sentinel-1':
                    self.img_scale = first_image.select(0).projection().nominalScale().getInfo()
                else:
                    bandNames = first_image.bandNames().getInfo()
                    self.img_scale = first_image.select(str(bandNames[0])).projection().nominalScale().getInfo()

                self.Map.addLayer(self.clipped_images.first(), self.visParams, self.imageType)

                # Get no. of processed images
                no_of_images = self.filtered_Collection.size().getInfo()

                # Display number of images
                self.lbl_RetrievedImages.value = str(no_of_images)

                # List of files
                self.file_list = self.filtered_Collection.aggregate_array('system:id').getInfo()
                # display list of files
                self.lst_files.options = self.file_list
                self.extractWater_Button.disabled = False # enable the water extraction button
                self.download_button.disabled = False

            except Exception as e:
                     print(e)
                     print('An error occurred during processing.')
                        
    def Water_Extraction(self, b):
        """
        Function to extract surface water from satellite images

        args:
            None

        returns:
            None
        """
        with self.feedback:
            self.feedback.clear_output()
            try:

                color_palette = self.index_color.value       
                # Function to extract water using NDWI or MNDWI from multispectral images
                def water_index(img):
                    """
                    Function to extract surface water from Landsat and Sentinel-2 images using
                    water extraction indices: NDWI, MNDWI, and AWEI

                    args:
                        Image

                    returns:
                        Image with water mask
                    """
                    index_image = ee.Image(1)
                    if self.water_indices.value == 'NDWI':
                        if self.imageType == 'Landsat-Collection 1' or self.imageType == 'Landsat-Collection 2' or self.imageType == 'Sentinel-2':
                            bands = ['green', 'nir']
                        elif self.imageType == 'USDA NAIP':
                            bands = ['G', 'N']
                        index_image = img.normalizedDifference(bands).rename('waterIndex')\
                            .copyProperties(img, ['system:time_start'])

                    elif self.water_indices.value == 'MNDWI':
                        if self.imageType == 'Landsat-Collection 1' or self.imageType == 'Landsat-Collection 2':
                            bands = ['green', 'swir1']
                            index_image = img.normalizedDifference(bands).rename('waterIndex')\
                                .copyProperties(img, ['system:time_start'])

                        elif self.imageType == 'Sentinel-2':
                            # Resample the swir bands from 20m to 10m
                            resampling_bands = img.select(['swir1','swir2'])
                            img = img.resample('bilinear').reproject(**
                                        {'crs': resampling_bands.projection().crs(),
                                        'scale':10
                                        })
                            bands = ['green', 'swir1']
                            index_image = img.normalizedDifference(bands).rename('waterIndex')\
                                .copyProperties(img, ['system:time_start'])

                    elif self.water_indices.value == 'AWEInsh':
                        index_image = img.expression(
                                '(4 * (GREEN - SWIR1)) - ((0.25 * NIR)+(2.75 * SWIR2))', {
                                    'NIR': img.select('nir'),
                                    'GREEN': img.select('green'),
                                    'SWIR1': img.select('swir1'),
                                    'SWIR2': img.select('swir2')
                                }).rename('waterIndex').copyProperties(img, ['system:time_start'])

                    elif self.water_indices.value == 'AWEIsh':
                        index_image = img.expression(
                                '(BLUE + (2.5 * GREEN) - (1.5 * (NIR + SWIR1)) - (0.25 * SWIR2))', {
                                    'BLUE':img.select('blue'),
                                    'NIR': img.select('nir'),
                                    'GREEN': img.select('green'),
                                    'SWIR1': img.select('swir1'),
                                    'SWIR2': img.select('swir2')
                                }).rename('waterIndex').copyProperties(img, ['system:time_start'])

                    return img.addBands(index_image)

                def water_thresholding(img):
                    # Compute threshold
                    if self.threshold_dropdown.value == 'Simple': # Simple value no dynamic thresholding
                        nd_threshold = self.threshold_value.value
                        water_image = img.select('waterIndex').gt(nd_threshold).rename('water')\
                        .copyProperties(img, ['system:time_start'])
                    elif self.threshold_dropdown.value == 'Otsu':
                        reducers = ee.Reducer.histogram(255,2).combine(reducer2=ee.Reducer.mean(), sharedInputs=True)\
                            .combine(reducer2=ee.Reducer.variance(), sharedInputs= True)

                        histogram = img.select('waterIndex').reduceRegion(
                                        reducer=reducers,
                                        geometry=self.site.geometry(),
                                        scale=self.img_scale,
                                        bestEffort=True)
                        nd_threshold = otsu(histogram.get('waterIndex_histogram')) # get threshold from the nir band

                        water_image = img.select('waterIndex').gt(nd_threshold).rename('water')  
                        water_image = water_image.copyProperties(img, ['system:time_start'])

                    return img.addBands(water_image)

                # Function to extract water from SAR Sentinel 1 images
                def add_S1_waterMask(band):
                    """
                    Function to extract surface water from Sentinel-1 images Otsu algorithm

                    args:
                        Image

                    returns:
                        Image with water mask
                    """
                    def wrap(img):
                        reducers = ee.Reducer.histogram(255,2).combine(reducer2=ee.Reducer.mean(), sharedInputs=True)\
                            .combine(reducer2=ee.Reducer.variance(), sharedInputs= True)
                        histogram = img.select(band).reduceRegion(
                        reducer=reducers,
                        geometry=self.site.geometry(),
                        scale=self.img_scale,
                        bestEffort=True)

                        # Calculate threshold via function otsu (see before)
                        threshold = otsu(histogram.get(band+'_histogram'))

                        # get watermask
                        waterMask = img.select(band).lt(threshold).rename('water')
                #             waterMask = waterMask.updateMask(waterMask) #Remove all pixels equal to 0
                        return img.addBands(waterMask)
                    return wrap

                def maskDSWE_Water(img):
                    nd_threshold = self.threshold_value.value+1
                    waterImage = img.select('dswe').rename('water')
                    water = waterImage.gt(0).And(waterImage.lt(nd_threshold)).copyProperties(img, ['system:time_start'])
                    return img.addBands(water)
                def mask_Water(img):
                    waterMask = img.select('water').selfMask().rename('waterMask').copyProperties(img, ['system:time_start'])
                    return img.addBands(waterMask)

                if self.imageType == 'Sentinel-1':
                    band = self.water_indices.value
                    self.water_images = self.clipped_images.map(add_S1_waterMask(band)).select('water')
                    self.WaterMasks = self.water_images.map(mask_Water)
                    self.visParams = {'min': 0,'max': 1, 'palette': color_palette}
                    self.Map.addLayer(self.WaterMasks.select('waterMask').max(), self.visParams, 'Water')
                elif self.imageType == 'Landsat-Collection 1' or self.imageType == 'Landsat-Collection 2':
                    if self.water_indices.value == 'DSWE':
                        dem = ee.Image('USGS/SRTMGL1_003')
                        self.dswe_images = DSWE(self.filtered_landsat, dem, self.site)
                            # Viz parameters: classes: 0, 1, 2, 3, 4, 9
                        self.dswe_viz = {'min':0, 'max': 9, 'palette': ['000000', '002ba1', '6287ec', '77b800', 'c1bdb6', 
                                                                    '000000', '000000', '000000', '000000', 'ffffff']}
                        self.water_images = self.dswe_images.map(maskDSWE_Water)
                        self.WaterMasks = self.water_images.map(mask_Water)
    #                     Map.addLayer(dswe_images.max(), dswe_viz, 'DSWE')
                    else:
                        self.index_images = self.clipped_images.map(water_index)
                        self.water_images = self.index_images.map(water_thresholding)
                        self.WaterMasks = self.water_images.map(mask_Water)
                    self.Map.addLayer(self.WaterMasks.select('waterMask').max(), {'palette': color_palette}, 'Water')

                else:
                    self.index_images = self.clipped_images.map(water_index)
                    self.water_images = self.index_images.map(water_thresholding)
                    self.WaterMasks = self.water_images.map(mask_Water)
                    self.Map.addLayer(self.WaterMasks.select('waterMask').max(), {'palette': color_palette}, 'Water')

                self.water_Frequency_button.disabled = False
                self.Depths_Button.disabled = False
                self.elev_Methods.disabled = False
                self.plot_button.disabled = False

            except Exception as e:
                     print(e)
                     print('An error occurred during computation.')
 

    def calc_area(self, img):
        """
        Function to calculate area of water pixels

        args:
            Water mask image

        returns:
            Water image with calculated total area of water pixels
        """
        global unit_symbol
        unit = self.area_unit.value
        divisor = 1
        if unit =='Square Km':
            divisor = 1e6
            unit_symbol = 'Sq km'
        elif unit =='Hectares':
            divisor = 1e4
            unit_symbol = 'Ha'
        elif unit =='Square m':
            divisor = 1
            unit_symbol = 'Sq m'
        else:
            divisor = 4047
            unit_symbol = 'acre'

        pixel_area = img.select('waterMask').multiply(ee.Image.pixelArea()).divide(divisor)
        img_area = pixel_area.reduceRegion(**{
                            'geometry': self.site.geometry(),
                            'reducer': ee.Reducer.sum(),
                            'scale': self.img_scale,
                            'maxPixels': 1e13
                            })

        return img.set({'water_area': img_area})
    
    def plot_areas(self, b):
        """
        Function to plot a time series of calculated water area for each water image
        and to cycle through 

        args:
            None

        returns:
            None
        """
        with self.feedback:
            self.feedback.clear_output()
            try:
                global df
                global save_water_data
                save_water_data = True
                # Compute water areas
                water_areas = self.WaterMasks.map(self.calc_area)
                water_stats = water_areas.aggregate_array('water_area').getInfo()

                self.dates = self.WaterMasks.aggregate_array('system:time_start')\
                    .map(lambda d: ee.Date(d).format('YYYY-MM-dd')).getInfo()

                dates_lst = [datetime.strptime(i, '%Y-%m-%d') for i in self.dates]
                y = [item.get('waterMask') for item in water_stats]
                df = pd.DataFrame(list(zip(dates_lst,y)), columns=['Date','Area'])

                self.fig.data = []

                self.fig.add_trace(go.Scatter(x=df['Date'], y=df['Area'], name='Water Hydrograph', 
                        mode='lines+markers', line=dict(dash = 'solid', color ='Blue', width = 0.5)))

                self.fig.layout.title = '<b>Surface Water Area Hydrograph<b>'
                self.fig.layout.titlefont = dict(family="Arial",size=24)
                self.fig.layout.title.x = 0.5
                self.fig.layout.title.y = 0.9

                self.fig.layout.yaxis.title = 'Area ('+unit_symbol+')'

                scatter = self.fig.data[0] # set figure data to scatter for click function

                color_palette = self.index_color.value

                max_Area_value = df['Area'].max()
                min_Area_value = df['Area'].min()
                avg_Area_value = df['Area'].mean()
                self.lbl_Max_Area.value = str(round(max_Area_value, 3))
                self.lbl_Min_Area.value = str(round(min_Area_value, 3))
                self.lbl_Avg_Area.value = str(round(avg_Area_value, 3))

                # Function to select and show images on clicking the graph
                def update_point(trace, points, selector):
                    global wImage
                    global selected_sat
                    date = df['Date'].iloc[points.point_inds].values[0]
                    date = pd.to_datetime(str(date))
                    selected_image = self.WaterMasks.closest(date).first()
                    wImage = selected_image.select('waterMask')
                    self.Map.addLayer(selected_image, self.visParams, self.imageType)
                    if self.water_indices.value == 'DSWE':
                        selected_DWSE = self.dswe_images.closest(date).first()
                        self.Map.addLayer(selected_DWSE.select('dswe'), self.dswe_viz, 'DSWE')
#                         Map.addLayer(wImage, {'palette': color_palette}, 'Water')
                    self.Map.addLayer(wImage, {'palette': color_palette}, 'Water')

                scatter.on_click(update_point)

            except Exception as e:
                    print(e)
                    print('An error occurred during computation.')


    def save_data(self, b):
        """
        Function to save time series to CSV file
        args:
            None

        returns:
            None
        """
        with self.feedback:
            self.feedback.clear_output()
            try:
                if save_water_data==True:
                    filename = self.file_selector1.selected
                    water_df = df
                    water_df = water_df.rename(columns={'Area':'Area, '+unit_symbol})
                    water_df.to_csv(filename, index=False)
                elif save_water_data==False:
                    filename = self.file_selector1.selected
                    filtered_df = depths_df.drop(columns=['reducer'])
                    filtered_df = filtered_df[['date','Depth']]
                    filtered_df = filtered_df.rename(columns={'Depth':'Depth, m'})
                    filtered_df.to_csv(filename, index=False)

            except Exception as e:
                    print(e)
                    print('Data save error')


    def dowload_images(self, b):
        with self.feedback:
            self.feedback.clear_output()
            try:
                path = self.folder_selector.selected_path
                folder = self.folder_name.value
                name_Pattern = '{sat}_{system_date}_{imgType}'
                date_pattern = 'YYYY-MM-dd'
                extra = dict(sat=self.imageType, imgType = 'Water')
                if self.files_to_download.index == 0:
                    download_images = self.clipped_images
                    extra = dict(sat=self.imageType, imgType = 'Satellite')
                elif self.files_to_download.index == 1:
                    download_images = self.WaterMasks.select('waterMask')
                    extra = dict(sat=self.imageType, imgType = 'Water')
                elif self.files_to_download.index == 2:
                    download_images = ee.ImageCollection([water_occurence])
                    name_Pattern = '{sat}_{start}_{end}_{imgType}'
                    extra = dict(sat=self.imageType, imgType = 'Frequency', start=self.start_date.value.strftime("%x"),
                                 end=self.end_date.value.strftime("%x"))
                elif self.files_to_download.index == 3:
                    download_images = self.depth_maps
                    extra = dict(sat=self.imageType, imgType = 'Depth')
                else:
                    download_images = self.dswe_images
                    extra = dict(sat=self.imageType, imgType = 'DSWE')

                if self.download_location.index == 0:
                    task = geetools.batch.Export.imagecollection.toDrive(
                        collection = download_images,
                        folder = folder,
                        region = self.site.geometry(),
                        namePattern = name_Pattern,
                        scale = self.img_scale,
                        datePattern=date_pattern,
                        extra = extra,
                        verbose=True,
                        maxPixels = int(1e13))
                    task
                else:
                    export_image_collection_to_local(download_images,path,name_Pattern,date_pattern,extra,self.img_scale,region=self.site)

                print('Download complete!!')

            except Exception as e:
                    print(e)
                    print('Download could not be completed')
                    
    def water_frequency(self, b):
        with self.feedback:
            self.feedback.clear_output()
            try:
                global water_frequency
                global water_occurence
                water_occurence =  self.water_images.select('water').reduce(ee.Reducer.sum())
                water_frequency = water_occurence.divide(self.water_images.size()).multiply(100)
                Max_Water_Map = self.WaterMasks.select('waterMask').max()
                water_frequency = water_frequency.updateMask(Max_Water_Map)
                self.freqParams = {'min':0, 'max':100, 'palette': ['white','lightblue','blue','darkblue']}
                self.Map.addLayer(water_frequency, self.freqParams, 'Water Frequency')

                colors = self.freqParams['palette']
                vmin = self.freqParams['min']
                vmax = self.freqParams['max']

                self.Map.add_colorbar_branca(colors=colors, vmin=vmin, vmax=vmax, layer_name="Water Frequency")
            except Exception as e:
                        print(e)
                        print('Frequency computation could not be completed')

    def get_dates(self, col):
        dates = ee.List(col.toList(col.size()).map(lambda img: ee.Image(img).date().format()))
        return dates

    # Function to count water pixels for each image   
    def CountWaterPixels(self, img):
        count = img.select('waterMask').reduceRegion(ee.Reducer.sum(), self.site).values().get(0)
        return img.set({'pixel_count': count})

    def calc_depths(self, b):
        with self.feedback:
            self.feedback.clear_output()
            try:

                if self.elevData_options.value =='NED':
                    demSource = 'USGS/NED'
                    band = 'elevation'
                elif self.elevData_options.value =='SRTM':
                    demSource = 'USGS/SRTMGL1_003'
                    band = 'elevation'
                else:
                    demSource = str(self.userDEM.value)
                    band = 'b1'

                dem = ee.Image(demSource).select(band).clip(self.site)

                # get water pixel count per image
                countImages = self.WaterMasks.map(self.CountWaterPixels)

                # Filter out only images containing water pixels to avoid error in depth estimation
                self.filtered_Water_Images = countImages.filter(ee.Filter.gt('pixel_count', 0))
                
                if self.elev_Methods.value == 'Random Forest':
                    if self.rf_ee_classifier is not None:
                        collection_with_depth_variables = self.WaterMasks.map(add_depth_variables)
                        self.depth_maps = collection_with_depth_variables.map(RF_Depth_Estimate(self.rf_ee_classifier))
                    else:
                        filename = 'ML_models/Landsat_RF_model.sav'
                        feature_names = ['mod_green','mod_swir1']
                        loaded_model = pickle.load(open(filename, 'rb'))
                        trees =  ml.rf_to_strings(loaded_model,feature_names)
                        self.rf_ee_classifier = ml.strings_to_classifier(trees)
                        collection_with_depth_variables = self.WaterMasks.map(add_depth_variables)
                        self.depth_maps = collection_with_depth_variables.map(RF_Depth_Estimate(self.rf_ee_classifier))
                elif self.elev_Methods.value == 'Mod_Stumpf':
                    collection_with_depth_variables = self.WaterMasks.map(add_depth_variables)
                    self.depth_maps = collection_with_depth_variables.map(Mod_Stumpf_Depth_Estimate)
                elif self.elev_Methods.value == 'Mod_Lyzenga':
                    collection_with_depth_variables = self.WaterMasks.map(add_depth_variables)
                    self.depth_maps = collection_with_depth_variables.map(Mod_Lyzenga_Depth_Estimate)
                elif self.elev_Methods.value == 'FwDET':
                    self.depth_maps = self.filtered_Water_Images.map(FwDET_Depth_Estimate(dem))
                else:
                    self.depth_maps = self.filtered_Water_Images.map(estimateDepths_FromDEM(dem, self.site, self.img_scale))

                max_depth_map = self.depth_maps.select('Depth').max()
                maxVal = max_depth_map.reduceRegion(ee.Reducer.max(),self.site, self.img_scale).values().get(0).getInfo()

                self.depthParams = {'min':0, 'max':round(maxVal,1), 'palette': ['1400f7','00f4e8','f4f000','f40000','960424']}
                #['006633', 'E5FFCC', '662A00', 'D8D8D8', 'F5F5F5']
                self.Map.addLayer(max_depth_map, self.depthParams, 'Depth')
                colors = self.depthParams['palette']
                self.Map.add_colorbar_branca(colors=colors, vmin=0, vmax=round(maxVal,1), layer_name='Depth')
                self.depth_plot_button.disabled = False # enable depth plotting

            except Exception as e:
                    print(e)

    def plot_depths(self, b):
        with self.feedback:
            self.feedback.clear_output()
            try: 
                global depths_df
                global save_water_data
                save_water_data = False
                if self.point_preference.index == 0:
                    point = ee.FeatureCollection(self.Map.draw_last_feature)
                else:
                    coordinates = self.coordinates_textbox.value
                    xy = coordinates.split(',')
                    floated_xy = [float(i) for i in xy]
                    point = ee.Geometry.Point(floated_xy)
                    self.Map.addLayer(point, {}, 'Depth Point')

                ts_1 = self.depth_maps.getTimeSeriesByRegion(geometry = point,
                                          bands = ['Depth'],
                                          reducer = [ee.Reducer.mean()],
                                          scale = self.img_scale)

                depths_df = geemap.ee_to_pandas(ts_1)
                depths_df[depths_df == -9999] = np.nan
                depths_df = depths_df.fillna(0)
                depths_df['date'] = pd.to_datetime(depths_df['date'],infer_datetime_format = True)

                self.fig.data = []

                self.fig.add_trace(go.Scatter(x=depths_df['date'], y=depths_df['Depth'], name='Depth Hydrograph', 
                            mode='lines+markers', line=dict(dash = 'solid', color ='Red', width = 0.5)))

                self.fig.layout.yaxis.title = '<b>Depth (m)<b>'
                self.fig.layout.title = '<b>Water Depth Hydrograph<b>'
                self.fig.layout.titlefont = dict(family="Arial",size=24)
                self.fig.layout.title.x = 0.5
                self.fig.layout.title.y = 0.9

                scatter = self.fig.data[0] # set figure data to scatter for click function

                max_Depth_value = depths_df['Depth'].max()
                min_Depth_value = depths_df['Depth'].min()
                avg_Depth_value = depths_df['Depth'].mean()
                self.lbl_Max_Depth.value = str(round(max_Depth_value, 3))
                self.lbl_Min_Depth.value = str(round(min_Depth_value, 3))
                self.lbl_Avg_Depth.value = str(round(avg_Depth_value, 3))

                color_palette = self.index_color.value

                # Function to select and show water image on clicking the graph
                def update_point(trace, points, selector):
                    global wImage
                    global selected_sat
                    date = depths_df['date'].iloc[points.point_inds].values[0]
                    date = pd.to_datetime(str(date))
                    selected_image = self.depth_maps.closest(date)
                    wImage = selected_image.select('waterMask')
#                     selected_sat = clipped_images.closest(date).first()
                    depthImage = selected_image.select('Depth')
                    self.Map.addLayer(selected_image, self.visParams, self.imageType)
                    self.Map.addLayer(wImage, {'palette': color_palette}, 'Water')
                    self.Map.addLayer(depthImage, self.depthParams, 'Depth')

                scatter.on_click(update_point)

            except Exception as e:
                print(e)
                print('Please draw a point or enter coordinates')
