# optimize_monitoring_points.py

import geopandas as gpd
import rasterio
import numpy as np
import matplotlib.pyplot as plt
import os
from genetic_algorithm import GeneticAlgorithm

def load_data(rivers_path, candidate_points_path, buffer_path, raster_path):
    """Load river data, candidate points, buffer zones, and human activity raster."""
    river_gdf = gpd.read_file(rivers_path)
    candidate_points_gdf = gpd.read_file(candidate_points_path)
    buffer_gdf = gpd.read_file(buffer_path)
    human_activity_raster = rasterio.open(raster_path)

    if buffer_gdf.crs != human_activity_raster.crs:
        buffer_gdf = buffer_gdf.to_crs(human_activity_raster.crs)

    return river_gdf, candidate_points_gdf, buffer_gdf, human_activity_raster

def calculate_total_activity(raster_path):
    """Calculate total human activity intensity from raster."""
    with rasterio.open(raster_path) as src:
        data = src.read(1)
        nodata_value = src.nodata
        data = np.where(data == nodata_value, np.nan, data)
        return np.nansum(data)

def save_best_individual_points(candidate_points_gdf, best_individual, num_points, output_dir):
    """Save the selected monitoring points of the best individual."""
    selected_indices = np.where(best_individual.chromosome == 1)[0]
    selected_points_gdf = candidate_points_gdf.iloc[selected_indices]

    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, f"best_monitoring_points_{num_points}_points.shp")

    selected_points_gdf.to_file(file_path, encoding='utf-8')
    print(f"✅ Saved {len(selected_points_gdf)} points to {file_path}")

def plot_best_coverage(best_coverage_results):
    """Plot the best coverage ratio for different numbers of points."""
    plt.figure(figsize=(10, 6))
    plt.plot(list(best_coverage_results.keys()), [v * 100 for v in best_coverage_results.values()], marker='o', linestyle='-', color='b')

    for num_points, coverage in best_coverage_results.items():
        plt.text(num_points, coverage * 100, f'{coverage * 100:.2f}%', fontsize=8, ha='right', va='bottom')

    plt.xlabel('Number of Monitoring Points')
    plt.ylabel('Best Coverage (%)')
    plt.title('Best Coverage vs Number of Monitoring Points')
    plt.grid(True)
    plt.show()

def main(
    rivers_path='your_rivers_path',
    candidate_points_path='your_candidate_points_path',
    buffer_path='your_buffer_path',
    raster_path='your_raster_path',
    output_dir='your_output_directory'
):
    river_gdf, candidate_points_gdf, buffer_gdf, human_activity_raster = load_data(
        rivers_path, candidate_points_path, buffer_path, raster_path
    )

    total_value = calculate_total_activity(raster_path)

    candidate_points_fid = np.array(candidate_points_gdf['point_id'])
    fixed_indices = candidate_points_gdf[~candidate_points_gdf['编号'].isnull()].index.to_numpy()

    num_candidates = len(candidate_points_gdf)
    min_points = len(fixed_indices)
    increment = 22
    max_points = min_points + increment
    base_generations = 50
    runs_per_point_count = 2

    pop_size = 50
    crossover_rate = 0.8
    mutation_rate = 0.08

    best_coverage_results = {}
    best_individuals = {}

    for num_points in range(min_points, max_points + 1, increment):
        best_coverages = []
        individuals = []

        adjusted_generations = base_generations + (num_points - min_points) // increment * 10

        for run_number in range(runs_per_point_count):
            ga = GeneticAlgorithm(
                pop_size=pop_size,
                num_candidates=num_candidates,
                crossover_rate=crossover_rate,
                mutation_rate=mutation_rate,
                max_generations=adjusted_generations,
                num_selected_points=num_points,
                fixed_indices=fixed_indices
            )

            best_individual = ga.evolve(candidate_points_gdf, buffer_gdf, human_activity_raster)

            total_covered_intensity = best_individual.fitness
            coverage_ratio = total_covered_intensity / total_value

            best_coverages.append(coverage_ratio)
            individuals.append(best_individual)

        max_coverage = max(best_coverages)
        best_coverage_results[num_points] = max_coverage

        best_index = best_coverages.index(max_coverage)
        best_individuals[num_points] = individuals[best_index]

        save_best_individual_points(candidate_points_gdf, best_individuals[num_points], num_points, output_dir)

    plot_best_coverage(best_coverage_results)

if __name__ == "__main__":
    main(
        rivers_path='your_rivers_path',
        candidate_points_path='your_candidate_points_path',
        buffer_path='your_buffer_path',
        raster_path='your_raster_path',
        output_dir='your_output_directory'
    )
