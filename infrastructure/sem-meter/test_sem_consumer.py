"""Tests for SEM-meter consumer scaling and line protocol generation."""

import json
import pytest
from unittest.mock import MagicMock, patch

from circuit_config import DEVICE_CIRCUITS, DEVICE_MAIN_LEGS
from sem_consumer import scale_circuit, on_message

SHOP = "A085E3FD6EA6"
HOBBIT = "1CDBD4423A6E"

SHOP_CIRCUITS = DEVICE_CIRCUITS[SHOP]
HOBBIT_CIRCUITS = DEVICE_CIRCUITS[HOBBIT]


# Real message captured from the Shop broker
SAMPLE_MESSAGE = {"sense": [
    [1208, 0, 0, 0, 0],        # 0: old_outlet
    [1208, 0, 0, 10949, 0],    # 1: heater
    [1208, 0, 0, 0, 0],        # 2: old_pump
    [1208, 0, 0, 0, 0],        # 3: timer_outlet
    [1208, 0, 790, 4191, 0],   # 4: gfci_network
    [1208, 0, 0, 0, 0],        # 5: indicator_light
    [1208, 0, 0, 0, 0],        # 6: 20a_outlet
    [1208, 0, 0, 0, 0],        # 7: lights
    [1208, 0, 0, 0, 0],        # 8: pond_pump
    [1208, 47, 184, 11905, 0], # 9: new_pump (240V)
    [1208, 0, 0, 0, 0],        # 10-15: unnamed
    [1208, 0, 0, 0, 0],
    [1208, 0, 0, 0, 0],
    [1208, 0, 0, 0, 0],
    [1208, 0, 0, 0, 0],
    [1208, 0, 0, 0, 0],
    [1208, 44, 650, 24626, 0], # 16: main_leg1
    [1208, 51, 1682, 28356, 0],# 17: main_leg2
    [1208, 0, 0, 0, 0],        # 18: main_leg3
]}

# Hobbit message: 5 connected circuits (0-4), unconnected 5-15, 2 live main legs.
HOBBIT_MESSAGE = {"sense": [
    [600, 32, 640, 5000, 0],   # 0: tank_pump (240V)
    [1208, 0, 0, 0, 0],        # 1: hobbit_outlets
    [1208, 10, 120, 800, 0],   # 2: hangar
    [600, 0, 0, 0, 0],         # 3: dryer (240V)
    [600, 0, 0, 0, 0],         # 4: runway_pump (240V)
    [0, 0, 0, 0, 0],           # 5-15: unconnected
    [0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0],
    [1208, 40, 500, 10000, 0], # 16: main_leg1
    [1208, 30, 400, 8000, 0],  # 17: main_leg2
    [0, 0, 0, 0, 0],           # 18: main_leg3 (unused)
]}


class TestScaling:
    def test_120v_circuit_voltage(self):
        result = scale_circuit(SHOP_CIRCUITS[0], [1208, 0, 0, 0, 0])
        assert result["voltage"] == 120.8

    def test_240v_circuit_voltage(self):
        result = scale_circuit(SHOP_CIRCUITS[9], [1208, 47, 184, 11905, 0])
        assert result["voltage"] == 241.6  # 1208 * 0.2

    def test_240v_circuit_current(self):
        result = scale_circuit(SHOP_CIRCUITS[9], [1208, 47, 184, 11905, 0])
        assert result["current"] == 0.47

    def test_240v_circuit_power(self):
        result = scale_circuit(SHOP_CIRCUITS[9], [1208, 47, 184, 11905, 0])
        assert result["power_w"] == 3.68  # 184 * 0.02

    def test_240v_circuit_energy(self):
        result = scale_circuit(SHOP_CIRCUITS[9], [1208, 47, 184, 11905, 0])
        assert result["energy_in_kwh"] == 23.81  # 11905 * 0.002

    def test_120v_circuit_power(self):
        result = scale_circuit(SHOP_CIRCUITS[4], [1208, 0, 790, 4191, 0])
        assert result["power_w"] == 7.9  # 790 * 0.01

    def test_120v_circuit_energy(self):
        result = scale_circuit(SHOP_CIRCUITS[4], [1208, 0, 790, 4191, 0])
        assert result["energy_in_kwh"] == 4.191  # 4191 * 0.001

    def test_main_leg_scaling(self):
        result = scale_circuit(SHOP_CIRCUITS[16], [1208, 44, 650, 24626, 0])
        assert result["voltage"] == 120.8
        assert result["current"] == 0.44
        assert result["power_w"] == 6.5
        assert result["energy_in_kwh"] == 24.626

    def test_zero_values(self):
        result = scale_circuit(SHOP_CIRCUITS[0], [1208, 0, 0, 0, 0])
        assert result["current"] == 0.0
        assert result["power_w"] == 0.0
        assert result["energy_in_kwh"] == 0.0
        assert result["energy_out_kwh"] == 0.0

    def test_hobbit_240v_tank_pump(self):
        # tank_pump is 240V: voltage 0.2, power 0.02, energy 0.002
        result = scale_circuit(HOBBIT_CIRCUITS[0], [600, 32, 640, 5000, 0])
        assert result["voltage"] == 120.0  # 600 * 0.2
        assert result["current"] == 0.32
        assert result["power_w"] == 12.8   # 640 * 0.02
        assert result["energy_in_kwh"] == 10.0  # 5000 * 0.002

    def test_hobbit_120v_hangar(self):
        result = scale_circuit(HOBBIT_CIRCUITS[2], [1208, 10, 120, 800, 0])
        assert result["voltage"] == 120.8
        assert result["power_w"] == 1.2    # 120 * 0.01
        assert result["energy_in_kwh"] == 0.8


class TestCircuitConfig:
    def test_shop_has_19_circuits(self):
        assert len(SHOP_CIRCUITS) == 19

    def test_shop_indices_0_through_18(self):
        for i in range(19):
            assert i in SHOP_CIRCUITS

    def test_hobbit_has_5_circuits_plus_mains(self):
        # 5 connected circuits (0-4) + 3 main-leg slots
        assert len(HOBBIT_CIRCUITS) == 8
        for i in [0, 1, 2, 3, 4, 16, 17, 18]:
            assert i in HOBBIT_CIRCUITS

    def test_hobbit_skips_unconnected_slots(self):
        for i in range(5, 16):
            assert i not in HOBBIT_CIRCUITS

    def test_hobbit_circuit_names(self):
        assert HOBBIT_CIRCUITS[0]["name"] == "tank_pump"
        assert HOBBIT_CIRCUITS[1]["name"] == "hobbit_outlets"
        assert HOBBIT_CIRCUITS[2]["name"] == "hangar"
        assert HOBBIT_CIRCUITS[3]["name"] == "dryer"
        assert HOBBIT_CIRCUITS[4]["name"] == "runway_pump"

    def test_main_legs_are_16_17_18(self):
        assert DEVICE_MAIN_LEGS[SHOP] == [16, 17, 18]
        assert DEVICE_MAIN_LEGS[HOBBIT] == [16, 17, 18]

    def test_240v_circuits(self):
        for idx in [2, 8, 9]:
            assert SHOP_CIRCUITS[idx]["type"] == "240v"
            assert SHOP_CIRCUITS[idx]["voltage_scale"] == 0.2
            assert SHOP_CIRCUITS[idx]["power_scale"] == 0.02
            assert SHOP_CIRCUITS[idx]["energy_scale"] == 0.002


def _mock_ok_session(mock_session):
    mock_resp = MagicMock()
    mock_resp.status_code = 204
    mock_session.post.return_value = mock_resp


def _written_lines(mock_session):
    body = mock_session.post.call_args[1].get("data") or mock_session.post.call_args[0][1]
    return body.strip().split("\n")


class TestOnMessage:
    @patch("sem_consumer.session")
    def test_writes_20_points(self, mock_session):
        """Shop: 19 circuits + 1 main_total = 20 points."""
        _mock_ok_session(mock_session)

        msg = MagicMock()
        msg.topic = f"SEMMETER/{SHOP}/HA"
        msg.payload = json.dumps(SAMPLE_MESSAGE)

        on_message(None, None, msg)

        mock_session.post.assert_called_once()
        assert len(_written_lines(mock_session)) == 20

    @patch("sem_consumer.session")
    def test_hobbit_writes_9_points(self, mock_session):
        """Hobbit: 5 connected circuits + 3 main legs + 1 main_total = 9 points."""
        _mock_ok_session(mock_session)

        msg = MagicMock()
        msg.topic = f"SEMMETER/{HOBBIT}/HA"
        msg.payload = json.dumps(HOBBIT_MESSAGE)

        on_message(None, None, msg)

        lines = _written_lines(mock_session)
        assert len(lines) == 9
        assert all(f"device={HOBBIT}" in l for l in lines)
        assert any("circuit=tank_pump" in l for l in lines)
        assert any("circuit=main_total" in l for l in lines)
        # Unconnected slots must not be written
        assert not any("circuit=old_outlet" in l for l in lines)

    @patch("sem_consumer.session")
    def test_main_total_computed(self, mock_session):
        _mock_ok_session(mock_session)

        msg = MagicMock()
        msg.topic = f"SEMMETER/{SHOP}/HA"
        msg.payload = json.dumps(SAMPLE_MESSAGE)

        on_message(None, None, msg)

        main_total_line = [l for l in _written_lines(mock_session) if "circuit=main_total" in l]
        assert len(main_total_line) == 1
        # Main total power = leg1(6.5) + leg2(16.82) + leg3(0) = 23.32
        assert "power_w=23.32" in main_total_line[0]

    @patch("sem_consumer.session")
    def test_device_id_from_topic(self, mock_session):
        _mock_ok_session(mock_session)

        msg = MagicMock()
        msg.topic = f"SEMMETER/{HOBBIT}/HA"
        msg.payload = json.dumps(HOBBIT_MESSAGE)

        on_message(None, None, msg)

        body = mock_session.post.call_args[1].get("data") or mock_session.post.call_args[0][1]
        assert f"device={HOBBIT}" in body

    @patch("sem_consumer.session")
    def test_unknown_device_skipped(self, mock_session):
        """A meter with no configured circuit map must not write garbage."""
        msg = MagicMock()
        msg.topic = "SEMMETER/DEADBEEF9999/HA"
        msg.payload = json.dumps(SAMPLE_MESSAGE)

        on_message(None, None, msg)
        mock_session.post.assert_not_called()

    @patch("sem_consumer.session")
    def test_bad_json_skipped(self, mock_session):
        msg = MagicMock()
        msg.topic = f"SEMMETER/{SHOP}/HA"
        msg.payload = b"not json"

        on_message(None, None, msg)
        mock_session.post.assert_not_called()
