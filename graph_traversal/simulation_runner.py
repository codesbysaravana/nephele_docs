"""Simulation and validation runner for the Graph Traversal Engine."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from knowledge_graph.graph_loader import load_graph_document
from .graph_navigator import GraphNavigator
from .models import TraversalDecision, TraversalState
from .traversal_engine import GraphTraversalEngine, get_next_concept, find_graph_path


class MockCursor:
    """Mock database cursor to record executed queries and parameters."""

    def __init__(self) -> None:
        self.queries: List[tuple[str, tuple[Any, ...]]] = []

    def execute(self, query: str, params: tuple[Any, ...] = ()) -> None:
        self.queries.append((query, params))

    def fetchone(self) -> Optional[tuple[Any, ...]]:
        # For mock updates/inserts we don't fetch rows, but for load we return mock data if needed
        return None

    def fetchall(self) -> List[tuple[Any, ...]]:
        return []

    def __enter__(self) -> MockCursor:
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        pass


class MockConnection:
    """Mock database connection returning a MockCursor."""

    def __init__(self) -> None:
        self.cursor_obj = MockCursor()

    def cursor(self) -> MockCursor:
        return self.cursor_obj


class GraphTraversalSimulator:
    """Simulates and validates Graph Traversal Engine navigation and state."""

    def __init__(self, domain: str = "machine_learning") -> None:
        self.domain = domain
        self.graph_path = find_graph_path(domain)
        self.graph = load_graph_document(self.graph_path)
        self.navigator = GraphNavigator(self.graph)
        self.engine = GraphTraversalEngine(self.graph_path)

    def run_validation_suite(self) -> Dict[str, Any]:
        """Run all simulations, tests, validations, and persistence checks."""
        print("==================================================")
        print("   NEPHELE GRAPH TRAVERSAL VALIDATION RUNNER      ")
        print("==================================================\n")

        # 1. Run Simulated Interview Scenario
        interview_logs, interview_valid = self.run_simulated_interview()

        # 2. Run Branch Termination Test
        termination_valid = self.run_branch_termination_test()

        # 3. Run Acceleration Test
        acceleration_valid = self.run_acceleration_test()

        # 4. Perform Graph Validations
        loops_found, loop_details = self.check_loops(interview_logs)
        dead_ends_found, dead_ends = self.check_dead_ends()
        invalid_jumps_found, jump_details = self.check_invalid_jumps(interview_logs)

        # 5. Validate State Persistence
        state_persistence_valid = self.validate_state_persistence(interview_logs)

        # 6. Database Reconstruction Validation
        db_reconstruction_valid = self.validate_db_reconstruction(interview_logs)

        # 7. Print Coverage Report
        coverage_report = self.generate_coverage_report(interview_logs)
        print("\nGRAPH COVERAGE REPORT:")
        print(json.dumps(coverage_report, indent=2))

        # 8. Print Validation Details if issues found
        if loops_found:
            print(f"\nWARNING: Loops detected! Details: {loop_details}")
        if dead_ends_found:
            print(f"\nWARNING: Dead ends detected! Details: {dead_ends}")
        if invalid_jumps_found:
            print(f"\nWARNING: Invalid jumps detected! Details: {jump_details}")

        # 9. Final Validation Report
        final_report = {
            "loops_found": loops_found,
            "dead_ends_found": dead_ends_found,
            "invalid_jumps_found": invalid_jumps_found,
            "state_persistence_valid": state_persistence_valid,
            "branch_termination_valid": termination_valid,
            "acceleration_valid": acceleration_valid and db_reconstruction_valid
        }
        
        print("\nFINAL VALIDATION REPORT:")
        print(json.dumps(final_report, indent=2))
        print("==================================================")

        return final_report

    def run_simulated_interview(self) -> tuple[List[Dict[str, Any]], bool]:
        """Execute the step-by-step traversal defined in the scenario."""
        print("--- SIMULATED INTERVIEW RUN ---")
        
        scenario_steps = [
            {"concept": "Supervised Learning", "mastery": 0.90},
            {"concept": "Train-Test Split", "mastery": 0.80},
            {"concept": "Overfitting", "mastery": 0.20},
            {"concept": "Train-Test Split", "mastery": 0.70},
            {"concept": "Overfitting", "mastery": 0.40},
            {"concept": "Overfitting", "mastery": 0.85},
            {"concept": "Regularization", "mastery": 0.90},
        ]

        state = {
            "visited_concepts": [],
            "mastery_history": [],
            "success_streak": 0,
            "failure_streak": 0
        }
        
        logs = []
        
        for i, step in enumerate(scenario_steps):
            current_concept = step["concept"]
            mastery = step["mastery"]
            
            # Run get_next_concept API
            result = get_next_concept(
                domain=self.domain,
                current_concept=current_concept,
                mastery=mastery,
                confidence=0.90,
                state=state,
                candidate_id="sim_candidate"
            )
            
            step_log = {
                "current_concept": current_concept,
                "mastery": mastery,
                "decision": result["decision"],
                "next_concept": result.get("next_concept"),
                "state": {
                    "visited_concepts": list(state["visited_concepts"]),
                    "mastery_history": list(state["mastery_history"]),
                    "success_streak": state["success_streak"],
                    "failure_streak": state["failure_streak"]
                }
            }
            
            logs.append(step_log)
            
            # Print exact requested log format
            print(json.dumps({
                "current_concept": current_concept,
                "mastery": mastery,
                "decision": result["decision"],
                "next_concept": result.get("next_concept"),
                "state": {
                    "success_streak": state["success_streak"],
                    "failure_streak": state["failure_streak"]
                }
            }, indent=2))
            print()

        return logs, True

    def run_branch_termination_test(self) -> bool:
        """Simulate three consecutive failures and verify terminate_branch."""
        print("--- RUNNING BRANCH TERMINATION TEST ---")
        state = {
            "visited_concepts": ["Overfitting"],
            "mastery_history": [],
            "success_streak": 0,
            "failure_streak": 0
        }
        
        concepts = ["Overfitting", "Train-Test Split", "Supervised Learning"]
        
        res1 = get_next_concept(self.domain, concepts[0], 0.20, 0.90, state, "terminate_student")
        res2 = get_next_concept(self.domain, concepts[1], 0.20, 0.90, state, "terminate_student")
        res3 = get_next_concept(self.domain, concepts[2], 0.20, 0.90, state, "terminate_student")
        
        print(f"1st failure decision: {res1['decision']}")
        print(f"2nd failure decision: {res2['decision']}")
        print(f"3rd failure decision: {res3['decision']}")
        print(f"Final State: {json.dumps(state)}\n")
        
        return res3["decision"] == "terminate_branch" and state.get("terminated") is True

    def run_acceleration_test(self) -> bool:
        """Simulate three consecutive successes and verify accelerate."""
        print("--- RUNNING ACCELERATION TEST ---")
        state = {
            "visited_concepts": ["Overfitting"],
            "mastery_history": [],
            "success_streak": 0,
            "failure_streak": 0
        }
        
        concepts = ["Overfitting", "Regularization", "L1 Regularization"]
        
        res1 = get_next_concept(self.domain, concepts[0], 0.95, 0.90, state, "accelerate_student")
        res2 = get_next_concept(self.domain, concepts[1], 0.95, 0.90, state, "accelerate_student")
        res3 = get_next_concept(self.domain, concepts[2], 0.95, 0.90, state, "accelerate_student")
        
        print(f"1st success decision: {res1['decision']}")
        print(f"2nd success decision: {res2['decision']}")
        print(f"3rd success decision: {res3['decision']}")
        print(f"Final State: {json.dumps(state)}\n")
        
        return res3["decision"] == "accelerate" and state.get("accelerated") is True

    def check_loops(self, logs: List[Dict[str, Any]]) -> tuple[bool, List[str]]:
        """Detect if an infinite loop (e.g. A -> B -> A -> B -> A -> B) occurs."""
        path = [log["current_concept"] for log in logs]
        if logs and logs[-1].get("next_concept"):
            path.append(logs[-1]["next_concept"])
            
        n = len(path)
        # Check for any pattern of length L repeating consecutively K >= 3 times
        for pattern_len in range(1, 4):
            for i in range(n - 3 * pattern_len + 1):
                p1 = path[i : i + pattern_len]
                p2 = path[i + pattern_len : i + 2 * pattern_len]
                p3 = path[i + 2 * pattern_len : i + 3 * pattern_len]
                if p1 == p2 == p3:
                    return True, [f"Sequence repeating 3+ times: {p1}"]
        return False, []

    def check_dead_ends(self) -> tuple[bool, List[str]]:
        """Verify that every concept has at least one valid progression path."""
        dead_ends = []
        for concept in self.graph.concepts:
            cid = concept.concept_id
            successors = self.navigator.get_successors(cid)
            prerequisites = self.navigator.get_prerequisites(cid)
            # A dead end is a concept with no successors and no prerequisites
            if not successors and not prerequisites:
                dead_ends.append(concept.concept_name)
        return len(dead_ends) > 0, dead_ends

    def check_invalid_jumps(self, logs: List[Dict[str, Any]]) -> tuple[bool, List[str]]:
        """Verify that transitions only follow successors, prerequisites, stays, or acceleration rules."""
        violations = []
        for log in logs:
            curr = log["current_concept"]
            nxt = log["next_concept"]
            decision = log["decision"]
            
            if not nxt:
                continue
                
            curr_node = self.navigator.lookup_concept(curr)
            nxt_node = self.navigator.lookup_concept(nxt)
            
            if not curr_node or not nxt_node:
                violations.append(f"Could not resolve concept nodes: {curr} -> {nxt}")
                continue
                
            curr_id = curr_node.concept_id
            nxt_id = nxt_node.concept_id
            
            if decision == "stay":
                if curr_id != nxt_id:
                    violations.append(f"Stay decision but transitioned: {curr} -> {nxt}")
            elif decision == "advance":
                successors = self.navigator.get_successors(curr_id)
                # Successor, or cycle protection jump
                if nxt_id not in successors:
                    # Verify if it was cycle protection: all successors must be visited
                    visited_names = set(log["state"]["visited_concepts"])
                    all_successors_visited = all(
                        self.navigator.get_concept_name(s) in visited_names or s in visited_names 
                        for s in successors
                    )
                    if not all_successors_visited:
                        violations.append(f"Invalid advance transition: {curr} -> {nxt}")
            elif decision == "backtrack":
                prerequisites = self.navigator.get_prerequisites(curr_id)
                if nxt_id not in prerequisites:
                    visited_names = set(log["state"]["visited_concepts"])
                    all_prereqs_visited = all(
                        self.navigator.get_concept_name(p) in visited_names or p in visited_names 
                        for p in prerequisites
                    )
                    if not all_prereqs_visited:
                        violations.append(f"Invalid backtrack transition: {curr} -> {nxt}")
            elif decision == "accelerate":
                # Grand successor, successor, or unvisited higher difficulty
                successors = self.navigator.get_successors(curr_id)
                grand_successors = []
                for s in successors:
                    grand_successors.extend(self.navigator.get_successors(s))
                    
                valid_ids = set(successors).union(grand_successors)
                if nxt_id not in valid_ids:
                    # Verify if it fell back to higher difficulty unvisited
                    if nxt_node.difficulty <= curr_node.difficulty:
                        violations.append(f"Invalid acceleration jump: {curr} -> {nxt}")
                        
        return len(violations) > 0, violations

    def validate_state_persistence(self, logs: List[Dict[str, Any]]) -> bool:
        """Verify that state attributes are properly updated and accumulated at each step."""
        for i, log in enumerate(logs):
            state = log["state"]
            # length of mastery_history should match the step number (i + 1)
            if len(state["mastery_history"]) != i + 1:
                return False
            # current mastery score must be appended last
            if state["mastery_history"][-1] != log["mastery"]:
                return False
            # visited concepts list should contain the current concept
            if log["current_concept"] not in state["visited_concepts"]:
                return False
        return True

    def validate_db_reconstruction(self, logs: List[Dict[str, Any]]) -> bool:
        """Simulate writing to database tables and verify reconstruction of the interview."""
        print("--- RUNNING DATABASE PERSISTENCE & RECONSTRUCTION VALIDATION ---")
        mock_conn = MockConnection()
        
        # 1. Simulate the steps writing to the DB
        state = {
            "visited_concepts": [],
            "mastery_history": [],
            "success_streak": 0,
            "failure_streak": 0
        }
        
        for log in logs:
            get_next_concept(
                domain=self.domain,
                current_concept=log["current_concept"],
                mastery=log["mastery"],
                confidence=0.90,
                state=state,
                candidate_id="reconstruct_student",
                conn=mock_conn
            )
            
        # 2. Extract executed queries from cursor
        queries = mock_conn.cursor_obj.queries
        
        # Filter for concept_progress insert queries
        progress_inserts = [
            q for q in queries if "INSERT INTO concept_progress" in q[0]
        ]
        
        # Filter for interview_sessions upsert queries
        session_upserts = [
            q for q in queries if "INSERT INTO interview_sessions" in q[0]
        ]
        
        print(f"Logged {len(progress_inserts)} concept_progress inserts.")
        print(f"Logged {len(session_upserts)} interview_sessions upserts.")
        
        # 3. Reconstruct the interview path from concept_progress records
        reconstructed_steps = []
        for query, params in progress_inserts:
            # params = (candidate_id, concept_id, mastery, decision)
            reconstructed_steps.append({
                "concept": params[1],
                "mastery": float(params[2]),
                "decision": params[3]
            })
            
        print("\nReconstructed Interview History:")
        for idx, step in enumerate(reconstructed_steps):
            print(f"  Step {idx+1}: Concept='{step['concept']}', Mastery={step['mastery']:.2f}, Decision='{step['decision']}'")
            
        # 4. Verify match with original simulation log
        if len(reconstructed_steps) != len(logs):
            print("FAILED: Log length mismatch!")
            return False
            
        for orig, recon in zip(logs, reconstructed_steps):
            orig_name = self.navigator.get_concept_name(orig["current_concept"]) or orig["current_concept"]
            recon_name = self.navigator.get_concept_name(recon["concept"]) or recon["concept"]
            if orig_name.lower() != recon_name.lower():
                print(f"FAILED: Concept mismatch: original='{orig_name}', reconstructed='{recon_name}'")
                return False
            if abs(orig["mastery"] - recon["mastery"]) > 1e-4:
                print(f"FAILED: Mastery mismatch: original={orig['mastery']}, reconstructed={recon['mastery']}")
                return False
            if orig["decision"] != recon["decision"]:
                print(f"FAILED: Decision mismatch: original='{orig['decision']}', reconstructed='{recon['decision']}'")
                return False
                
        print("SUCCESS: Database records successfully reconstructed 100% of the interview history.\n")
        return True

    def generate_coverage_report(self, logs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Compute coverage of the concepts visited during simulation."""
        total_concepts = len(self.graph.concepts)
        visited_concepts = set()
        for log in logs:
            visited_concepts.add(log["current_concept"])
            if log.get("next_concept"):
                visited_concepts.add(log["next_concept"])
                
        visited_count = len(visited_concepts)
        coverage_percent = (visited_count / total_concepts) * 100 if total_concepts else 0.0
        
        return {
            "visited_count": visited_count,
            "total_concepts": total_concepts,
            "coverage_percent": round(coverage_percent, 2)
        }


if __name__ == "__main__":
    simulator = GraphTraversalSimulator()
    simulator.run_validation_suite()
