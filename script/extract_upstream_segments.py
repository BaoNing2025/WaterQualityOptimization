
# extract_upstream_segments.py

import geopandas as gpd
from shapely.geometry import LineString, MultiLineString
from shapely.ops import substring
import pandas as pd
import os

def load_geodata(rivers_path, intersections_path, sections_path):
    """Load river lines, river intersections, and monitoring section points."""
    river_gdf = gpd.read_file(rivers_path)
    intersection_gdf = gpd.read_file(intersections_path)
    duanmian_gdf = gpd.read_file(sections_path)
    return river_gdf, intersection_gdf, duanmian_gdf

def create_upstream_segments(start_point, buffer_length, river_gdf, intersection_gdf, visited_confluences, total_upstream_segments):
    """Recursively extract upstream segments from a start point."""
    if buffer_length <= 1:
        return total_upstream_segments

    current_point = start_point.geometry.iloc[0]
    point_buffer = current_point.buffer(50)
    point_gdf = gpd.GeoDataFrame(geometry=[point_buffer], crs=river_gdf.crs)

    containing_rivers = gpd.sjoin(river_gdf, point_gdf, how="inner", predicate='intersects')

    if containing_rivers.empty:
        return total_upstream_segments

    for _, row in containing_rivers.iterrows():
        river_line = row.geometry
        nearest_point = river_line.interpolate(river_line.project(current_point))
        start_distance = river_line.project(nearest_point)
        end_distance = max(start_distance - buffer_length, 0)

        upstream_segment = substring(river_line, end_distance, start_distance)

        if upstream_segment.is_empty or upstream_segment.length < 1.0:
            continue

        total_upstream_segments.append(upstream_segment)

        segment_gdf = gpd.GeoDataFrame(geometry=[upstream_segment], crs=river_gdf.crs)
        intersecting_confluences = gpd.sjoin(intersection_gdf, segment_gdf, how="inner", predicate='intersects')

        if not intersecting_confluences.empty:
            for _, conf_row in intersecting_confluences.iterrows():
                confluence_geom = conf_row.geometry
                confluence_key = confluence_geom.wkt

                if confluence_key in visited_confluences:
                    continue

                visited_confluences.add(confluence_key)
                segment_length = upstream_segment.length
                new_buffer = buffer_length - segment_length

                next_start = gpd.GeoDataFrame(geometry=[confluence_geom], crs=river_gdf.crs)
                create_upstream_segments(next_start, new_buffer, river_gdf, intersection_gdf, visited_confluences, total_upstream_segments)

    return total_upstream_segments

def extract_all_upstream_segments(
    rivers_path='your_rivers_path',
    intersections_path='your_intersections_path',
    sections_path='your_sections_path',
    output_path='your_output_path',
    buffer_length=2000
):
    """Main workflow to extract upstream segments for each section point."""
    river_gdf, intersection_gdf, duanmian_gdf = load_geodata(rivers_path, intersections_path, sections_path)

    river_gdf = river_gdf.to_crs(epsg=32651)
    intersection_gdf = intersection_gdf.to_crs(epsg=32651)
    duanmian_gdf = duanmian_gdf.to_crs(epsg=32651)

    all_control_segments = []

    for idx, selected_feature in duanmian_gdf.iterrows():
        start_point = gpd.GeoDataFrame(geometry=[selected_feature.geometry], crs=river_gdf.crs)
        current_geom = selected_feature.geometry

        is_junction = not intersection_gdf[intersection_gdf.geometry.distance(current_geom) < 1e-6].empty

        control_geoms = []

        if not is_junction:
            visited_confluences = set()
            upstream_segments = create_upstream_segments(
                start_point, buffer_length, river_gdf, intersection_gdf, visited_confluences, total_upstream_segments=[]
            )
            upstream_segments = [seg for seg in upstream_segments if isinstance(seg, (LineString, MultiLineString))]
            merged_upstream = gpd.GeoSeries(upstream_segments).unary_union if upstream_segments else None
            if merged_upstream:
                control_geoms.append(merged_upstream)

        if control_geoms:
            merged_control_segment = gpd.GeoSeries(control_geoms).unary_union
            result_gdf = gpd.GeoDataFrame(geometry=[merged_control_segment], crs=river_gdf.crs)
            result_gdf['section_id'] = selected_feature['point_id']
            all_control_segments.append(result_gdf)

    if all_control_segments:
        combined_gdf = gpd.GeoDataFrame(pd.concat(all_control_segments, ignore_index=True))
        combined_gdf = combined_gdf[combined_gdf.geometry.apply(lambda geom: isinstance(geom, (LineString, MultiLineString)))]
        combined_gdf.to_file(output_path, encoding='utf-8')
        print("✅ All upstream control segments successfully saved.")
    else:
        print("⚠️ No valid upstream segments generated.")

if __name__ == "__main__":
    extract_all_upstream_segments(
        rivers_path='your_rivers_path',
        intersections_path='your_intersections_path',
        sections_path='your_sections_path',
        output_path='your_output_shapefile_path'
    )
