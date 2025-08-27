"""Rules engine for email processing with condition evaluation and action execution."""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from .api.models import Action, Classification, Condition, Decision, Rule


@dataclass
class RuleMatch:
    """Result of rule evaluation."""
    
    rule_id: str
    rule_name: str
    priority: int
    matched_conditions: List[str]
    actions: List[Action]


class RulesEngine:
    """Engine for evaluating rules and determining actions."""
    
    def __init__(self, rules: List[Rule]):
        """
        Initialize rules engine.
        
        Args:
            rules: List of rules to evaluate
        """
        # Sort rules by priority (lower number = higher priority)
        self.rules = sorted(rules, key=lambda r: r.priority)
    
    def evaluate(
        self,
        email: Dict[str, Any],
        classification: Classification
    ) -> List[RuleMatch]:
        """
        Evaluate all rules against an email and its classification.
        
        Args:
            email: Email data
            classification: ML classification results
            
        Returns:
            List of matched rules with their actions
        """
        matches = []
        
        for rule in self.rules:
            if not rule.enabled:
                continue
            
            # Evaluate conditions
            matched_conditions = self._evaluate_conditions(
                rule.conditions, 
                email, 
                classification
            )
            
            # If all conditions match, add to results
            if matched_conditions is not None:
                matches.append(RuleMatch(
                    rule_id=rule.id,
                    rule_name=rule.name,
                    priority=rule.priority,
                    matched_conditions=matched_conditions,
                    actions=rule.actions
                ))
        
        return matches
    
    def _evaluate_conditions(
        self,
        conditions: List[Condition],
        email: Dict[str, Any],
        classification: Classification
    ) -> Optional[List[str]]:
        """
        Evaluate a list of conditions.
        
        Args:
            conditions: Conditions to evaluate
            email: Email data
            classification: Classification results
            
        Returns:
            List of matched condition descriptions if all match, None otherwise
        """
        if not conditions:
            return []
        
        matched = []
        logic = conditions[0].logic if conditions else "AND"
        
        for condition in conditions:
            # Get field value
            value = self._get_field_value(condition.field, email, classification)
            
            # Evaluate condition
            if self._evaluate_condition(condition, value):
                matched.append(
                    f"{condition.field} {condition.operator} {condition.value}"
                )
            elif logic == "AND":
                # AND logic: all must match
                return None
        
        # OR logic: at least one must match
        if logic == "OR" and not matched:
            return None
        
        return matched
    
    def _get_field_value(
        self, 
        field: str, 
        email: Dict[str, Any],
        classification: Classification
    ) -> Any:
        """Get field value from email or classification."""
        # Handle classification fields
        if field.startswith("classification."):
            attr = field.split(".", 1)[1]
            return getattr(classification, attr, None)
        
        # Handle nested email fields
        if "." in field:
            parts = field.split(".")
            value = email
            for part in parts:
                if isinstance(value, dict) and part in value:
                    value = value[part]
                else:
                    return None
            return value
        
        # Direct email fields
        return email.get(field)
    
    def _evaluate_condition(self, condition: Condition, value: Any) -> bool:
        """Evaluate a single condition against a value."""
        operator = condition.operator
        expected = condition.value
        
        # Handle exists operator
        if operator == "exists":
            return value is not None
        
        # Handle None values for other operators
        if value is None:
            return False
        
        # Comparison operators
        if operator == "eq":
            return value == expected
        elif operator == "in":
            return value in expected if isinstance(expected, list) else False
        elif operator == "lt":
            return self._compare_values(value, expected, lambda a, b: a < b)
        elif operator == "lte":
            return self._compare_values(value, expected, lambda a, b: a <= b)
        elif operator == "gt":
            return self._compare_values(value, expected, lambda a, b: a > b)
        elif operator == "gte":
            return self._compare_values(value, expected, lambda a, b: a >= b)
        elif operator == "regex":
            return self._regex_match(str(value), str(expected))
        
        return False
    
    def _compare_values(
        self, 
        value: Any, 
        expected: Any,
        comparator: callable
    ) -> bool:
        """Compare values with type handling."""
        try:
            # Try numeric comparison
            if isinstance(value, (int, float)) and isinstance(expected, (int, float)):
                return comparator(value, expected)
            
            # Try string comparison
            return comparator(str(value), str(expected))
        except Exception:
            return False
    
    def _regex_match(self, value: str, pattern: str) -> bool:
        """Match value against regex pattern."""
        try:
            return bool(re.search(pattern, value, re.IGNORECASE))
        except Exception:
            return False
    
    def execute_actions(
        self,
        actions: List[Action],
        email: Dict[str, Any],
        decision: Decision
    ) -> List[Dict[str, Any]]:
        """
        Execute actions and return results.
        
        Args:
            actions: Actions to execute
            email: Email data
            decision: Decision record
            
        Returns:
            List of action execution results
        """
        results = []
        
        for action in actions:
            result = self._execute_action(action, email, decision)
            results.append({
                "type": action.type,
                "status": result["status"],
                "executedAt": datetime.now().isoformat(),
                "parameters": action.parameters,
                "result": result.get("result"),
                "error": result.get("error")
            })
        
        return results
    
    def _execute_action(
        self,
        action: Action,
        email: Dict[str, Any],
        decision: Decision
    ) -> Dict[str, Any]:
        """Execute a single action."""
        try:
            # Action implementations would go here
            # For now, return mock results
            
            if action.type == "set_classification":
                # Update classification
                return {
                    "status": "success",
                    "result": {
                        "category": action.parameters.get("category"),
                        "label": action.parameters.get("label")
                    }
                }
            
            elif action.type == "mark_read":
                return {"status": "success", "result": {"marked": True}}
            
            elif action.type == "create_calendar_event":
                event = action.parameters.get("event", {})
                return {
                    "status": "success",
                    "result": {
                        "eventId": f"evt_{datetime.now().timestamp()}",
                        "title": event.get("title"),
                        "startTime": event.get("startTime")
                    }
                }
            
            elif action.type == "add_contact":
                contact = action.parameters.get("contact", {})
                return {
                    "status": "success",
                    "result": {
                        "contactId": f"cnt_{datetime.now().timestamp()}",
                        "name": contact.get("name")
                    }
                }
            
            elif action.type == "save_to_folder":
                return {
                    "status": "success",
                    "result": {
                        "folder": action.parameters.get("folder")
                    }
                }
            
            else:
                # TODO: Implement remaining actions
                return {
                    "status": "pending",
                    "result": {"message": f"Action {action.type} not implemented"}
                }
                
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e)
            }


def create_rules_engine(rules_data: List[Dict[str, Any]]) -> RulesEngine:
    """
    Create rules engine from raw rule data.
    
    Args:
        rules_data: List of rule dictionaries
        
    Returns:
        Configured rules engine
    """
    rules = []
    
    for rule_data in rules_data:
        # Convert conditions
        conditions = []
        for cond_data in rule_data.get("conditions", []):
            conditions.append(Condition(**cond_data))
        
        # Convert actions
        actions = []
        for action_data in rule_data.get("actions", []):
            actions.append(Action(**action_data))
        
        # Create rule
        rule = Rule(
            id=rule_data["id"],
            name=rule_data["name"],
            description=rule_data.get("description"),
            priority=rule_data["priority"],
            enabled=rule_data.get("enabled", True),
            conditions=conditions,
            actions=actions
        )
        rules.append(rule)
    
    return RulesEngine(rules)
