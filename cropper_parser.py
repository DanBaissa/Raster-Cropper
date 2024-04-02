import argparse
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import rasterio
from rasterio.mask import mask
from shapely.geometry import mapping
import os
import glob
import tempfile

# Load the shapefile
shapefile = gpd.read_file('Data/World_Countries/World_Countries_Generalized.shp')

def crop_raster_with_shapefile(raster_path, country_shape, output_path):
    with rasterio.open(raster_path) as src:
        image_data = src.read(1) + 1
        country_shape = country_shape.to_crs(src.crs)
        with tempfile.NamedTemporaryFile(delete=False, suffix='.tif') as temp_file:
            with rasterio.open(temp_file.name, 'w', **src.meta) as temp_dst:
                temp_dst.write(image_data, 1)

            with rasterio.open(temp_file.name) as temp_src:
                out_image, out_transform = mask(temp_src, [mapping(geom) for geom in country_shape.geometry], crop=True, invert=False)
                out_meta = temp_src.meta.copy()

    out_meta.update({"driver": "GTiff", "height": out_image.shape[1], "width": out_image.shape[2], "transform": out_transform})
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with rasterio.open(output_path, "w", **out_meta) as dest:
        dest.write(out_image[0], 1)
    os.remove(temp_file.name)

def run(raster_dir, output_dir, country_name, view_rasters):
    country = shapefile[shapefile['COUNTRY'] == country_name]
    raster_files = glob.glob(os.path.join(raster_dir, '*.tif'))

    for raster_file in raster_files:
        output_file = os.path.join(output_dir, os.path.basename(raster_file))
        crop_raster_with_shapefile(raster_file, country, output_file)

        if view_rasters:
            with rasterio.open(output_file) as src:
                img = src.read(1)
            fig, (ax1, ax2) = plt.subplots(ncols=2, figsize=(12, 6))
            ax1.imshow(img, cmap='turbo')
            ax1.set_title("Standard")
            ax2.imshow(np.log1p(img), cmap='turbo')
            ax2.set_title("Log transformed")
            plt.show()

def parse_arguments():
    parser = argparse.ArgumentParser(description="Crop rasters using a specified country from a shapefile and optionally display the results.")
    parser.add_argument("--raster-dir", required=True, help="Directory containing raster files.")
    parser.add_argument("--output-dir", required=True, help="Directory to save cropped rasters.")
    parser.add_argument("--country", required=True, help="Name of the country to use for cropping.")
    parser.add_argument("--view-rasters", action='store_true', help="Set this flag to view rasters after cropping.")
    return parser.parse_args()

def main():
    args = parse_arguments()
    run(args.raster_dir, args.output_dir, args.country, args.view_rasters)

if __name__ == "__main__":
    main()
