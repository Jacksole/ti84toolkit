import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.validation import ValidationError
from modules import logic


class TestEvaluateGate:
    @pytest.mark.parametrize(
        "gate,inputs,expected",
        [
            ("AND", [True, True], True),
            ("AND", [True, False], False),
            ("OR", [False, False], False),
            ("OR", [False, True], True),
            ("NOT", [True], False),
            ("NOT", [False], True),
            ("XOR", [True, False], True),
            ("XOR", [True, True], False),
            ("NAND", [True, True], False),
            ("NAND", [True, False], True),
            ("NOR", [False, False], True),
            ("NOR", [True, False], False),
            ("XNOR", [True, True], True),
            ("XNOR", [True, False], False),
        ],
    )
    def test_two_input_truth_values(self, gate, inputs, expected):
        assert logic.evaluate_gate(gate, inputs) is expected

    def test_and_or_xor_scale_to_n_inputs(self):
        assert logic.evaluate_gate("AND", [True, True, True]) is True
        assert logic.evaluate_gate("AND", [True, True, False]) is False
        assert logic.evaluate_gate("OR", [False, False, True]) is True
        assert logic.evaluate_gate("XOR", [True, True, True]) is True  # odd parity

    def test_unknown_gate_raises(self):
        with pytest.raises(ValidationError):
            logic.evaluate_gate("MAYBE", [True, False])

    def test_not_requires_exactly_one_input(self):
        with pytest.raises(ValidationError):
            logic.evaluate_gate("NOT", [True, False])

    def test_and_requires_at_least_two(self):
        with pytest.raises(ValidationError):
            logic.evaluate_gate("AND", [True])


class TestGateTruthTable:
    def test_and_truth_table_has_4_rows_for_2_inputs(self):
        result = logic.gate_truth_table("AND", 2)
        assert result.variables == ["A", "B"]
        assert len(result.rows) == 4
        # Only the all-true row should be True for AND
        true_rows = [r for r in result.rows if r[1]]
        assert len(true_rows) == 1
        assert true_rows[0][0] == [True, True]

    def test_not_truth_table(self):
        result = logic.gate_truth_table("NOT", 1)
        assert result.variables == ["A"]
        assert len(result.rows) == 2

    def test_rejects_too_many_inputs(self):
        with pytest.raises(ValidationError):
            logic.gate_truth_table("AND", 6)


class TestExpressionParsing:
    def test_simple_and(self):
        result = logic.expression_truth_table("A AND B")
        assert result.variables == ["A", "B"]
        true_rows = [r for r in result.rows if r[1]]
        assert len(true_rows) == 1

    def test_operator_precedence_not_and_or(self):
        # NOT binds tighter than AND, which binds tighter than OR
        ast = logic.parse_expression("A OR B AND NOT C")
        # Should parse as: A OR (B AND (NOT C))
        assert ast[0] == "OR"
        assert ast[2][0] == "AND"
        assert ast[2][2][0] == "NOT"

    def test_parentheses_override_precedence(self):
        ast = logic.parse_expression("(A OR B) AND C")
        assert ast[0] == "AND"
        assert ast[1][0] == "OR"

    def test_three_variable_expression(self):
        result = logic.expression_truth_table("A AND (B OR NOT C)")
        assert result.variables == ["A", "B", "C"]
        assert len(result.rows) == 8
        # A=T, B=F, C=F -> B OR NOT C = F OR T = T -> A AND T = T
        for combo, output in result.rows:
            a, b, c = combo
            expected = a and (b or not c)
            assert output is expected

    def test_empty_expression_raises(self):
        with pytest.raises(ValidationError):
            logic.expression_truth_table("")

    def test_unmatched_parenthesis_raises(self):
        with pytest.raises(ValidationError):
            logic.expression_truth_table("(A AND B")

    def test_invalid_character_raises(self):
        with pytest.raises(ValidationError):
            logic.expression_truth_table("A AND 1")

    def test_too_many_variables_raises(self):
        with pytest.raises(ValidationError):
            logic.expression_truth_table("A AND B AND C AND D AND E AND F")
