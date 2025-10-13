"""
Test script to verify custom model integration with Estefania's TextScrubber
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent))

from scrubbers.text_scrubber import TextScrubber

def test_integration():
    """Test the enhanced TextScrubber with custom models"""
    
    print("🔍 Testing Enhanced TextScrubber Integration")
    print("=" * 50)
    
    # Initialize scrubber
    scrubber = TextScrubber()
    
    # Check if custom models are available
    if hasattr(scrubber, 'model_manager') and scrubber.model_manager:
        status = scrubber.model_manager.get_status()
        print(f"📊 Custom Models Status:")
        print(f"   Available: {status['available_models']}")
        print(f"   Total Loaded: {status['total_loaded']}")
        print(f"   Integration: {status['integration_status']}")
    else:
        print("📊 Custom Models: Not available (using Presidio only)")
    
    # Test cases
    test_cases = {
        'C3': "Customer John Smith email john@example.com needs help with payment PO-12345",
        'C4': "Authentication: PIN 1234, CVV 567, Card 4532-1234-5678-9012 expires 12/25"
    }
    
    print(f"\n🧪 Testing Scrubbing:")
    
    for level, text in test_cases.items():
        print(f"\n📝 {level} Test:")
        print(f"   Input:  {text}")
        
        result = scrubber.scrub_text(text, level)
        
        print(f"   Output: {result['scrubbed_text']}")
        print(f"   Entities: {len(result['entities'])}")
        
        for entity in result['entities']:
            print(f"     - {entity['type']}: '{entity['original']}' -> '{entity['replacement']}'")
    
    return True

def main():
    """Main test execution"""
    try:
        success = test_integration()
        if success:
            print(f"\n✅ Integration test completed successfully!")
            print(f"\n💡 Next steps:")
            print(f"   1. Download C3 model: https://drive.google.com/file/d/1yFl0jBxb3wynQ851yZGpP3ysjl230Wik/view?usp=drive_link")
            print(f"   2. Download C4 model: https://drive.google.com/file/d/1RtNWZmFGTEQhW5__MnkzQ458eJn2wzEE/view?usp=drive_link")
            print(f"   3. Extract to: backend/scrubbers/nlp/models_c3/ and backend/scrubbers/nlp/models_c4/")
            print(f"   4. Re-run this test to see enhanced performance")
        else:
            print(f"\n❌ Integration test failed")
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()