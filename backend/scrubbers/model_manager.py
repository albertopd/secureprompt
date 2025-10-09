"""
Model Manager for Custom spaCy Models

Integrates seamlessly with Estefania's TextScrubber without major modifications.
Provides optional enhancement for C3 and C4 security levels.
"""

import spacy
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)

class ModelManager:
    """
    Manages custom spaCy models for enhanced entity recognition.
    Falls back gracefully if models are not available.
    """
    
    def __init__(self):
        self.models = {}
        self.model_paths = self._get_model_paths()
        self._load_models()
    
    def _get_model_paths(self) -> Dict[str, Path]:
        """Get expected paths for custom models"""
        base_path = Path(__file__).parent / "nlp"
        return {
            'C3': base_path / "models_c3",
            'C4': base_path / "models_c4"
        }
    
    def _load_models(self):
        """Load available custom models"""
        for level, model_path in self.model_paths.items():
            try:
                if model_path.exists():
                    model = spacy.load(str(model_path))
                    self.models[level] = model
                    logger.info(f"✅ Custom model loaded for {level}")
                else:
                    logger.info(f"📁 Custom model not found for {level}: {model_path}")
            except Exception as e:
                logger.warning(f"⚠️  Failed to load custom model for {level}: {e}")
    
    def has_model(self, level: str) -> bool:
        """Check if custom model is available"""
        return level in self.models
    
    def enhance_entities(self, text: str, presidio_entities: List[Dict], target_risk: str) -> List[Dict]:
        """
        Enhance presidio entities with custom model results.
        
        Args:
            text: Original text
            presidio_entities: Entities detected by Presidio
            target_risk: Security level (C1, C2, C3, C4)
            
        Returns:
            Enhanced entity list combining both approaches
        """
        if not self.has_model(target_risk):
            return presidio_entities
        
        try:
            # Get custom model predictions
            model = self.models[target_risk]
            doc = model(text)
            
            # Convert spaCy entities to presidio format
            custom_entities = []
            for ent in doc.ents:
                custom_entities.append({
                    'entity_type': ent.label_,
                    'start': ent.start_char,
                    'end': ent.end_char,
                    'score': 0.95,  # High confidence for custom models
                    'source': 'custom_model'
                })
            
            # Merge with presidio entities (custom models take priority)
            merged = self._merge_entities(presidio_entities, custom_entities)
            
            logger.debug(f"Enhanced {target_risk}: {len(presidio_entities)} -> {len(merged)} entities")
            return merged
            
        except Exception as e:
            logger.error(f"Error enhancing entities with {target_risk} model: {e}")
            return presidio_entities
    
    def _merge_entities(self, presidio_entities: List[Dict], custom_entities: List[Dict]) -> List[Dict]:
        """Merge entity lists, giving priority to custom model entities"""
        result = []
        
        # Add custom entities first (they have priority)
        result.extend(custom_entities)
        
        # Add presidio entities that don't overlap with custom ones
        for presidio_entity in presidio_entities:
            if not self._overlaps_with_any(presidio_entity, custom_entities):
                result.append(presidio_entity)
        
        # Sort by start position
        result.sort(key=lambda x: x['start'])
        return result
    
    def _overlaps_with_any(self, entity: Dict, entity_list: List[Dict]) -> bool:
        """Check if entity overlaps with any entity in the list"""
        for other in entity_list:
            if (entity['start'] < other['end'] and entity['end'] > other['start']):
                return True
        return False
    
    def get_status(self) -> Dict:
        """Get status information about loaded models"""
        return {
            'available_models': list(self.models.keys()),
            'model_paths': {k: str(v) for k, v in self.model_paths.items()},
            'total_loaded': len(self.models),
            'integration_status': 'active' if self.models else 'disabled'
        }

# Global instance
_model_manager = None

def get_model_manager() -> ModelManager:
    """Get singleton model manager instance"""
    global _model_manager
    if _model_manager is None:
        _model_manager = ModelManager()
    return _model_manager