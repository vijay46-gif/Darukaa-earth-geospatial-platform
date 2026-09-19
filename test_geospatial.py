import pytest

from app.services.geospatial import GeospatialService


def test_valid_polygon_parsing_and_area():
    # ~1 degree x 1 degree polygon near equator
    polygon_geojson = {
        "type": "Polygon",
        "coordinates": [
            [[-60.0, -3.0], [-59.9, -3.0], [-59.9, -3.1], [-60.0, -3.1], [-60.0, -3.0]]
        ],
    }

    poly, area_ha, lat, lng = GeospatialService.validate_and_parse_geojson(polygon_geojson)
    assert poly.is_valid
    assert area_ha > 10000.0  # Approx ~12,000 hectares
    assert -3.1 <= lat <= -3.0
    assert -60.0 <= lng <= -59.9


def test_ring_unclosed_auto_closure():
    # Coordinates without duplicate last point
    unclosed = {
        "type": "Polygon",
        "coordinates": [[[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0]]],
    }
    poly, area_ha, lat, lng = GeospatialService.validate_and_parse_geojson(unclosed)
    assert poly.is_valid
    assert area_ha > 0.0


def test_out_of_bounds_coordinates_raise_error():
    out_of_bounds = {
        "type": "Polygon",
        "coordinates": [[[200.0, 0.0], [201.0, 0.0], [201.0, 1.0], [200.0, 1.0], [200.0, 0.0]]],
    }
    with pytest.raises(ValueError, match="Longitude 200.0 out of range"):
        GeospatialService.validate_and_parse_geojson(out_of_bounds)
