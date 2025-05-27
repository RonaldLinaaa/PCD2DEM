import open3d as o3d
o3d.utility.set_verbosity_level(o3d.utility.VerbosityLevel.Error)

import laspy
import numpy as np
import os
from tqdm import tqdm

from scipy.spatial import cKDTree
from rasterio.transform import from_origin

from groundPoint_fliter import filter_pointcloud
from interpolator import kriging_interpolation, idw_interpolation, idw_color_interpolation, nearest_color_interpolation
from dem_save import save_geotiff

# 读取点云数据（支持.las, .laz, .ply, .pcd）
def read_pointcloud(file_path):
    print("Reading point cloud...")
    ext = os.path.splitext(file_path)[1].lower()
    with tqdm(total=1, desc="Reading", ncols=80) as pbar:
        if ext in ['.las', '.laz']:
            with laspy.open(file_path) as f:
                pointcloud = f.read()
            xyz = np.vstack((pointcloud.x, pointcloud.y, pointcloud.z)).T
            if hasattr(pointcloud, 'red') and hasattr(pointcloud, 'green') and hasattr(pointcloud, 'blue'):
                rgb = np.vstack((pointcloud.red, pointcloud.green, pointcloud.blue)).T
                rgb = rgb / 65535.0 if rgb.max() > 255 else rgb / 255.0
            else:
                rgb = None
        elif ext in ['.ply', '.pcd']:
            pcd = o3d.io.read_point_cloud(file_path)
            xyz = np.asarray(pcd.points)
            rgb = np.asarray(pcd.colors) if len(pcd.colors) > 0 else None
        else:
            raise ValueError(f"Unsupported file format: {ext}")
        pbar.update(1)
    return xyz, rgb
    
# 可视化点云
def visualize_pointcloud(points, colors=None, title="Point Cloud"):
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(points)
    if colors is not None:
        pcd.colors = o3d.utility.Vector3dVector(colors)
    o3d.visualization.draw_geometries([pcd], window_name=title)

# 主函数
def demGenerate(file_path, ground_fliter=None, colors_data=None, method="idw", grid_size=500):
    # 读取点云数据
    if colors_data is not None:
        points, colors = read_pointcloud(file_path)
        # visualize_pointcloud(points, colors, title="Original Point Cloud")
    else:
        points, _ = read_pointcloud(file_path)
        colors = None
        # visualize_pointcloud(points, title="Original Point Cloud")

    # 地面点提取
    if ground_fliter is None:
        ground_points = points
        ground_colors = colors
    else:
        ground_points, ground_colors = filter_pointcloud(points, colors)
        # visualize_pointcloud(ground_points, ground_colors, title="Filtered Ground Points")

    # 网格大小设置
    min_x, max_x = ground_points[:, 0].min(), ground_points[:, 0].max()
    min_y, max_y = ground_points[:, 1].min(), ground_points[:, 1].max()
    grid_x, grid_y = np.meshgrid(
        np.linspace(min_x, max_x, grid_size),
        np.linspace(min_y, max_y, grid_size)
    )

    if method == "idw":
        dem = idw_interpolation(ground_points, grid_x, grid_y)
        print("DEM generated using IDW.")
    elif method == "kriging":
        dem = kriging_interpolation(ground_points, grid_x, grid_y, k_neighbors=100, n_jobs=8)
        print("DEM generated using Kriging.")
    else:
        raise ValueError("Invalid interpolation method. Choose 'idw' or 'kriging'.")
    
    # 颜色插值
    if ground_colors is not None:
        # color_grid = idw_color_interpolation(ground_points, ground_colors, grid_x, grid_y, n_jobs=8)
        color_grid = nearest_color_interpolation(ground_points, ground_colors, grid_x, grid_y, n_jobs=8)
    else:
        color_grid = None

    return dem, color_grid, grid_x, grid_y
    

if __name__ == "__main__":
    file_path = "../pcd_data/fused2.ply"
    ground_fliter = None  # 是否进行地面点提取
    color_data = True  # 是否保留颜色信息
    method = "idw"  # "idw" or "kriging"
    grid_size = 100  # 网格大小
    dem, color_grid, grid_x, grid_y = demGenerate(file_path, ground_fliter, color_data, method, grid_size)

    # 可视化DEM
    dem_points = np.column_stack((grid_x.ravel(), grid_y.ravel(), dem.ravel()))
    dem_points = dem_points[~np.isnan(dem_points[:, 2])]
    flat_colors = color_grid.reshape(-1, 3).astype(np.float32) / 255.0
    visualize_pointcloud(dem_points, flat_colors, title="DEM Surface")
    
    save_geotiff(dem, color_grid, grid_x, grid_y, out_path="..\output_dem.tif")