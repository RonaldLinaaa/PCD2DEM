import os
import numpy as np

from dem_evaluator import load_and_align_dem, compute_rmse

if __name__ == "__main__":
    my_dem_path = "my_dem.tif"   # 替换为你生成的 DEM 文件路径
    gt_dem_path = "gt_dem.tif"   # 替换为真值 DEM 文件路径

    aligned_pred, aligned_gt = load_and_align_dem(my_dem_path, gt_dem_path)
    rmse = compute_rmse(aligned_pred, aligned_gt)
    print(f"RMSE between generated DEM and ground truth DEM: {rmse:.4f}")