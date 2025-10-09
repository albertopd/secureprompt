"""
Detailed analysis of specific C3 and C4 test cases
to understand why performance is still low
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from scrubbers.text_scrubber import TextScrubber
from tests.structural_comparison import compare_structure

def test_specific_examples():
    """Test specific examples to understand the issues"""
    
    print("🔍 DETAILED ANALYSIS: C3 and C4 Examples")
    print("=" * 60)
    
    scrubber = TextScrubber()
    
    # C3 Examples
    c3_examples = [
        {
            "prompt": "System check: is Linda Walker's information up to date?",
            "expected": "System check: is <PERSON>'s information up to date?",
            "response": "Customer Linda Walker: Email linda.walker@skynet.be, Phone +32 77 716 932",
            "expected_response": "Customer <PERSON>: Email linda.walker@skynet.be, Phone <PHONE_NUMBER>"
        },
        {
            "prompt": "Transaction PO-0010 failed - need to contact the customer",
            "expected": "Transaction <PAYMENT_ID> failed - need to contact the customer",
            "response": "Payment PO-0010: 10523.35 GBP from Chris Taylor to John Miller, Status: Completed",
            "expected_response": "Payment <PAYMENT_ID>: 10523.35 GBP from Chris Taylor to John Miller, Status: Completed"
        },
        {
            "prompt": "Customer verification: Chris Walker claims to be 23 years old - can you confirm?",
            "expected": "Customer verification: <PERSON> claims to be 23 years old - can you confirm?",
            "response": "Chris Walker is 23 years old",
            "expected_response": "<PERSON> is 23 years old"
        }
    ]
    
    # C4 Examples
    c4_examples = [
        {
            "prompt": "E-commerce issue: William Forbes says CVV 846 keeps getting declined online.",
            "expected": "E-commerce issue: William Forbes says CVV <CVC> keeps getting declined online.",
            "response": "I can see the CVV 846 mentioned. Please provide the customer name to verify this against our records.",
            "expected_response": "I can see the CVV <CVC> mentioned. Please provide the customer name to verify this against our records."
        },
        {
            "prompt": "Can someone double-check? Jonathan Green insists their PIN is 2741 but I'm seeing something different.",
            "expected": "Can someone double-check? Jonathan Green insists their PIN <PIN> but I'm seeing something different.",
            "response": "Authentication details for Jonathan Green: PIN 2741, CVV 996, Card 4673848664071750, Expires 10/29",
            "expected_response": "Authentication details for <PERSON>: PIN <PIN>, CVV <CVC>, Card <CREDIT_CARD>, Expires 10/29"
        },
        {
            "prompt": "Card verification: John Jones has card 4267022256893233 with CVV 787, expires 12/25.",
            "expected": "Card verification: John Jones has card <CREDIT_CARD> with CVV <CVC>, expires <EXPIRATION_DATE>.",
            "response": "Confirmed: John Jones's CVV 787 is correct. You can proceed with the transaction.",
            "expected_response": "Confirmed: <PERSON>'s CVV <CVC> is correct. You can proceed with the transaction."
        }
    ]
    
    print("\n📝 C3 CUSTOMER DATA EXAMPLES:")
    print("-" * 40)
    
    for i, example in enumerate(c3_examples, 1):
        print(f"\n🔍 C3 Example {i}:")
        print(f"Input:    '{example['prompt']}'")
        print(f"Expected: '{example['expected']}'")
        
        result = scrubber.scrub_text(example['prompt'], 'C3')
        actual = result['scrubbed_text']
        print(f"Actual:   '{actual}'")
        
        comparison = compare_structure(example['expected'], actual)
        is_match = comparison.get('structure_match', False)
        score = 1.0 if is_match else 0.0
        print(f"Match:    {is_match} (Score: {score:.1%})")
        
        if not is_match:
            print(f"Expected entities: {comparison.get('expected_count', 0)}")
            print(f"Actual entities:   {comparison.get('actual_count', 0)}")
            print(f"Structure match:   {comparison.get('structure_match', False)}")
        
        print(f"Entities detected: {len(result['entities'])}")
        for entity in result['entities']:
            print(f"  - {entity['type']}: '{entity['original']}' -> '{entity['replacement']}'")
    
    print("\n📝 C4 SENSITIVE DATA EXAMPLES:")
    print("-" * 40)
    
    for i, example in enumerate(c4_examples, 1):
        print(f"\n🔍 C4 Example {i}:")
        print(f"Input:    '{example['prompt']}'")
        print(f"Expected: '{example['expected']}'")
        
        result = scrubber.scrub_text(example['prompt'], 'C4')
        actual = result['scrubbed_text']
        print(f"Actual:   '{actual}'")
        
        comparison = compare_structure(example['expected'], actual)
        is_match = comparison.get('structure_match', False)
        score = 1.0 if is_match else 0.0
        print(f"Match:    {is_match} (Score: {score:.1%})")
        
        if not is_match:
            print(f"Expected entities: {comparison.get('expected_count', 0)}")
            print(f"Actual entities:   {comparison.get('actual_count', 0)}")
            print(f"Structure match:   {comparison.get('structure_match', False)}")
        
        print(f"Entities detected: {len(result['entities'])}")
        for entity in result['entities']:
            print(f"  - {entity['type']}: '{entity['original']}' -> '{entity['replacement']}'")
    
    print("\n🎯 ANALYSIS SUMMARY:")
    print("-" * 40)
    
    # Test what entities the models can detect
    print(f"\n🤖 Custom Model Detection Test:")
    
    test_texts = {
        'C3': "Customer John Smith email john@example.com payment PO-12345",
        'C4': "User PIN 1234 CVV 567 Card 4532-1234-5678-9012"
    }
    
    for level, text in test_texts.items():
        print(f"\n{level} Test: '{text}'")
        result = scrubber.scrub_text(text, level)
        print(f"Result: '{result['scrubbed_text']}'")
        entities_info = [f"{e['type']}:'{e['original']}'" for e in result['entities']]
        print(f"Entities: {entities_info}")

if __name__ == "__main__":
    test_specific_examples()