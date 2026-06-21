"""Tests for Graph Traversal simulation and validation runner."""

from __future__ import annotations

import unittest
from graph_traversal.simulation_runner import GraphTraversalSimulator


class TestGraphTraversalSimulation(unittest.TestCase):
    def setUp(self) -> None:
        self.simulator = GraphTraversalSimulator(domain="machine_learning")

    def test_run_validation_suite(self) -> None:
        """Execute the validation suite and assert all safety and progression properties are valid."""
        report = self.simulator.run_validation_suite()

        self.assertFalse(report["loops_found"], "Infinite loops were found in graph traversal!")
        self.assertFalse(report["dead_ends_found"], "Dead-end concepts were found in the graph!")
        self.assertFalse(report["invalid_jumps_found"], "Invalid transitions/jumps were found!")
        self.assertTrue(report["state_persistence_valid"], "State persistence validation failed!")
        self.assertTrue(report["branch_termination_valid"], "Branch termination validation failed!")
        self.assertTrue(report["acceleration_valid"], "Acceleration validation failed!")


if __name__ == "__main__":
    unittest.main()
