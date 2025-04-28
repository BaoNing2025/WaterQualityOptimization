# cut_raster_by_buffer.py
import geopandas as gpd
import rasterio
from rasterio.mask import mask
import os

def cut_raster_by_buffer(raster_path, buffer_shp_path, output_raster_path):
    """
    Cut raster data based on a buffer shapefile.

    Args:
        raster_path (str): Path to the input raster (.tif).
        buffer_shp_path (str): Path to the buffer shapefile (.shp).
        output_raster_path (str): Path where the output raster will be saved.
    """

    # Check if input files exist
    if not os.path.exists(raster_path):
        raise FileNotFoundError(f"Raster file not found: {raster_path}")
    if not os.path.exists(buffer_shp_path):
        raise FileNotFoundError(f"Buffer shapefile not found: {buffer_shp_path}")

    # Read river buffer shapefile
    river_buffer_gdf = gpd.read_file(buffer_shp_path)

    # Open raster data
    with rasterio.open(raster_path) as src:
        # Check and align CRS
        if river_buffer_gdf.crs != src.crs:
            print(f"CRS mismatch detected. Converting buffer CRS to match raster CRS...")
            river_buffer_gdf = river_buffer_gdf.to_crs(src.crs)
            print(f"Buffer CRS after conversion: {river_buffer_gdf.crs}")
        else:
            print("Buffer and raster CRS match.")

        # Cut raster using buffer geometry
        try:
            out_image, out_transform = mask(src, river_buffer_gdf.geometry, crop=True)

            # Update metadata
            out_meta = src.meta.copy()
            out_meta.update({
                "driver": "GTiff",
                "height": out_image.shape[1],
                "width": out_image.shape[2],
                "transform": out_transform
            })

            # Save output raster
            with rasterio.open(output_raster_path, 'w', **out_meta) as dest:
                dest.write(out_image)

            print(f"Raster successfully clipped and saved to: {output_raster_path}")

        except ValueError as e:
            print(f"Error during raster clipping: {e}")

if __name__ == "__main__":
    # Example usage
    raster_path = "your_raster_path"
    buffer_shp_path = "your_buffer_shapefile_path"
    output_raster_path = "your_output_raster_save_path"
    cut_raster_by_buffer(raster_path, buffer_shp_path, output_raster_path)
