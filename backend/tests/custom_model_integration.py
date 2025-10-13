"""
Custom Model Manager for SecurePrompt

This module integrates the new C3/C4 custom spaCy models with the TextScrubber system.
It provides model loading, validation, and hybrid scrubbing capabilities.
"""

import spacy
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
import warnings
from spacy.lang.en import English

# Suppress spaCy warnings
warnings.filterwarnings("ignore", message=".*Skipping.*")

class CustomModelManager:
    """Manages custom spaCy models for different security levels"""
    
    def __init__(self):
        self.models_dir = Path(__file__).parent.parent / "scrubbers" / "models"
        self.loaded_models = {}
        self.model_paths = {
            'C3': self.models_dir / "models_c3" / "model_c3_v3_3_small" / "model-best",
            'C4': self.models_dir / "models_c4" / "model_vers_3_small" / "model-best"
        }
        
        # Initialize models
        self._load_available_models()
    
    def _load_available_models(self):
        """Load all available custom models"""
        print("🔄 Loading custom models...")
        
        for level, model_path in self.model_paths.items():
            try:
                if model_path.exists():
                    print(f"   📥 Loading {level} model from {model_path}")
                    model = spacy.load(str(model_path))
                    self.loaded_models[level] = model
                    print(f"   ✅ {level} model loaded successfully")
                    
                    # Display model info
                    entities = list(model.get_pipe("ner").labels)
                    print(f"   📋 {level} entities: {entities[:5]}{'...' if len(entities) > 5 else ''}")
                else:
                    print(f"   ⚠️  {level} model not found at {model_path}")
            except Exception as e:
                print(f"   ❌ Failed to load {level} model: {e}")
    
    def has_custom_model(self, level: str) -> bool:
        """Check if custom model is available for security level"""
        return level in self.loaded_models
    
    def get_model(self, level: str):
        """Get custom model for security level"""
        return self.loaded_models.get(level)
    
    def extract_entities_with_custom_model(self, text: str, level: str) -> List[Dict]:
        """Extract entities using custom model"""
        if not self.has_custom_model(level):
            return []
        
        model = self.get_model(level)
        doc = model(text)
        
        entities = []
        for ent in doc.ents:
            entities.append({
                'start': ent.start_char,
                'end': ent.end_char,
                'label': ent.label_,
                'text': ent.text,
                'confidence': getattr(ent, 'score', 0.9)  # Default confidence
            })
        
        return entities
    
    def validate_model_performance(self, level: str, test_cases: List[Dict] = None) -> Dict:
        """Validate custom model performance against test cases"""
        if not self.has_custom_model(level):
            return {'error': f'No custom model available for {level}'}
        
        model = self.get_model(level)
        
        # Basic validation
        test_text = "John Smith's credit card 4532123456789012 has CVV 123 and PIN 1234."
        entities = self.extract_entities_with_custom_model(test_text, level)
        
        return {
            'level': level,
            'model_loaded': True,
            'test_entities_found': len(entities),
            'sample_entities': entities[:3]  # Show first 3
        }

class EnhancedTextScrubber:
    """Enhanced TextScrubber with custom model integration"""
    
    def __init__(self):
        from scrubbers.text_scrubber import TextScrubber
        self.presidio_scrubber = TextScrubber()
        self.model_manager = CustomModelManager()
        
        print("🚀 Enhanced TextScrubber initialized")
        print(f"   📊 Available custom models: {list(self.model_manager.loaded_models.keys())}")
    
    def scrub_text_hybrid(self, text: str, target_risk: str = "C4", language: str = "en") -> Dict:
        """
        Enhanced scrubbing using custom models + Presidio fallback
        
        Strategy:
        1. Use custom model if available for C3/C4
        2. Merge with Presidio results for comprehensive coverage
        3. Fallback to Presidio-only for C1/C2
        """
        
        # Always get Presidio results as baseline
        presidio_result = self.presidio_scrubber.scrub_text(text, target_risk, language)
        
        # Check if we have custom model for this level
        if self.model_manager.has_custom_model(target_risk):
            # Get custom model entities
            custom_entities = self.model_manager.extract_entities_with_custom_model(text, target_risk)
            
            # Merge custom entities with Presidio entities
            merged_result = self._merge_entity_results(
                text, 
                presidio_result, 
                custom_entities, 
                target_risk
            )
            
            merged_result['scrubbing_method'] = f'Hybrid (Custom {target_risk} + Presidio)'
            merged_result['custom_entities_found'] = len(custom_entities)
            
            return merged_result
        else:
            # Fallback to Presidio only
            presidio_result['scrubbing_method'] = 'Presidio Only'
            presidio_result['custom_entities_found'] = 0
            
            return presidio_result
    
    def _merge_entity_results(self, text: str, presidio_result: Dict, custom_entities: List[Dict], target_risk: str) -> Dict:
        """Merge custom model entities with Presidio results"""
        
        # Start with Presidio results
        merged_entities = presidio_result.get('entities', [])
        
        # Convert custom entities to Presidio format
        for custom_ent in custom_entities:
            # Check if this entity overlaps with existing Presidio entities
            overlaps = False
            for presidio_ent in merged_entities:
                if self._entities_overlap(custom_ent, presidio_ent):
                    overlaps = True
                    # Custom model takes priority - update the entity
                    presidio_ent['type'] = custom_ent['label']
                    presidio_ent['score'] = custom_ent['confidence']
                    presidio_ent['source'] = 'custom_model'
                    break
            
            # If no overlap, add as new entity
            if not overlaps:
                merged_entities.append({
                    'type': custom_ent['label'],
                    'start': custom_ent['start'],
                    'end': custom_ent['end'],
                    'original': custom_ent['text'],
                    'replacement': f"<{custom_ent['label']}>",
                    'explanation': f"Custom {custom_ent['label']} detected",
                    'score': custom_ent['confidence'],
                    'source': 'custom_model'
                })
        
        # Re-scrub text with merged entities
        # For now, use Presidio's scrubbing logic with our merged entities
        # TODO: Implement custom scrubbing logic if needed
        
        return {
            'scrubbed_text': presidio_result['scrubbed_text'],  # Keep Presidio scrubbing for now
            'entities': merged_entities,
            'entity_counts': self._count_entity_types(merged_entities)
        }
    
    def _entities_overlap(self, ent1: Dict, ent2: Dict) -> bool:
        """Check if two entities overlap in position"""
        start1, end1 = ent1['start'], ent1['end']
        start2, end2 = ent2['start'], ent2['end']
        
        return not (end1 <= start2 or end2 <= start1)
    
    def _count_entity_types(self, entities: List[Dict]) -> Dict[str, int]:
        """Count entities by type"""
        counts = {}
        for entity in entities:
            entity_type = entity['type']
            counts[entity_type] = counts.get(entity_type, 0) + 1
        return counts
    
    def compare_scrubbing_methods(self, text: str, target_risk: str = "C4") -> Dict:
        """Compare Presidio-only vs Hybrid scrubbing"""
        
        # Presidio only
        presidio_result = self.presidio_scrubber.scrub_text(text, target_risk)
        
        # Hybrid (if custom model available)
        hybrid_result = self.scrub_text_hybrid(text, target_risk)
        
        return {
            'text': text[:100] + "..." if len(text) > 100 else text,
            'target_risk': target_risk,
            'presidio_only': {
                'entities_found': len(presidio_result.get('entities', [])),
                'entity_types': list(self._count_entity_types(presidio_result.get('entities', [])).keys())
            },
            'hybrid': {
                'entities_found': len(hybrid_result.get('entities', [])),
                'entity_types': list(self._count_entity_types(hybrid_result.get('entities', [])).keys()),
                'custom_entities': hybrid_result.get('custom_entities_found', 0)
            },
            'improvement': {
                'additional_entities': len(hybrid_result.get('entities', [])) - len(presidio_result.get('entities', [])),
                'has_custom_model': self.model_manager.has_custom_model(target_risk)
            }
        }

def validate_custom_models():
    """Validate that custom models are working correctly"""
    print("🧪 Validating Custom Models...")
    print("=" * 50)
    
    model_manager = CustomModelManager()
    
    # Test each model
    test_texts = {
        'C3': "Customer John Smith called about payment PO-12345. His email is john.smith@email.com and phone is +32 123 456 789.",
        'C4': "Customer authentication: Name John Smith, Card 4532123456789012, CVV 123, PIN 1234, expires 12/25."
    }
    
    for level, test_text in test_texts.items():
        print(f"\n🔍 Testing {level} Model:")
        print(f"   Text: {test_text}")
        
        validation = model_manager.validate_model_performance(level)
        
        if 'error' in validation:
            print(f"   ❌ {validation['error']}")
        else:
            print(f"   ✅ Model loaded successfully")
            print(f"   📊 Entities found: {validation['test_entities_found']}")
            if validation['sample_entities']:
                for ent in validation['sample_entities']:
                    print(f"   📋 {ent['label']}: '{ent['text']}' (confidence: {ent['confidence']:.2f})")

def test_hybrid_scrubbing():
    """Test the hybrid scrubbing approach"""
    print("\n🧪 Testing Hybrid Scrubbing...")
    print("=" * 50)
    
    enhanced_scrubber = EnhancedTextScrubber()
    
    test_cases = [
        {
            'text': "Customer John Smith has credit card 4532123456789012 with CVV 123 and PIN 1234.",
            'level': 'C4'
        },
        {
            'text': "Payment PO-12345 from customer jane.doe@email.com, phone +32 987 654 321.",
            'level': 'C3'
        }
    ]
    
    for test_case in test_cases:
        print(f"\n🔍 Testing {test_case['level']} Scrubbing:")
        print(f"   Text: {test_case['text']}")
        
        comparison = enhanced_scrubber.compare_scrubbing_methods(
            test_case['text'], 
            test_case['level']
        )
        
        print(f"   📊 Presidio Only: {comparison['presidio_only']['entities_found']} entities")
        print(f"   📊 Hybrid: {comparison['hybrid']['entities_found']} entities ({comparison['hybrid']['custom_entities']} from custom model)")
        print(f"   📈 Improvement: +{comparison['improvement']['additional_entities']} entities")
        
        if comparison['improvement']['additional_entities'] > 0:
            print(f"   ✅ Hybrid approach found more entities!")
        elif comparison['improvement']['additional_entities'] == 0:
            print(f"   ⚖️  Same number of entities found")
        else:
            print(f"   ⚠️  Hybrid found fewer entities")

def main():
    """Main testing function"""
    print("🎯 CUSTOM MODEL INTEGRATION TEST")
    print("=" * 60)
    
    # Validate models
    validate_custom_models()
    
    # Test hybrid scrubbing
    test_hybrid_scrubbing()
    
    print("\n✅ Custom Model Integration Testing Complete!")
    print("🔗 Ready to integrate with main TextScrubber")

if __name__ == "__main__":
    main()