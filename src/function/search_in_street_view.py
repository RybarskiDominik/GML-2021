import webbrowser
from PySide6.QtCore import QPointF
from pyproj import Transformer


def open_parcel_in_street_view(xy: QPointF, heading: float=0, EPSG="EPSG:2177"):
    x = xy.x()
    y = abs(xy.y())

    transformer = Transformer.from_crs(EPSG, "EPSG:4326", always_xy=True)

    lon, lat = transformer.transform(x, y)

    google_maps_url = (
        f"https://maps.google.com/maps?q=&layer=c&cbll={lat},{lon}"
        f"&cbp=12,{heading},0,0,0&z=18"
    )

    webbrowser.open(google_maps_url, new=0, autoraise=True)


if __name__ == '__main__':
    pass
