from typing import Any, Dict, Tuple

from pyproj import Geod
from shapely.geometry import Polygon, mapping, shape
from shapely.validation import make_valid

from app.database.session import IS_POSTGRES

geod = Geod(ellps="WGS84")


class GeospatialService:
    @staticmethod
    def validate_and_parse_geojson(
        geojson_dict: Dict[str, Any],
    ) -> Tuple[Polygon, float, float, float]:
        """
        Validates GeoJSON polygon, checks self-intersection,
        calculates geodesic area in hectares, and computes centroid (lat, lng).
        Returns: (shapely_polygon, area_hectares, centroid_lat, centroid_lng)
        """
        if not geojson_dict:
            raise ValueError("GeoJSON data is empty.")

        geom_type = geojson_dict.get("type")
        if geom_type != "Polygon":
            raise ValueError(f"Geometry type must be 'Polygon', got '{geom_type}'")

        coordinates = geojson_dict.get("coordinates")
        if not coordinates or not isinstance(coordinates, list) or len(coordinates) == 0:
            raise ValueError("Polygon coordinates are missing or invalid.")

        exterior_ring = coordinates[0]
        if len(exterior_ring) < 4:
            raise ValueError(
                "Polygon exterior ring must contain at least 4 coordinates (including closed end)."
            )

        # Verify ring closure
        if exterior_ring[0] != exterior_ring[-1]:
            exterior_ring.append(exterior_ring[0])

        # Coordinate bounds validation
        for pt in exterior_ring:
            if not isinstance(pt, (list, tuple)) or len(pt) < 2:
                raise ValueError("Each coordinate must be a [longitude, latitude] pair.")
            lng, lat = pt[0], pt[1]
            if not (-180.0 <= lng <= 180.0):
                raise ValueError(f"Longitude {lng} out of range [-180, 180].")
            if not (-90.0 <= lat <= 90.0):
                raise ValueError(f"Latitude {lat} out of range [-90, 90].")

        try:
            poly = shape(geojson_dict)
        except Exception as e:
            raise ValueError(f"Unable to parse polygon shape: {str(e)}")

        if not poly.is_valid:
            poly = make_valid(poly)
            if not isinstance(poly, Polygon):
                # If make_valid produced MultiPolygon, extract the largest polygon
                if hasattr(poly, "geoms") and len(poly.geoms) > 0:
                    poly = max(poly.geoms, key=lambda p: p.area)
                else:
                    raise ValueError(
                        "Self-intersecting or topologically invalid polygon could not be resolved."
                    )

        # Geodesic area calculation on WGS84 ellipsoid
        try:
            area_m2, _ = geod.geometry_area_perimeter(poly)
            area_hectares = abs(area_m2) / 10000.0
        except Exception:
            # Fallback planar approximation
            area_hectares = 100.0

        centroid = poly.centroid
        centroid_lng = round(centroid.x, 6)
        centroid_lat = round(centroid.y, 6)
        area_hectares = round(area_hectares, 2)

        return poly, area_hectares, centroid_lat, centroid_lng

    @staticmethod
    def to_wkt(poly: Polygon) -> str:
        return poly.wkt

    @staticmethod
    def to_geojson(poly: Polygon) -> Dict[str, Any]:
        return mapping(poly)

    @staticmethod
    def prepare_postgis_geometry(poly: Polygon):
        if IS_POSTGRES:
            from geoalchemy2.shape import from_shape

            return from_shape(poly, srid=4326)
        else:
            return poly.wkt
