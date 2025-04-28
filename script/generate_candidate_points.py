# generate_candidate_points.py

import geopandas as gpd
from shapely.geometry import LineString, MultiLineString, Point
from shapely.ops import substring, nearest_points
import rasterio
from rasterio.plot import show
import matplotlib.pyplot as plt
import pandas as pd
import os

plt.rcParams['font.sans-serif'] = ['STSong']
plt.rcParams['axes.unicode_minus'] = False

def load_geodata(rivers_path, intersections_path, sections_path):
    """Load river network, river intersections, and monitoring section points."""
    river_gdf = gpd.read_file(rivers_path)
    intersection_gdf = gpd.read_file(intersections_path)
    duanmian_gdf = gpd.read_file(sections_path)

    print("River CRS:", river_gdf.crs)
    print("Intersection CRS:", intersection_gdf.crs)
    print("Monitoring Sections CRS:", duanmian_gdf.crs)

    return river_gdf, intersection_gdf, duanmian_gdf

def plot_river_and_sections(river_gdf, duanmian_gdf):
    """Plot river lines and monitoring sections for visual inspection."""
    fig, ax = plt.subplots(figsize=(10, 10))
    river_gdf.plot(ax=ax, color='blue', label='Rivers')
    duanmian_gdf.plot(ax=ax, color='red', marker='o', label='Sections')
    plt.legend()
    plt.show()

def create_candidate_points(line, distance_interval, existing_points):
    """Create candidate points along a line geometry at a fixed interval."""
    total_length = line.length
    candidate_points = []
    current_distance = 0

    while current_distance <= total_length:
        point = line.interpolate(total_length - current_distance)
        point_rounded = (round(point.x, 6), round(point.y, 6))
        if point_rounded not in existing_points:
            candidate_points.append(point)
            existing_points.add(point_rounded)
        current_distance += distance_interval

    return candidate_points

def generate_candidate_shapefile(river_gdf, output_path, distance_interval=10000, start_id=7):
    """Generate candidate monitoring points along rivers and save as a shapefile."""
    all_candidate_points = []
    existing_points = set()

    for river in river_gdf.geometry:
        if isinstance(river, LineString):
            points = create_candidate_points(river, distance_interval, existing_points)
            all_candidate_points.extend(points)
        elif isinstance(river, MultiLineString):
            for sub_line in river.geoms:
                points = create_candidate_points(sub_line, distance_interval, existing_points)
                all_candidate_points.extend(points)

    candidate_points_gdf = gpd.GeoDataFrame(geometry=all_candidate_points, crs=river_gdf.crs)
    candidate_points_gdf['point_id'] = range(start_id, start_id + len(candidate_points_gdf))

    candidate_points_gdf.to_file(output_path)
    print(f"Generated {len(candidate_points_gdf)} candidate points.")
    print("Candidate points CRS:", candidate_points_gdf.crs)

    return candidate_points_gdf

def merge_with_retained_sections(candidate_points_gdf, retained_points_path, output_path):
    """Merge candidate points with retained sections and save as a new shapefile."""
    retain_points_gdf = gpd.read_file(retained_points_path)

    combined_gdf = pd.concat([retain_points_gdf, candidate_points_gdf], ignore_index=True)
    combined_gdf['FID'] = range(1, len(combined_gdf) + 1)

    combined_gdf.to_file(output_path, encoding='utf-8')
    print(f"Merged candidate and retained points. Saved to {output_path}.")

def main():
    # Paths
    rivers_path='your_rivers_path',
    intersections_path='your_intersections_path',
    sections_path='your_sections_path',
    retained_sections_path='your_retained_sections_path',
    candidate_points_path='your_candidate_points_save_path',
    merged_output_path='your_merged_output_path'

    # Load data
    river_gdf, intersection_gdf, duanmian_gdf = load_geodata(
        rivers_path, intersections_path, sections_path
    )
    # Optional: Visual check
    plot_river_and_sections(river_gdf, duanmian_gdf)

    # Generate candidate points
    candidate_points_gdf = generate_candidate_shapefile(river_gdf, candidate_points_path)

    # Merge with retained sections
    merge_with_retained_sections(candidate_points_gdf, retained_sections_path, merged_output_path)

if __name__ == "__main__":
    main()
