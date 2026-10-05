"""Structured validation results."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Issue:
    code: str
    objects: List[str]
    details: str
    severity: str = "error"          # "error" (hard rule) | "warning" (design heuristic)
    hint: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    object_ids: List[str] = field(default_factory=list)   # persistent model ids, filled in by validate_building

    def to_dict(self) -> Dict[str, Any]:
        d = {"code": self.code, "severity": self.severity, "object_ids": self.object_ids, "objects": self.objects,
             "message": self.details, "details": self.details}
        if self.hint:
            d["hint"] = self.hint
        if self.data:
            d["data"] = self.data
        return d


@dataclass
class ValidationReport:
    errors: List[Issue] = field(default_factory=list)
    warnings: List[Issue] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)

    @property
    def valid(self) -> bool:
        return not self.errors

    def add(self, issue: Issue):
        (self.errors if issue.severity == "error" else self.warnings).append(issue)

    def extend(self, issues):
        for i in issues:
            self.add(i)

    def to_dict(self) -> Dict[str, Any]:
        return {"valid": self.valid, "errors": [e.to_dict() for e in self.errors],
                "warnings": [w.to_dict() for w in self.warnings], "summary": self.summary}

    def format_for_agent(self) -> str:
        """Text fed back to the LLM so it can repair the design."""
        if self.valid:
            return "VALIDATION PASSED.\n" + (
                "Design heuristics to consider:\n" + json.dumps([w.to_dict() for w in self.warnings], indent=2)
                if self.warnings else "")
        return ("VALIDATION FAILED. The validator (not you) decides geometric validity. Fix every error by editing "
                "design.py -- do not remove rooms from the brief just to silence an error unless the brief is truly "
                "impossible, in which case explain why and stop.\n"
                + json.dumps({"valid": False, "errors": [e.to_dict() for e in self.errors],
                              "warnings": [w.to_dict() for w in self.warnings]}, indent=2))


def error(code, objects, details, hint=None, data=None) -> Issue:
    return Issue(code, list(objects), details, "error", hint, data)


def warning(code, objects, details, hint=None, data=None) -> Issue:
    return Issue(code, list(objects), details, "warning", hint, data)
