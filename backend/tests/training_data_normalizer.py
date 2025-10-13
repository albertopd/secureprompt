"""
Training Data Normalizer

This script fixes inconsistent scrubbing in training data by re-scrubbing all prompts
with consistent security level standards. This should dramatically improve model performance.
"""

import pandas as pd
import os
import sys
from pathlib import Path
from typing import Dict, List
import shutil
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrubbers.text_scrubber import TextScrubber

class TrainingDataNormalizer:
    def __init__(self):
        self.scrubber = TextScrubber()
        self.data_dir = Path(__file__).parent / "data" / "prompts"
        self.backup_dir = self.data_dir / "backup" / datetime.now().strftime("%Y%m%d_%H%M%S")
        self.normalized_dir = self.data_dir / "normalized"
        
        # Create directories
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.normalized_dir.mkdir(parents=True, exist_ok=True)
        
        self.stats = {
            'files_processed': 0,
            'rows_normalized': 0,
            'entities_fixed': 0,
            'by_level': {}
        }

    def backup_original_files(self):
        """Create backup of original files before normalization"""
        print("🔄 Creating backup of original files...")
        
        csv_files = list(self.data_dir.glob("*.csv"))
        for csv_file in csv_files:
            if csv_file.parent != self.backup_dir:  # Don't backup backup files
                backup_path = self.backup_dir / csv_file.name
                shutil.copy2(csv_file, backup_path)
                print(f"   ✅ Backed up: {csv_file.name}")
        
        print(f"📁 Backup created at: {self.backup_dir}")

    def normalize_csv_file(self, csv_path: Path, level: str) -> Dict:
        """Normalize a single CSV file by re-scrubbing all content"""
        print(f"\n🔧 Normalizing {csv_path.name} (Level {level})...")
        
        try:
            df = pd.read_csv(csv_path)
        except Exception as e:
            return {'error': f"Failed to read CSV: {e}"}
        
        # Find column names (handle variations)
        prompt_col = None
        sanitized_prompt_col = None
        response_col = None
        sanitized_response_col = None
        
        for col in df.columns:
            col_lower = col.lower()
            if 'prompt' in col_lower and 'sanitized' not in col_lower:
                prompt_col = col
            elif 'prompt' in col_lower and ('sanitized' in col_lower or 'scrub' in col_lower):
                sanitized_prompt_col = col
            elif 'response' in col_lower and 'sanitized' not in col_lower:
                response_col = col
            elif 'response' in col_lower and ('sanitized' in col_lower or 'scrub' in col_lower):
                sanitized_response_col = col
        
        if not prompt_col:
            return {'error': f"Prompt column not found. Available: {list(df.columns)}"}
        
        # Create new sanitized columns if they don't exist
        if not sanitized_prompt_col:
            sanitized_prompt_col = 'Sanitized_Prompt'
        if not sanitized_response_col and response_col:
            sanitized_response_col = 'Sanitized_Response'
        
        rows_processed = 0
        entities_fixed = 0
        
        print(f"   📊 Processing {len(df)} rows...")
        
        for idx, row in df.iterrows():
            # Normalize prompt
            if pd.notna(row[prompt_col]):
                result = self.scrubber.scrub_text(row[prompt_col], level)
                df.loc[idx, sanitized_prompt_col] = result['scrubbed_text']
                entities_fixed += len(result.get('entities', []))
            
            # Normalize response (if available)
            if response_col and pd.notna(row[response_col]):
                result = self.scrubber.scrub_text(row[response_col], level)
                df.loc[idx, sanitized_response_col] = result['scrubbed_text']
                entities_fixed += len(result.get('entities', []))
            
            rows_processed += 1
            
            # Progress indicator
            if rows_processed % 50 == 0:
                print(f"   📈 Processed {rows_processed}/{len(df)} rows...")
        
        # Ensure column order is logical
        column_order = [prompt_col, sanitized_prompt_col]
        if response_col:
            column_order.extend([response_col, sanitized_response_col])
        
        # Add any remaining columns
        for col in df.columns:
            if col not in column_order:
                column_order.append(col)
        
        df = df[column_order]
        
        # Save normalized file
        normalized_path = self.normalized_dir / csv_path.name
        df.to_csv(normalized_path, index=False)
        
        return {
            'file': csv_path.name,
            'level': level,
            'rows_processed': rows_processed,
            'entities_fixed': entities_fixed,
            'normalized_path': normalized_path
        }

    def normalize_all_files(self) -> Dict:
        """Normalize all CSV files"""
        print("🚀 Starting Training Data Normalization...")
        print("=" * 60)
        
        # Create backup first
        self.backup_original_files()
        
        # Find all CSV files and map to levels
        csv_files = list(self.data_dir.glob("*.csv"))
        level_files = {}
        
        for csv_file in csv_files:
            filename = csv_file.name.lower()
            if 'c1' in filename:
                level_files['C1'] = csv_file
            elif 'c2' in filename:
                level_files['C2'] = csv_file
            elif 'c3' in filename:
                level_files['C3'] = csv_file
            elif 'c4' in filename:
                level_files['C4'] = csv_file
        
        results = {}
        
        for level, csv_file in level_files.items():
            result = self.normalize_csv_file(csv_file, level)
            results[level] = result
            
            if 'error' not in result:
                self.stats['files_processed'] += 1
                self.stats['rows_normalized'] += result['rows_processed']
                self.stats['entities_fixed'] += result['entities_fixed']
                self.stats['by_level'][level] = result
                
                print(f"   ✅ {result['file']}: {result['rows_processed']} rows, {result['entities_fixed']} entities fixed")
            else:
                print(f"   ❌ {csv_file.name}: {result['error']}")
        
        return results

    def validate_normalized_data(self) -> Dict:
        """Validate that normalized data is now consistent"""
        print("\n🔍 Validating normalized data...")
        
        # Import validator
        from training_data_validator import TrainingDataValidator
        
        validator = TrainingDataValidator()
        validator.data_dir = self.normalized_dir  # Point to normalized files
        
        validation_results = validator.analyze_all_files()
        
        return validation_results

    def generate_normalization_report(self, results: Dict, validation: Dict = None) -> str:
        """Generate comprehensive normalization report"""
        report = []
        report.append("🎯 TRAINING DATA NORMALIZATION REPORT")
        report.append("=" * 60)
        report.append("")
        
        # Summary statistics
        report.append(f"📊 NORMALIZATION SUMMARY:")
        report.append(f"   • Files Processed: {self.stats['files_processed']}")
        report.append(f"   • Total Rows Normalized: {self.stats['rows_normalized']:,}")
        report.append(f"   • Total Entities Fixed: {self.stats['entities_fixed']:,}")
        report.append(f"   • Backup Location: {self.backup_dir}")
        report.append(f"   • Normalized Files: {self.normalized_dir}")
        report.append("")
        
        # Level-by-level details
        for level in ['C1', 'C2', 'C3', 'C4']:
            if level in results and 'error' not in results[level]:
                r = results[level]
                report.append(f"🔧 {level} NORMALIZATION:")
                report.append(f"   • File: {r['file']}")
                report.append(f"   • Rows Processed: {r['rows_processed']:,}")
                report.append(f"   • Entities Fixed: {r['entities_fixed']:,}")
                report.append(f"   • Output: {r['normalized_path'].name}")
                report.append("")
        
        # Validation results (if available)
        if validation:
            total_rows = sum(v.get('total_rows', 0) for v in validation.values() if 'error' not in v)
            total_inconsistent = sum(v.get('inconsistent_rows', 0) for v in validation.values() if 'error' not in v)
            consistency_rate = ((total_rows - total_inconsistent) / total_rows * 100) if total_rows > 0 else 0
            
            report.append(f"✅ POST-NORMALIZATION VALIDATION:")
            report.append(f"   • Overall Consistency Rate: {consistency_rate:.1f}%")
            
            if consistency_rate >= 95:
                report.append(f"   🎉 EXCELLENT: Data is now highly consistent!")
            elif consistency_rate >= 85:
                report.append(f"   ✅ GOOD: Data consistency significantly improved!")
            elif consistency_rate >= 70:
                report.append(f"   ⚠️  FAIR: Some issues remain, but much improved")
            else:
                report.append(f"   ❌ POOR: Additional normalization needed")
            
            report.append("")
            
            for level in ['C1', 'C2', 'C3', 'C4']:
                if level in validation:
                    v = validation[level]
                    if 'error' not in v:
                        report.append(f"   {level}: {v['consistency_rate']:.1f}% consistent ({v['inconsistent_rows']}/{v['total_rows']} issues)")
            
            report.append("")
        
        # Next steps
        report.append("🎯 NEXT STEPS:")
        report.append("   1. ✅ Training data normalized and validated")
        report.append("   2. 🔄 Integrate new C3/C4 custom models")
        report.append("   3. 🧪 Test performance with normalized data")
        report.append("   4. 📊 Compare before/after metrics")
        report.append("   5. 🚀 Deploy improved models")
        report.append("")
        
        report.append("📁 FILE LOCATIONS:")
        report.append(f"   • Original Files (Backup): {self.backup_dir}")
        report.append(f"   • Normalized Files: {self.normalized_dir}")
        report.append("   • Use normalized files for model training!")
        
        return "\n".join(report)

    def copy_normalized_to_main(self):
        """Copy normalized files back to main directory (optional)"""
        response = input("\n🤔 Copy normalized files back to main directory? (y/N): ")
        
        if response.lower() == 'y':
            normalized_files = list(self.normalized_dir.glob("*.csv"))
            for norm_file in normalized_files:
                main_path = self.data_dir / norm_file.name
                shutil.copy2(norm_file, main_path)
                print(f"   ✅ Copied: {norm_file.name}")
            
            print("📁 Normalized files copied to main directory")
        else:
            print("📁 Normalized files remain in /normalized directory")
            print(f"   Use files from: {self.normalized_dir}")

def main():
    """Main execution function"""
    normalizer = TrainingDataNormalizer()
    
    print("🎯 This will normalize all training data for consistent scrubbing.")
    print("   Original files will be backed up automatically.")
    print("")
    
    # Normalize all files
    results = normalizer.normalize_all_files()
    
    # Validate normalized data
    validation = normalizer.validate_normalized_data()
    
    # Generate report
    report = normalizer.generate_normalization_report(results, validation)
    print("\n" + report)
    
    # Save reports
    output_dir = Path(__file__).parent / "reports"
    output_dir.mkdir(exist_ok=True)
    
    with open(output_dir / "normalization_report.txt", 'w', encoding='utf-8') as f:
        f.write(report)
    
    # Save detailed results
    import json
    with open(output_dir / "normalization_results.json", 'w', encoding='utf-8') as f:
        json.dump({
            'normalization': results,
            'validation': validation,
            'stats': normalizer.stats
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 Reports saved to: {output_dir}")
    
    # Ask about copying to main directory
    normalizer.copy_normalized_to_main()
    
    return results, validation

if __name__ == "__main__":
    main()