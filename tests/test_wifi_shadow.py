"""Tests for the Wi-Fi/BLE shadow sensing layer."""

import math
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from wifi_shadow import (
    RfAccessPoint, BleBeacon, WifiShadowSensor, WifiShadowState,
    free_space_path_loss_db, body_shadow_db, wall_attenuation_db,
    is_detectable, wavelength_m, spatial_resolution_m,
    wifi_shadow_advisory,
)


def test_free_space_path_loss_formula():
    # 30 m at 5.5 GHz should be ~76.8 dB
    loss = free_space_path_loss_db(30.0, 5.5)
    assert abs(loss - 76.8) < 0.5, f"FSPL got {loss:.1f}, expected ~76.8"


def test_body_shadow_scales_with_tissue():
    thin = body_shadow_db(tissue_m=0.1)
    thick = body_shadow_db(tissue_m=0.3)
    assert thick > thin
    assert abs(thin - 3.0) < 0.1
    assert abs(thick - 9.0) < 0.1


def test_wall_attenuation():
    assert wall_attenuation_db('drywall', 2) == 10.0
    assert wall_attenuation_db('concrete', 1) == 15.0


def test_detectable_within_regulatory_power():
    # 30 m, 5.5 GHz, 2 drywall walls, 20 cm body: should be detectable
    assert is_detectable(30.0, 5.5, walls=2, tissue_m=0.2) is True


def test_not_detectable_through_heavy_concrete():
    # 30 m, 5.5 GHz, 3 concrete walls, 20 cm body: not detectable
    assert is_detectable(30.0, 5.5, walls=3, wall_type='concrete', tissue_m=0.2) is False


def test_wavelength_and_resolution():
    wl = wavelength_m(5.5)
    assert abs(wl - 0.0545) < 0.001
    res = spatial_resolution_m(5.5)
    assert abs(res - 0.0273) < 0.001


def test_sensor_detects_shadow_from_rssi_deficit():
    sensor = WifiShadowSensor(min_shadow_db=4.0, min_confidence=0.5)
    # Build AP history: stable baseline around -60, then a 8 dB drop
    ap = RfAccessPoint(ssid='TestNet', bssid='aa:bb:cc:dd:ee:ff', frequency_ghz=5.5,
                       tx_power_dbm=20.0, last_rssi_dbm=-60.0, distance_m=25.0)
    for _ in range(5):
        sensor.update_access_points([ap])
    ap.last_rssi_dbm = -68.0  # 8 dB deficit
    sensor.update_access_points([ap])
    state = sensor.detect(timestamp_ms=12345)
    assert len(state.detections) >= 1
    d = state.detections[0]
    assert d.confidence >= 0.5
    assert d.source == 'wifi'
    assert d.estimated_size_m == 0.5


def test_sensor_ignores_small_deficit():
    sensor = WifiShadowSensor(min_shadow_db=4.0)
    ap = RfAccessPoint(ssid='TestNet', bssid='aa:bb:cc:dd:ee:ff', frequency_ghz=5.5,
                       tx_power_dbm=20.0, last_rssi_dbm=-60.0, distance_m=25.0)
    for _ in range(5):
        sensor.update_access_points([ap])
    ap.last_rssi_dbm = -62.0  # only 2 dB deficit
    sensor.update_access_points([ap])
    state = sensor.detect()
    assert len(state.detections) == 0


def test_ble_beacon_shadow_detection():
    sensor = WifiShadowSensor(min_shadow_db=4.0, min_confidence=0.5)
    b = BleBeacon(name='Watch', mac='11:22:33:44:55:66', rssi_dbm=-70.0, distance_m=15.0)
    for _ in range(5):
        sensor.update_beacons([b])
    b.rssi_dbm = -78.0
    sensor.update_beacons([b])
    state = sensor.detect(timestamp_ms=999)
    assert len(state.detections) >= 1
    assert state.detections[0].source == 'ble'


def test_advisory_fires_on_high_shadow_density():
    state = WifiShadowState(shadow_density=0.4, detections=[object()])
    adv = wifi_shadow_advisory(state)
    assert adv is not None
    assert 'shadow density' in adv.lower()


def test_advisory_none_on_clean_field():
    state = WifiShadowState(shadow_density=0.0, detections=[])
    assert wifi_shadow_advisory(state) is None


def test_mean_rssi_computed():
    sensor = WifiShadowSensor()
    ap = RfAccessPoint(ssid='A', bssid='aa:bb', frequency_ghz=5.5, tx_power_dbm=20.0,
                       last_rssi_dbm=-55.0, distance_m=20.0)
    sensor.update_access_points([ap])
    state = sensor.detect()
    assert state.mean_rssi_dbm == -55.0
    assert state.ap_count == 1


if __name__ == '__main__':
    tests = [v for k, v in globals().items() if k.startswith('test_')]
    passed = 0
    for t in tests:
        try:
            t()
            passed += 1
            print(f'PASS {t.__name__}')
        except Exception as e:
            print(f'FAIL {t.__name__}: {e}')
    print(f'{passed}/{len(tests)} passed')
    sys.exit(0 if passed == len(tests) else 1)
