"""
Logic module -- gate simulation and truth table generation.

V1 scope (basic gates) plus the V2-roadmap "truth table generator" and
"advanced logic tools" brought forward, since Python removes the memory
constraints that deferred them on the TI-84.

Supports:
  - Direct gate evaluation (AND, OR, NOT, XOR, NAND, NOR, XNOR)
  - Truth table generation for a single gate at arbitrary input count
  - Boolean expression parsing + truth table generation, e.g. "A AND (B OR NOT C)"
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from itertools import product

from core.validation import ValidationError

# ---------------------------------------------------------------------------
# Basic gate evaluation
# ---------------------------------------------------------------------------

# Two-input gates (or fold across N inputs for AND/OR/XOR/NAND/NOR/XNOR)
_UNARY_GATES = {"NOT"}
_NARY_GATES = {"AND", "OR", "XOR", "NAND", "NOR", "XNOR"}
GATE_NAMES = sorted(_UNARY_GATES | _NARY_GATES)


def evaluate_gate(gate: str, inputs: list[bool]) -> bool:
    """Evaluate a named gate against a list of boolean inputs."""
    gate = gate.strip().upper()

    if gate not in GATE_NAMES:
        raise ValidationError(f"Unknown gate '{gate}'. Valid gates: {', '.join(GATE_NAMES)}.")

    if gate == "NOT":
        if len(inputs) != 1:
            raise ValidationError("NOT takes exactly 1 input.")
        return not inputs[0]

    if len(inputs) < 2:
        raise ValidationError(f"{gate} requires at least 2 inputs.")

    if gate == "AND":
        return all(inputs)
    if gate == "OR":
        return any(inputs)
    if gate == "XOR":
        return sum(inputs) % 2 == 1
    if gate == "NAND":
        return not all(inputs)
    if gate == "NOR":
        return not any(inputs)
    if gate == "XNOR":
        return sum(inputs) % 2 == 0

    raise ValidationError(f"Gate '{gate}' is recognized but not implemented.")  # pragma: no cover


@dataclass
class TruthTableResult:
    variables: list[str]
    rows: list[tuple[list[bool], bool]]  # (input combination, output)


def gate_truth_table(gate: str, num_inputs: int) -> TruthTableResult:
    """Generate a full truth table for a single named gate at the given input count."""
    gate_upper = gate.strip().upper()
    if gate_upper == "NOT" and num_inputs != 1:
        raise ValidationError("NOT only accepts 1 input.")
    if gate_upper != "NOT" and num_inputs < 2:
        raise ValidationError(f"{gate_upper} requires at least 2 inputs.")
    if num_inputs > 5:
        raise ValidationError("Limit truth tables to 5 inputs (32 rows) for readability.")

    variables = [chr(ord("A") + i) for i in range(num_inputs)]
    rows = []
    for combo in product([False, True], repeat=num_inputs):
        rows.append((list(combo), evaluate_gate(gate_upper, list(combo))))

    return TruthTableResult(variables, rows)


# ---------------------------------------------------------------------------
# Boolean expression parsing (e.g. "A AND (B OR NOT C)")
# ---------------------------------------------------------------------------
# Precedence, highest to lowest: NOT > AND/NAND > XOR/XNOR > OR/NOR

_TOKEN_RE = re.compile(
    r"\s*(?:(?P<LPAREN>\()|(?P<RPAREN>\))|(?P<OP>NAND|NOR|XNOR|AND|OR|XOR|NOT)|(?P<VAR>[A-Za-z]))",
    re.IGNORECASE,
)


def _tokenize(expr: str) -> list[str]:
    tokens = []
    pos = 0
    while pos < len(expr):
        m = _TOKEN_RE.match(expr, pos)
        if not m or m.end() == pos:
            if expr[pos].isspace():
                pos += 1
                continue
            raise ValidationError(f"Unexpected character '{expr[pos]}' in expression at position {pos}.")
        kind = m.lastgroup
        text = m.group(kind)
        if kind == "OP":
            tokens.append(text.upper())
        elif kind == "VAR":
            tokens.append(text.upper())
        else:
            tokens.append(text)
        pos = m.end()
    return tokens


class _Parser:
    """Recursive-descent parser for boolean expressions -> nested tuple AST."""

    def __init__(self, tokens: list[str]):
        self.tokens = tokens
        self.pos = 0

    def _peek(self) -> str | None:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def _advance(self) -> str:
        tok = self._peek()
        if tok is None:
            raise ValidationError("Unexpected end of expression.")
        self.pos += 1
        return tok

    def parse(self):
        node = self._or_expr()
        if self.pos != len(self.tokens):
            raise ValidationError(f"Unexpected token '{self._peek()}' -- check parentheses/operators.")
        return node

    def _or_expr(self):
        node = self._xor_expr()
        while self._peek() in ("OR", "NOR"):
            op = self._advance()
            node = (op, node, self._xor_expr())
        return node

    def _xor_expr(self):
        node = self._and_expr()
        while self._peek() in ("XOR", "XNOR"):
            op = self._advance()
            node = (op, node, self._and_expr())
        return node

    def _and_expr(self):
        node = self._not_expr()
        while self._peek() in ("AND", "NAND"):
            op = self._advance()
            node = (op, node, self._not_expr())
        return node

    def _not_expr(self):
        if self._peek() == "NOT":
            self._advance()
            return ("NOT", self._not_expr())
        return self._primary()

    def _primary(self):
        tok = self._peek()
        if tok == "(":
            self._advance()
            node = self._or_expr()
            if self._advance() != ")":
                raise ValidationError("Missing closing parenthesis.")
            return node
        if tok is not None and len(tok) == 1 and tok.isalpha():
            self._advance()
            return ("VAR", tok)
        raise ValidationError(f"Expected a variable or '(' but got '{tok}'.")


def parse_expression(expr: str):
    """Parse a boolean expression string into an AST."""
    if not expr.strip():
        raise ValidationError("Expression cannot be empty.")
    tokens = _tokenize(expr)
    if not tokens:
        raise ValidationError("Expression cannot be empty.")
    return _Parser(tokens).parse()


def _eval_ast(node, values: dict[str, bool]) -> bool:
    if node[0] == "VAR":
        return values[node[1]]
    if node[0] == "NOT":
        return not _eval_ast(node[1], values)
    op, left, right = node
    l, r = _eval_ast(left, values), _eval_ast(right, values)
    return evaluate_gate(op, [l, r])


def _extract_variables(node, found: set[str]) -> None:
    if node[0] == "VAR":
        found.add(node[1])
    elif node[0] == "NOT":
        _extract_variables(node[1], found)
    else:
        _extract_variables(node[1], found)
        _extract_variables(node[2], found)


def expression_truth_table(expr: str) -> TruthTableResult:
    """Parse a boolean expression and generate its full truth table."""
    ast = parse_expression(expr)
    found: set[str] = set()
    _extract_variables(ast, found)
    variables = sorted(found)

    if not variables:
        raise ValidationError("Expression contains no variables.")
    if len(variables) > 5:
        raise ValidationError("Limit expressions to 5 variables (32 rows) for readability.")

    rows = []
    for combo in product([False, True], repeat=len(variables)):
        values = dict(zip(variables, combo))
        rows.append((list(combo), _eval_ast(ast, values)))

    return TruthTableResult(variables, rows)
