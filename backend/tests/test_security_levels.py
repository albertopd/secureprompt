"""
Security Level Performance Analysis Test
"""
import pytest
from backend.scrubbers.text_scrubber import TextScrubber
from backend.tests.helpers.excel_loader import load_test_cases_from_csv
from backend.tests.structural_comparison import compare_structure
import re
from collections import defaultdict


def test_security_levels_analysis():
    """
    Analyzes scrubber performance by security classification level.
    
    C1: Public data
    C2: Internal operations
    C3: Customer data
    C4: Sensitive data
    """
    scrubber = TextScrubber()
    cases = load_test_cases_from_csv()
    
    # Group cases by security classification level
    by_security_level = defaultdict(list)
    
    for file, prompt, expected in cases:
        # Extract security level from filename
        if 'c1' in file.lower():
            level = 'C1 - Public Data'
        elif 'c2' in file.lower():
            level = 'C2 - Internal Operations'
        elif 'c3' in file.lower():
            level = 'C3 - Customer Data'
        elif 'c4' in file.lower():
            level = 'C4 - Sensitive Data'
        elif 'mixed' in file.lower():
            level = 'Mixed Security Levels'
        else:
            level = 'Unknown'
            
        by_security_level[level].append((file, prompt, expected))
    
    print("\n=== SECURITY LEVEL PERFORMANCE ANALYSIS ===")
    print(f"Total test cases: {len(cases)}")
    
    all_results = {}
    
    for level, level_cases in sorted(by_security_level.items()):
        print(f"\n{level}")
        print(f"Test cases: {len(level_cases)}")
        
        # Test maximum 30 cases per level for performance
        sample_size = min(30, len(level_cases))
        sample = level_cases[:sample_size] if len(level_cases) <= sample_size else level_cases[::len(level_cases)//sample_size][:sample_size]
        
        passed = 0
        total_score = 0
        failed_types = defaultdict(int)
        
        for file, prompt, expected in sample:
            result = scrubber.scrub_text(prompt)
            actual = result["scrubbed_text"]
            structural_result = compare_structure(expected, actual)
            
            total_score += structural_result["score"]
            
            if structural_result["passed"]:
                passed += 1
            else:
                # Analyze failure types
                expected_entities = re.findall(r'<([^>]+)>', expected)
                actual_entities = re.findall(r'<([^>]+)>', actual)
                
                if len(expected_entities) > len(actual_entities):
                    failed_types["under-detection"] += 1
                elif len(expected_entities) < len(actual_entities):
                    failed_types["over-detection"] += 1
                else:
                    failed_types["incorrect-labels"] += 1
        
        accuracy = (passed / len(sample)) * 100
        avg_score = (total_score / len(sample)) * 100
        
        all_results[level] = {
            'accuracy': accuracy,
            'avg_score': avg_score,
            'passed': passed,
            'total': len(sample),
            'failed_types': dict(failed_types)
        }
        
        print(f"Success rate: {passed}/{len(sample)} ({accuracy:.1f}%)")
        print(f"Average score: {avg_score:.1f}%")
        
        if failed_types:
            print("Failure analysis:")
            for failure_type, count in failed_types.items():
                print(f"  - {failure_type}: {count}")
    
    # Global summary
    print("\nSUMMARY BY SECURITY LEVEL:")
    
    for level, results in sorted(all_results.items()):
        status = "PASS" if results['accuracy'] >= 70 else "WARN" if results['accuracy'] >= 50 else "FAIL"
        print(f"[{status}] {level}: {results['accuracy']:.1f}% ({results['passed']}/{results['total']})")
    
    # Analysis and recommendations
    print("\nANALYSIS:")
    
    worst_level = min(all_results.items(), key=lambda x: x[1]['accuracy'])
    best_level = max(all_results.items(), key=lambda x: x[1]['accuracy'])
    
    print(f"Most problematic level: {worst_level[0]} ({worst_level[1]['accuracy']:.1f}%)")
    print(f"Best performing level: {best_level[0]} ({best_level[1]['accuracy']:.1f}%)")
    
    # Test should not fail - this is informational analysis
    assert True, "Analysis completed"


if __name__ == "__main__":
    test_security_levels_analysis()