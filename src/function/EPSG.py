import geopandas as gpd


def read_EPSG(path):
    gdf = gpd.read_file(path)
    if not gdf.crs:
        gdf.crs = "EPSG:2177"
    return gdf.crs


if __name__ == '__main__':
    pass