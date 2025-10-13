"""
Simple structural comparison script to test only structure, not labels
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import re
from scrubbers.text_scrubber import TextScrubber

def structural_compare_only(expected: str, actual: str) -> bool:
    """
    Compare only the structure by replacing all labels with <MASKED>
    """
    # Replace all labels with generic placeholder
    expected_normalized = re.sub(r'<[^>]+>', '<MASKED>', expected)
    actual_normalized = re.sub(r'<[^>]+>', '<MASKED>', actual)
    
    return expected_normalized == actual_normalized

def test_structural_only():
    """Test examples with structural comparison only"""
    
    print("🔍 STRUCTURAL COMPARISON ONLY")
    print("=" * 50)
    
    scrubber = TextScrubber()
    
    # Test cases that should pass structurally but fail on labels
    examples = [
        {
            "name": "CVV Detection Issue",
            "prompt": "CVV 846 keeps getting declined",
            "expected": "CVV <CVC> keeps getting declined",  
            "level": "C4"
        },
        {
            "name": "PIN + Person Issue", 
            "prompt": "Jonathan Green insists their PIN is 2741",
            "expected": "Jonathan Green insists their PIN <PIN>",
            "level": "C4"
        },
        {
            "name": "Credit Card Labels",
            "prompt": "Card 4267022256893233 with CVV 787",
            "expected": "Card <CREDIT_CARD> with CVV <CVC>", 
            "level": "C4"
        },
        {
            "name": "Person Possessive",
            "prompt": "Linda Walker's information",
            "expected": "<PERSON>'s information",
            "level": "C3"
        }
    ]
    
    structural_matches = 0
    total_tests = len(examples)
    
    for example in examples:
        print(f"\n📝 {example['name']}:")
        print(f"Input:    '{example['prompt']}'")
        print(f"Expected: '{example['expected']}'")
        
        result = scrubber.scrub_text(example['prompt'], example['level'])
        actual = result['scrubbed_text']
        print(f"Actual:   '{actual}'")
        
        # Structural comparison only
        is_structural_match = structural_compare_only(example['expected'], actual)
        
        # Show normalized versions
        expected_norm = re.sub(r'<[^>]+>', '<MASKED>', example['expected'])
        actual_norm = re.sub(r'<[^>]+>', '<MASKED>', actual)
        
        print(f"Expected (normalized): '{expected_norm}'")
        print(f"Actual (normalized):   '{actual_norm}'")
        print(f"Structural Match: {'✅ YES' if is_structural_match else '❌ NO'}")
        
        if is_structural_match:
            structural_matches += 1
        
        print(f"Entities detected: {len(result['entities'])}")
        for entity in result['entities']:
            print(f"  - {entity['type']}: '{entity['original']}' -> '{entity['replacement']}'")
    
    print(f"\n🎯 STRUCTURAL RESULTS:")
    print(f"Structural matches: {structural_matches}/{total_tests} ({structural_matches/total_tests*100:.1f}%)")
    
    # Test a few more examples quickly
    print(f"\n🚀 QUICK STRUCTURAL TESTS:")
    quick_tests = [
        ("C3", "Customer John Smith email john@test.com", "Customer <PERSON> email <EMAIL_ADDRESS>"),
        ("C4", "User PIN 1234 CVV 567", "User PIN <PIN> CVV <CVC>"),
        ("C4", "Card expires 12/25", "Card expires <EXPIRATION_DATE>")
    ]
    
    quick_matches = 0
    for level, input_text, expected in quick_tests:
        result = scrubber.scrub_text(input_text, level)
        actual = result['scrubbed_text']
        
        is_match = structural_compare_only(expected, actual)
        quick_matches += is_match
        
        print(f"{level}: '{input_text}' -> {'✅' if is_match else '❌'}")
        print(f"  Expected: '{expected}'")
        print(f"  Actual:   '{actual}'")
        
        if not is_match:
            expected_norm = re.sub(r'<[^>]+>', '<MASKED>', expected)
            actual_norm = re.sub(r'<[^>]+>', '<MASKED>', actual)
            print(f"  Norm Exp: '{expected_norm}'")
            print(f"  Norm Act: '{actual_norm}'")
    
    print(f"\nQuick tests: {quick_matches}/{len(quick_tests)} ({quick_matches/len(quick_tests)*100:.1f}%)")
    
    return {
        'detailed_matches': structural_matches,
        'detailed_total': total_tests,
        'quick_matches': quick_matches,
        'quick_total': len(quick_tests),
        'overall_structural_rate': (structural_matches + quick_matches) / (total_tests + len(quick_tests))
    }

if __name__ == "__main__":
    results = test_structural_only()
    print(f"\n🎉 OVERALL STRUCTURAL PERFORMANCE: {results['overall_structural_rate']:.1%}")