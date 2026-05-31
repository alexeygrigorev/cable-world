import pyproj
from shapely import ops
from shapely.geometry import Point, Polygon, MultiPolygon


class MapProjection:
    def __init__(self, bounds, image_size):
        self.min_lon, self.min_lat, self.max_lon, self.max_lat = bounds
        self.width, self.height = image_size

        self._merc = pyproj.Transformer.from_crs(
            "EPSG:4326", "EPSG:3857", always_xy=True
        )
        self._inv_merc = pyproj.Transformer.from_crs(
            "EPSG:3857", "EPSG:4326", always_xy=True
        )

        xm_min, ym_max = self._merc.transform(self.min_lon, self.max_lat)
        xm_max, ym_min = self._merc.transform(self.max_lon, self.min_lat)

        self._xm_min = xm_min
        self._xm_max = xm_max
        self._ym_min = ym_min
        self._ym_max = ym_max
        self._xm_range = xm_max - xm_min
        self._ym_range = ym_max - ym_min

    def project(self, lon, lat):
        xm, ym = self._merc.transform(lon, lat)
        x = (xm - self._xm_min) / self._xm_range * self.width
        y = (self._ym_max - ym) / self._ym_range * self.height
        return (x, y)

    def inverse(self, x, y):
        xm = self._xm_min + x / self.width * self._xm_range
        ym = self._ym_max - y / self.height * self._ym_range
        lon, lat = self._inv_merc.transform(xm, ym)
        return (lon, lat)

    def project_geometry(self, geom):
        if geom.is_empty:
            return geom

        def _transform_point(x, y, z=None):
            return self.project(x, y)

        return ops.transform(_transform_point, geom)
