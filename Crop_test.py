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

# Filter the shapefile for a specific country
country = shapefile[shapefile['COUNTRY'] == 'Ethiopia']

def crop_raster_with_shapefile(raster_path, country_shape, output_path):
    with rasterio.open(raster_path) as src:
        # Load the raster data into a numpy array and add 1 to all elements
        image_data = src.read(1) + 1

        # Ensure the CRS of the raster and shapefile match
        # Reproject the GeoDataFrame to the CRS of the raster
        country_shape = country_shape.to_crs(src.crs)

        # Create a temporary raster file with the adjusted data
        with tempfile.NamedTemporaryFile(delete=False, suffix='.tif') as temp_file:
            with rasterio.open(temp_file.name, 'w', **src.meta) as temp_dst:
                temp_dst.write(image_data, 1)

        # Crop the adjusted raster with the shapefile
        with rasterio.open(temp_file.name) as temp_src:
            out_image, out_transform = mask(temp_src, [mapping(geom) for geom in country_shape.geometry], crop=True, invert=False)
            out_meta = temp_src.meta.copy()

    # Update the metadata
    out_meta.update({
        "driver": "GTiff",
        "height": out_image.shape[1],
        "width": out_image.shape[2],
        "transform": out_transform
    })

    # Write the cropped raster to a new file
    with rasterio.open(output_path, "w", **out_meta) as dest:
        dest.write(out_image[0], 1)  # Select the first band

    # Delete the temporary file
    os.remove(temp_file.name)

# Example usage:
output_file = "test/test.tif"
crop_raster_with_shapefile("test/Ethiopia_2021001.tif", country, output_file)

# Open the resulting raster file
with rasterio.open(output_file) as src:
    img = src.read(1)

# Plotting
fig, (ax1, ax2) = plt.subplots(ncols=2, figsize=(12, 6))

# Standard plot
ax1.imshow(img, cmap='turbo')
ax1.set_title("Standard")

# Log transformed plot
# Adding small constant to avoid log(0)
ax2.imshow(np.log1p(img), cmap='turbo')
ax2.set_title("Log transformed")

plt.show()
