"""Migration validation script to compare old vs new evaluation outputs.

This script helps validate that the migration from ml-infra/evals to AI Evolution
produces equivalent results by comparing CSV outputs from both systems.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any

try:
    from ai_evolution.sdk.ml_infra import compare_csv_results
except ImportError:
    print("Error: ai_evolution package not found. Install with: pip install -e .")
    sys.exit(1)


def validate_migration(
    old_csv_path: Path,
    new_csv_path: Path,
    tolerance: float = 0.01,
    output_report: Path | None = None,
    verbose: bool = False,
) -> dict[str, Any]:
    """
    Validate migration by comparing old and new CSV outputs.
    
    Args:
        old_csv_path: Path to old ml-infra/evals CSV output
        new_csv_path: Path to new AI Evolution CSV output
        tolerance: Tolerance for score differences (default: 0.01)
        output_report: Optional path to save detailed report JSON
        verbose: Print detailed comparison information
    
    Returns:
        Dictionary with validation results
    """
    old_csv_path = Path(old_csv_path)
    new_csv_path = Path(new_csv_path)
    
    if not old_csv_path.exists():
        raise FileNotFoundError(f"Old CSV file not found: {old_csv_path}")
    if not new_csv_path.exists():
        raise FileNotFoundError(f"New CSV file not found: {new_csv_path}")
    
    print(f"Comparing outputs...")
    print(f"  Old: {old_csv_path}")
    print(f"  New: {new_csv_path}")
    print(f"  Tolerance: {tolerance}")
    print()
    
    # Run comparison
    comparison = compare_csv_results(
        csv1_path=old_csv_path,
        csv2_path=new_csv_path,
        tolerance=tolerance,
    )
    
    # Print summary
    print("=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)
    print(f"Old CSV rows:        {comparison['csv1_rows']}")
    print(f"New CSV rows:        {comparison['csv2_rows']}")
    print(f"Common test IDs:     {comparison.get('common_test_ids', 'N/A')}")
    print(f"Score matches:       {comparison['matches']}")
    print(f"Score differences:   {comparison['differences']}")
    print()
    
    # Check for structural differences
    if comparison['csv1_rows'] != comparison['csv2_rows']:
        print("⚠️  WARNING: Row count mismatch!")
        print(f"   Old has {comparison['csv1_rows']} rows, new has {comparison['csv2_rows']} rows")
        print()
    
    # Check for missing test IDs
    if comparison.get('missing_in_csv2'):
        print(f"⚠️  WARNING: {len(comparison['missing_in_csv2'])} test IDs missing in new CSV:")
        for test_id in comparison['missing_in_csv2'][:10]:  # Show first 10
            print(f"   - {test_id}")
        if len(comparison['missing_in_csv2']) > 10:
            print(f"   ... and {len(comparison['missing_in_csv2']) - 10} more")
        print()
    
    if comparison.get('missing_in_csv1'):
        print(f"⚠️  WARNING: {len(comparison['missing_in_csv1'])} test IDs missing in old CSV:")
        for test_id in comparison['missing_in_csv1'][:10]:  # Show first 10
            print(f"   - {test_id}")
        if len(comparison['missing_in_csv1']) > 10:
            print(f"   ... and {len(comparison['missing_in_csv1']) - 10} more")
        print()
    
    # Check for column differences
    old_cols = set(comparison['csv1_columns'])
    new_cols = set(comparison['csv2_columns'])
    missing_cols = old_cols - new_cols
    extra_cols = new_cols - old_cols
    
    if missing_cols:
        print(f"⚠️  WARNING: {len(missing_cols)} columns missing in new CSV:")
        for col in sorted(missing_cols):
            print(f"   - {col}")
        print()
    
    if extra_cols:
        print(f"ℹ️  INFO: {len(extra_cols)} extra columns in new CSV:")
        for col in sorted(extra_cols):
            print(f"   - {col}")
        print()
    
    # Show score differences
    if comparison['score_differences']:
        print(f"⚠️  WARNING: {len(comparison['score_differences'])} score differences found:")
        print()
        
        # Group by test_id for better readability
        differences_by_test: dict[str, list[dict[str, Any]]] = {}
        for diff in comparison['score_differences']:
            test_id = diff['test_id']
            if test_id not in differences_by_test:
                differences_by_test[test_id] = []
            differences_by_test[test_id].append(diff)
        
        # Show first 10 test IDs with differences
        shown = 0
        for test_id, diffs in list(differences_by_test.items())[:10]:
            print(f"  Test ID: {test_id}")
            for diff in diffs:
                col = diff['column']
                old_val = diff['csv1']
                new_val = diff['csv2']
                diff_val = diff.get('difference', abs(float(old_val) - float(new_val)))
                print(f"    {col}: {old_val} → {new_val} (diff: {diff_val:.4f})")
            print()
            shown += 1
        
        if len(differences_by_test) > 10:
            print(f"  ... and {len(differences_by_test) - 10} more test IDs with differences")
            print()
    
    # Calculate pass/fail
    total_comparisons = comparison['matches'] + comparison['differences']
    if total_comparisons == 0:
        print("❌ VALIDATION FAILED: No comparisons could be made")
        validation_passed = False
    elif comparison['differences'] == 0:
        print("✅ VALIDATION PASSED: All scores match within tolerance")
        validation_passed = True
    else:
        match_rate = comparison['matches'] / total_comparisons if total_comparisons > 0 else 0
        print(f"⚠️  VALIDATION PARTIAL: {match_rate * 100:.1f}% matches ({comparison['matches']}/{total_comparisons})")
        validation_passed = match_rate >= 0.95  # Pass if 95%+ match
    
    # Add validation status to comparison
    comparison['validation_passed'] = validation_passed
    comparison['match_rate'] = comparison['matches'] / total_comparisons if total_comparisons > 0 else 0
    
    # Save detailed report if requested
    if output_report:
        output_report = Path(output_report)
        output_report.parent.mkdir(parents=True, exist_ok=True)
        with output_report.open('w', encoding='utf-8') as f:
            json.dump(comparison, f, indent=2, default=str)
        print(f"\nDetailed report saved to: {output_report}")
    
    if verbose:
        print("\n" + "=" * 70)
        print("DETAILED COMPARISON")
        print("=" * 70)
        print(json.dumps(comparison, indent=2, default=str))
    
    return comparison


def main():
    parser = argparse.ArgumentParser(
        description="Validate migration by comparing old vs new CSV outputs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic comparison
  python migrations/ml_infra_evals/validate_migration.py \\
    --old-csv ml-infra/evals/results.csv \\
    --new-csv ai-evolution/results.csv
  
  # With custom tolerance and report
  python migrations/ml_infra_evals/validate_migration.py \\
    --old-csv ml-infra/evals/results.csv \\
    --new-csv ai-evolution/results.csv \\
    --tolerance 0.001 \\
    --output-report validation_report.json \\
    --verbose
        """,
    )
    parser.add_argument(
        "--old-csv",
        required=True,
        help="Path to old ml-infra/evals CSV output",
    )
    parser.add_argument(
        "--new-csv",
        required=True,
        help="Path to new AI Evolution CSV output",
    )
    parser.add_argument(
        "--tolerance",
        type=float,
        default=0.01,
        help="Tolerance for score differences (default: 0.01)",
    )
    parser.add_argument(
        "--output-report",
        help="Optional path to save detailed JSON report",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print detailed comparison information",
    )
    
    args = parser.parse_args()
    
    try:
        result = validate_migration(
            old_csv_path=Path(args.old_csv),
            new_csv_path=Path(args.new_csv),
            tolerance=args.tolerance,
            output_report=Path(args.output_report) if args.output_report else None,
            verbose=args.verbose,
        )
        
        # Exit with appropriate code
        sys.exit(0 if result['validation_passed'] else 1)
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
