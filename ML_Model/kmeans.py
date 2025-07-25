import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from typing import List, Tuple
import json
import sys

def load_coordinates_from_json(filename: str) -> List[Tuple[float, float]]:
  try:
    with open(filename, 'r') as file:
      data = json.load(file)
    
    coordinates = []
    if isinstance(data, list):
      for item in data:
        if isinstance(item, dict) and 'lat' in item and 'lon' in item:
          coordinates.append((float(item['lat']), float(item['lon'])))
        elif isinstance(item, list) and len(item) == 2:
          coordinates.append((float(item[0]), float(item[1])))
        else:
          print(f"Warning: Skipping invalid coordinate format: {item}")
      return coordinates
    else:
      raise ValueError("JSON file should contain a list of coordinates")
          
  except FileNotFoundError:
    print(f"Error: File '{filename}' not found")
    sys.exit(1)
  except json.JSONDecodeError:
    print(f"Error: Invalid JSON format in '{filename}'")
    sys.exit(1)
  except Exception as e:
    print(f"Error reading file: {e}")
    sys.exit(1)

def find_outlier_index(coordinates: List[Tuple[float, float]]) -> int:
  if len(coordinates) < 3:
    return 1
  
  coords_array = np.array(coordinates)
  scaler = StandardScaler()
  coords_scaled = scaler.fit_transform(coords_array)
  
  if len(coordinates) == 3:
    distances = np.linalg.norm(coords_scaled - np.mean(coords_scaled, axis=0), axis=1)
    return int(np.argmax(distances))
  
  # pyright: reportArgumentType=false
  kmeans = KMeans(n_clusters=2, random_state=42, n_init=10)
  cluster_labels = kmeans.fit_predict(coords_scaled)
  
  unique_labels, counts = np.unique(cluster_labels, return_counts=True)
  
  if len(unique_labels) == 1:
    distances = np.linalg.norm(coords_scaled - np.mean(coords_scaled, axis=0), axis=1)
    return int(np.argmax(distances))
  
  outlier_cluster = unique_labels[np.argmin(counts)]
  outlier_indices = np.where(cluster_labels == outlier_cluster)[0]
  
  if len(outlier_indices) == 1:
    return int(outlier_indices[0])
  
  elif len(outlier_indices) > 1:
    outlier_points = coords_scaled[outlier_indices]
    cluster_center = kmeans.cluster_centers_[outlier_cluster]
    
    distances = np.linalg.norm(outlier_points - cluster_center, axis=1)
    most_distant_idx = np.argmax(distances)
    
    return int(outlier_indices[most_distant_idx])
  
  else:
    distances = np.linalg.norm(coords_scaled - np.mean(coords_scaled, axis=0), axis=1)
    return int(np.argmax(distances))

if __name__ == "__main__":
  import argparse
  parser = argparse.ArgumentParser()
  parser.add_argument('filename', help='JSON file with coordinates')
  parser.add_argument('--quiet', action='store_true', help='Print only the outlier index')
  args = parser.parse_args()

  filename = args.filename
  quiet = args.quiet

  coordinates = load_coordinates_from_json(filename)

  try:
    outlier_index = find_outlier_index(coordinates)
    # If outlier is HQ (index 0), pick next most distant point
    if outlier_index == 0 and len(coordinates) > 1:
      coords_array = np.array(coordinates)
      scaler = StandardScaler()
      coords_scaled = scaler.fit_transform(coords_array)
      distances = np.linalg.norm(coords_scaled - np.mean(coords_scaled, axis=0), axis=1)
      outlier_index = 1 + np.argmax(distances[1:])
    if quiet:
      print(outlier_index)
    else:
      print("KMeans Outlier Detection")
      print("=" * 30)
      print(f"Loaded {len(coordinates)} coordinates:")
      for i, coord in enumerate(coordinates):
        print(f"  {i}: {coord}")
      print(f"\nOutlier index: {outlier_index}")
      print(f"Outlier coordinates: {coordinates[outlier_index]}")
  except ValueError as e:
    print(f"Error: {e}")
    sys.exit(1)