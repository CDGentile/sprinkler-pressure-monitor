"""Tests for SEM-meter consumer scaling and line protocol generation."""

import json
import pytest
from unittest.mock import MagicMock, patch

from circuit_config import CIRCUITS, MAIN_LEGS
from sem_consumer import scale_circuit, on_message


# Real message captured from broker
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


class TestScaling:
    def test_120v_circuit_voltage(self):
        result = scale_circuit(0, [1208, 0, 0, 0, 0])
        assert result["voltage"] == 120.8

    def test_240v_circuit_voltage(self):
        result = scale_circuit(9, [1208, 47, 184, 11905, 0])
        assert result["voltage"] == 241.6  # 1208 * 0.2

    def test_240v_circuit_current(self):
        result = scale_circuit(9, [1208, 47, 184, 11905, 0])
        assert result["current"] == 0.47

    def test_240v_circuit_power(self):
        result = scale_circuit(9, [1208, 47, 184, 11905, 0])
        assert result["power_w"] == 3.68  # 184 * 0.02

    def test_240v_circuit_energy(self):
        result = scale_circuit(9, [1208, 47, 184, 11905, 0])
        assert result["energy_in_kwh"] == 23.81  # 11905 * 0.002

    def test_120v_circuit_power(self):
        result = scale_circuit(4, [1208, 0, 790, 4191, 0])
        assert result["power_w"] == 7.9  # 790 * 0.01

    def test_120v_circuit_energy(self):
        result = scale_circuit(4, [1208, 0, 790, 4191, 0])
        assert result["energy_in_kwh"] == 4.191  # 4191 * 0.001

    def test_main_leg_scaling(self):
        result = scale_circuit(16, [1208, 44, 650, 24626, 0])
        assert result["voltage"] == 120.8
        assert result["current"] == 0.44
        assert result["power_w"] == 6.5
        assert result["energy_in_kwh"] == 24.626

    def test_zero_values(self):
        result = scale_circuit(0, [1208, 0, 0, 0, 0])
        assert result["current"] == 0.0
        assert result["power_w"] == 0.0
        assert result["energy_in_kwh"] == 0.0
        assert result["energy_out_kwh"] == 0.0


class TestCircuitConfig:
    def test_all_19_circuits_defined(self):
        assert len(CIRCUITS) == 19

    def test_indices_0_through_18(self):
        for i in range(19):
            assert i in CIRCUITS

    def test_main_legs_are_16_17_18(self):
        assert MAIN_LEGS == [16, 17, 18]

    def test_240v_circuits(self):
        for idx in [2, 8, 9]:
            assert CIRCUITS[idx]["type"] == "240v"
            assert CIRCUITS[idx]["voltage_scale"] == 0.2
            assert CIRCUITS[idx]["power_scale"] == 0.02
            assert CIRCUITS[idx]["energy_scale"] == 0.002


class TestOnMessage:
    @patch("sem_consumer.session")
    def test_writes_20_points(self, mock_session):
        """19 circuits + 1 main_total = 20 points."""
        mock_resp = MagicMock()
        mock_resp.status_code = 204
        mock_session.post.return_value = mock_resp

        msg = MagicMock()
        msg.topic = "SEMMETER/A085E3FD6EA6/HA"
        msg.payload = json.dumps(SAMPLE_MESSAGE)

        on_message(None, None, msg)

        mock_session.post.assert_called_once()
        body = mock_session.post.call_args[1].get("data") or mock_session.post.call_args[0][1]
        # If passed as kwarg 'data'
        if isinstance(body, str):
            lines = body.strip().split("\n")
        else:
            lines = mock_session.post.call_args[1]["data"].strip().split("\n")
        assert len(lines) == 20

    @patch("sem_consumer.session")
    def test_main_total_computed(self, mock_session):
        mock_resp = MagicMock()
        mock_resp.status_code = 204
        mock_session.post.return_value = mock_resp

        msg = MagicMock()
        msg.topic = "SEMMETER/A085E3FD6EA6/HA"
        msg.payload = json.dumps(SAMPLE_MESSAGE)

        on_message(None, None, msg)

        body = mock_session.post.call_args[1].get("data") or mock_session.post.call_args[0][1]
        lines = body.strip().split("\n")
        main_total_line = [l for l in lines if "circuit=main_total" in l]
        assert len(main_total_line) == 1
        # Main total power = leg1(6.5) + leg2(16.82) + leg3(0) = 23.32
        assert "power_w=23.32" in main_total_line[0]

    @patch("sem_consumer.session")
    def test_device_id_from_topic(self, mock_session):
        mock_resp = MagicMock()
        mock_resp.status_code = 204
        mock_session.post.return_value = mock_resp

        msg = MagicMock()
        msg.topic = "SEMMETER/TESTDEVICE123/HA"
        msg.payload = json.dumps(SAMPLE_MESSAGE)

        on_message(None, None, msg)

        body = mock_session.post.call_args[1].get("data") or mock_session.post.call_args[0][1]
        assert "device=TESTDEVICE123" in body

    @patch("sem_consumer.session")
    def test_bad_json_skipped(self, mock_session):
        msg = MagicMock()
        msg.topic = "SEMMETER/A085E3FD6EA6/HA"
        msg.payload = b"not json"

        on_message(None, None, msg)
        mock_session.post.assert_not_called()
