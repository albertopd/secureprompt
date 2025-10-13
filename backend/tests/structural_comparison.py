#!/usr/bin/env python3
"""
Structural comparator for sanitization tests
Compares the structure of masking rather than exact labels
"""

import re
from typing import List, Tuple, Dict, Any

def extract_masked_positions(text: str) -> List[Dict[str, Any]]:
    """
    Extract positions and types of masked entities in text
    
    Returns:
        List[Dict]: List of masked entities with position, length and type
    """
    masked_entities = []
    
    # Pattern pour trouver toutes les étiquettes <TYPE>
    pattern = r'<([^>]+)>'
    matches = re.finditer(pattern, text)
    
    for match in matches:
        masked_entities.append({
            'start': match.start(),
            'end': match.end(),
            'length': match.end() - match.start(),
            'type': match.group(1),
            'original_text': match.group(0)
        })
    
    return masked_entities

def normalize_text_for_comparison(text: str) -> str:
    """
    Normalize text by replacing all labels with a generic placeholder
    to enable structural comparison
    """
    # Replace all labels with <MASKED>
    normalized = re.sub(r'<[^>]+>', '<MASKED>', text)
    return normalized

def compare_structure(expected: str, actual: str, tolerance: int = 5) -> Dict[str, Any]:
    """
    Compare masking structure between two texts
    
    Args:
        expected: Expected text with labels
        actual: Actual text with labels  
        tolerance: Tolerance in characters for positions (default: 5)
        
    Returns:
        Dict with comparison results
    """
    expected_entities = extract_masked_positions(expected)
    actual_entities = extract_masked_positions(actual)
    
    # Normalize texts for structural comparison
    expected_normalized = normalize_text_for_comparison(expected)
    actual_normalized = normalize_text_for_comparison(actual)
    
    # Comparisons
    result = {
        'structure_match': expected_normalized == actual_normalized,
        'entity_count_match': len(expected_entities) == len(actual_entities),
        'expected_count': len(expected_entities),
        'actual_count': len(actual_entities),
        'expected_entities': expected_entities,
        'actual_entities': actual_entities,
        'position_matches': [],
        'score': 0.0
    }
    
    # Compare positions (with tolerance)
    if len(expected_entities) > 0 and len(actual_entities) > 0:
        # Try to match entities by position
        for exp_entity in expected_entities:
            best_match = None
            best_distance = float('inf')
            
            for act_entity in actual_entities:
                # Distance between start positions
                distance = abs(exp_entity['start'] - act_entity['start'])
                if distance <= tolerance and distance < best_distance:
                    best_match = act_entity
                    best_distance = distance
            
            if best_match:
                result['position_matches'].append({
                    'expected': exp_entity,
                    'actual': best_match,
                    'distance': best_distance
                })
    
    # Calculate overall score
    score = 0.0
    
    # 40% for structural match
    if result['structure_match']:
        score += 0.4
    
    # 30% for entity count
    if result['entity_count_match']:
        score += 0.3
    
    # 30% for positions (proportional to matches)
    if len(expected_entities) > 0:
        position_score = len(result['position_matches']) / len(expected_entities)
        score += 0.3 * position_score
    elif len(actual_entities) == 0:
        # Case where no entities are expected and none are found
        score += 0.3
    
    result['score'] = score
    result['passed'] = score >= 0.7  # 70% threshold to consider as passed
    
    return result

def structural_comparison_summary(expected: str, actual: str) -> str:
    """
    Generate a text summary of the structural comparison
    """
    comparison = compare_structure(expected, actual)
    
    summary_parts = []
    
    if comparison['structure_match']:
        summary_parts.append("✅ Identical structure")
    else:
        summary_parts.append("❌ Different structure")
    
    if comparison['entity_count_match']:
        summary_parts.append(f"✅ Same entity count ({comparison['expected_count']})")
    else:
        summary_parts.append(f"❌ Different count: {comparison['expected_count']} vs {comparison['actual_count']}")
    
    if comparison['position_matches']:
        match_ratio = len(comparison['position_matches']) / max(comparison['expected_count'], 1)
        summary_parts.append(f"📍 Positions: {len(comparison['position_matches'])}/{comparison['expected_count']} matches ({match_ratio:.1%})")
    
    summary_parts.append(f"🎯 Score: {comparison['score']:.1%}")
    
    return " | ".join(summary_parts)

# Test the function
if __name__ == "__main__":
    # Test examples
    test_cases = [
        {
            'expected': 'Customer <CUSTOMER_NAME> has PIN <PIN> and email <EMAIL>',
            'actual': 'Customer <PERSON> has PIN <PIN> and email <EMAIL_ADDRESS>'
        },
        {
            'expected': 'Amount <AMOUNT> for <CUSTOMER_NAME>',
            'actual': 'Amount <FINANCIAL_AMOUNT> for <PERSON>'
        },
        {
            'expected': 'No sensitive data here',
            'actual': 'No sensitive data here'
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n=== TEST {i} ===")
        print(f"Expected: {test['expected']}")
        print(f"Actual:   {test['actual']}")
        
        result = compare_structure(test['expected'], test['actual'])
        print(f"Result: {structural_comparison_summary(test['expected'], test['actual'])}")
        print(f"Passed: {'✅' if result['passed'] else '❌'}")