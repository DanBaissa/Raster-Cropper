import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import rasterio
from rasterio.mask import mask
from shapely.geometry import mapping
import os
import tempfile

# Load the shapefile
shapefile = gpd.read_file('Data/World_Countries/World_Countries_Generalized.shp')

def crop_raster_with_shapefile(raster_path, country_shape, output_path):
    print('Opening raster file...')
    with rasterio.open(raster_path) as src:
        # Load the raster data into a numpy array and add 1 to all elements
        print('Reading raster data...')
        image_data = src.read(1) + 1

        # Ensure the CRS of the raster and shapefile match
        print('Ensuring CRS match...')
        country_shape = country_shape.to_crs(src.crs)

        # Create a temporary raster file with the adjusted data
        print('Creating temporary raster file...')
        with tempfile.NamedTemporaryFile(delete=False, suffix='.tif') as temp_file:
            with rasterio.open(temp_file.name, 'w', **src.meta) as temp_dst:
                temp_dst.write(image_data, 1)

        # Crop the adjusted raster with the shapefile
        print('Cropping raster file...')
        with rasterio.open(temp_file.name) as temp_src:
            out_image, out_transform = mask(temp_src, [mapping(geom) for geom in country_shape.geometry], crop=True, invert=False)
            out_meta = temp_src.meta.copy()

    # Update the metadata
    print('Updating metadata...')
    out_meta.update({
        "driver": "GTiff",
        "height": out_image.shape[1],
        "width": out_image.shape[2],
        "transform": out_transform
    })

    # Write the cropped raster to a new file
    print('Writing cropped raster to new file...')
    with rasterio.open(output_path, "w", **out_meta) as dest:
        dest.write(out_image[0], 1)  # Select the first band

    # Delete the temporary file
    print('Deleting temporary file...')
    os.remove(temp_file.name)

    print('Finished cropping raster file.')

def select_raster_file():
    file_path = filedialog.askopenfilename()
    raster_file_var.set(file_path)

def select_output_file():
    file_path = filedialog.asksaveasfilename(defaultextension=".tif")
    output_file_var.set(file_path)

def run():
    try:
        print('Running...')
        country = shapefile[shapefile['COUNTRY'] == country_var.get()]
        crop_raster_with_shapefile(raster_file_var.get(), country, output_file_var.get())
        print('Done.')
        root.update()
    except Exception as e:
        messagebox.showerror("Error", str(e))

root = tk.Tk()

raster_file_var = tk.StringVar()
output_file_var = tk.StringVar()
country_var = tk.StringVar()

# Get sorted unique country names
country_options = sorted(shapefile['COUNTRY'].unique())

raster_file_button = tk.Button(root, text="Select Raster File", command=select_raster_file)
raster_file_button.pack()

output_file_button = tk.Button(root, text="Select Output File", command=select_output_file)
output_file_button.pack()

country_dropdown = ttk.Combobox(root, textvariable=country_var)
country_dropdown['values'] = country_options
country_dropdown.current(0)  # Set default value to first option
country_dropdown.pack()

run_button = tk.Button(root, text="Run", command=run)
run_button.pack()

root.mainloop()
