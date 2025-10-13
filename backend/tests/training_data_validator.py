"""
Training Data Consistency Validator

This script analyzes CSV training files for inconsistencies in scrubbing patterns
and provides detailed reports on data quality issues that cause over-detection.
"""

import pandas as pd
import re
import os
from typing import Dict, List, Tuple
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrubbers.text_scrubber import TextScrubber

class TrainingDataValidator:
    def __init__(self):
        self.scrubber = TextScrubber()
        self.data_dir = Path(__file__).parent / "data" / "prompts"
        
        # Define what entities SHOULD be scrubbed at each level
        self.level_entities = {
            'C1': [],  # Public data - minimal scrubbing
            'C2': ['PERSON', 'EMAIL_ADDRESS', 'PHONE_NUMBER', 'IBAN_CODE'],
            'C3': ['PERSON', 'EMAIL_ADDRESS', 'PHONE_NUMBER', 'PAYMENT_ID'],  
            'C4': ['PERSON', 'EMAIL_ADDRESS', 'PHONE_NUMBER', 'CVC', 'PIN', 'CREDIT_CARD', 'CVV', 'EXPIRATION_DATE']
        }
        
        self.validation_results = {}

    def extract_entities_from_text(self, text: str) -> List[Dict]:
        """Extract all <TAG> entities from sanitized text"""
        pattern = r'<([^>]+)>'
        matches = re.finditer(pattern, text)
        
        entities = []
        for match in matches:
            entities.append({
                'type': match.group(1),
                'start': match.start(),
                'end': match.end(),
                'text': match.group(0)
            })
        return entities

    def detect_unscrubbed_entities(self, text: str, target_level: str) -> List[Dict]:
        """Find entities that should be scrubbed but aren't"""
        result = self.scrubber.scrub_text(text, target_level)
        detected_entities = result.get('entities', [])
        
        # Filter for entities that should be scrubbed at this level
        required_entities = self.level_entities.get(target_level, [])
        
        unscrubbed = []
        for entity in detected_entities:
            if entity['type'] in required_entities:
                unscrubbed.append({
                    'type': entity['type'],
                    'original': entity['original'],
                    'start': entity['start'],
                    'end': entity['end'],
                    'score': entity['score']
                })
        
        return unscrubbed

    def validate_csv_file(self, csv_path: Path, level: str) -> Dict:
        """Validate a single CSV file for consistency"""
        print(f"\n📊 Analyzing {csv_path.name} (Level {level})...")
        
        try:
            df = pd.read_csv(csv_path)
        except Exception as e:
            return {'error': f"Failed to read CSV: {e}"}
        
        # Determine column names (handle variations)
        prompt_col = None
        sanitized_prompt_col = None
        response_col = None
        sanitized_response_col = None
        
        for col in df.columns:
            col_lower = col.lower()
            if 'prompt' in col_lower and 'sanitized' not in col_lower:
                prompt_col = col
            elif 'prompt' in col_lower and 'sanitized' in col_lower:
                sanitized_prompt_col = col
            elif 'response' in col_lower and 'sanitized' not in col_lower:
                response_col = col
            elif 'response' in col_lower and 'sanitized' in col_lower:
                sanitized_response_col = col
        
        if not all([prompt_col, sanitized_prompt_col]):
            return {'error': f"Required columns not found. Available: {list(df.columns)}"}
        
        issues = []
        total_rows = len(df)
        
        for idx, row in df.iterrows():
            row_issues = []
            
            # Check sanitized prompt consistency
            if pd.notna(row[sanitized_prompt_col]):
                unscrubbed_prompt = self.detect_unscrubbed_entities(row[sanitized_prompt_col], level)
                if unscrubbed_prompt:
                    row_issues.extend([
                        f"Prompt: Unscrubbed {entity['type']}: '{entity['original'][:50]}...'" 
                        for entity in unscrubbed_prompt
                    ])
            
            # Check sanitized response consistency (if available)
            if sanitized_response_col and pd.notna(row[sanitized_response_col]):
                unscrubbed_response = self.detect_unscrubbed_entities(row[sanitized_response_col], level)
                if unscrubbed_response:
                    row_issues.extend([
                        f"Response: Unscrubbed {entity['type']}: '{entity['original'][:50]}...'" 
                        for entity in unscrubbed_response
                    ])
            
            if row_issues:
                issues.append({
                    'row': idx + 1,
                    'issues': row_issues,
                    'prompt_sample': row[prompt_col][:100] + "..." if len(row[prompt_col]) > 100 else row[prompt_col]
                })
        
        # Calculate statistics
        inconsistent_rows = len(issues)
        consistency_rate = ((total_rows - inconsistent_rows) / total_rows) * 100 if total_rows > 0 else 0
        
        return {
            'file': csv_path.name,
            'level': level,
            'total_rows': total_rows,
            'inconsistent_rows': inconsistent_rows,
            'consistency_rate': consistency_rate,
            'issues': issues[:10],  # Show first 10 issues
            'total_issues': sum(len(issue['issues']) for issue in issues)
        }

    def analyze_all_files(self) -> Dict:
        """Analyze all CSV files in the prompts directory"""
        print("🔍 Starting Training Data Consistency Analysis...")
        print("=" * 60)
        
        # Find all CSV files
        csv_files = list(self.data_dir.glob("*.csv"))
        
        # Map files to security levels
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
            results[level] = self.validate_csv_file(csv_file, level)
        
        return results

    def generate_summary_report(self, results: Dict) -> str:
        """Generate a comprehensive summary report"""
        report = []
        report.append("🎯 TRAINING DATA CONSISTENCY ANALYSIS REPORT")
        report.append("=" * 60)
        report.append("")
        
        total_files = len(results)
        total_rows = sum(r.get('total_rows', 0) for r in results.values() if 'error' not in r)
        total_inconsistent = sum(r.get('inconsistent_rows', 0) for r in results.values() if 'error' not in r)
        total_issues = sum(r.get('total_issues', 0) for r in results.values() if 'error' not in r)
        
        overall_consistency = ((total_rows - total_inconsistent) / total_rows * 100) if total_rows > 0 else 0
        
        report.append(f"📈 OVERALL STATISTICS:")
        report.append(f"   • Files Analyzed: {total_files}")
        report.append(f"   • Total Training Rows: {total_rows:,}")
        report.append(f"   • Inconsistent Rows: {total_inconsistent:,}")
        report.append(f"   • Total Issues Found: {total_issues:,}")
        report.append(f"   • Overall Consistency Rate: {overall_consistency:.1f}%")
        report.append("")
        
        # Level-by-level breakdown
        for level in ['C1', 'C2', 'C3', 'C4']:
            if level in results:
                r = results[level]
                if 'error' in r:
                    report.append(f"❌ {level}: ERROR - {r['error']}")
                else:
                    report.append(f"📊 {level} SECURITY LEVEL:")
                    report.append(f"   • File: {r['file']}")
                    report.append(f"   • Total Rows: {r['total_rows']:,}")
                    report.append(f"   • Inconsistent Rows: {r['inconsistent_rows']:,}")
                    report.append(f"   • Consistency Rate: {r['consistency_rate']:.1f}%")
                    report.append(f"   • Total Issues: {r['total_issues']:,}")
                    
                    if r['issues']:
                        report.append(f"   • Sample Issues:")
                        for issue in r['issues'][:3]:  # Show top 3 issues
                            report.append(f"     - Row {issue['row']}: {len(issue['issues'])} issues")
                            for problem in issue['issues'][:2]:  # Show first 2 problems per row
                                report.append(f"       * {problem}")
                    report.append("")
        
        # Recommendations
        report.append("💡 RECOMMENDATIONS:")
        if overall_consistency < 80:
            report.append("   ⚠️  CRITICAL: Data consistency is below 80%")
            report.append("   🔧 URGENT: Run data normalization before model training")
        elif overall_consistency < 90:
            report.append("   ⚠️  WARNING: Data consistency could be improved")
            report.append("   🔧 RECOMMENDED: Run data normalization for better performance")
        else:
            report.append("   ✅ Data consistency is good")
            report.append("   🔧 OPTIONAL: Minor cleanup recommended")
        
        report.append("")
        report.append("🎯 NEXT STEPS:")
        report.append("   1. Run data normalization tool")
        report.append("   2. Re-train custom models with normalized data")
        report.append("   3. Test performance improvements")
        report.append("   4. Update training pipeline for consistency")
        
        return "\n".join(report)

    def save_detailed_report(self, results: Dict, output_path: Path):
        """Save detailed results to JSON file"""
        import json
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"📄 Detailed results saved to: {output_path}")

def main():
    """Main execution function"""
    validator = TrainingDataValidator()
    
    # Analyze all files
    results = validator.analyze_all_files()
    
    # Generate and display summary report
    summary = validator.generate_summary_report(results)
    print(summary)
    
    # Save detailed results
    output_dir = Path(__file__).parent / "reports"
    output_dir.mkdir(exist_ok=True)
    
    validator.save_detailed_report(
        results, 
        output_dir / "training_data_consistency_report.json"
    )
    
    # Save summary report
    with open(output_dir / "training_data_summary.txt", 'w', encoding='utf-8') as f:
        f.write(summary)
    
    print(f"\n📄 Reports saved to: {output_dir}")
    
    return results

if __name__ == "__main__":
    main()