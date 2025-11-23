"""
Batch Processing Utility Module for ADK Sequential Agent Pipeline
Provides utilities for processing multiple products and managing results
"""

import json
import asyncio
import csv
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from main import ProductExtractionPipeline


class BatchProcessor:
    """
    High-level batch processing orchestrator for the ADK extraction pipeline.
    Handles multiple products, result aggregation, and export formats.
    """

    def __init__(self, output_dir: str = "output"):
        """
        Initialize the batch processor
        
        Args:
            output_dir: Directory to save results
        """
        self.pipeline = ProductExtractionPipeline()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.processing_log = []

    def process_directory(self, base_folder: str) -> List[Dict[str, Any]]:
        """
        Process all products in a directory
        
        Args:
            base_folder: Path to folder containing product subfolders
            
        Returns:
            List of product profiles with extracted attributes
        """
        print(f"\n{'='*80}")
        print(f"[BATCH PROCESSOR] Starting directory processing")
        print(f"[BATCH PROCESSOR] Base folder: {base_folder}")
        print(f"{'='*80}\n")
        
        results = self.pipeline.process_batch(base_folder)
        
        return results

    def export_results_to_json(
        self,
        results: List[Dict[str, Any]],
        filename: Optional[str] = None
    ) -> str:
        """
        Export results to JSON file
        
        Args:
            results: List of product profiles
            filename: Optional custom filename (default: extraction_results_<timestamp>.json)
            
        Returns:
            Path to the saved file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"extraction_results_{timestamp}.json"
        
        output_path = self.output_dir / filename
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"[EXPORT] Results saved to JSON: {output_path}")
        return str(output_path)

    def export_results_to_csv(
        self,
        results: List[Dict[str, Any]],
        filename: Optional[str] = None
    ) -> str:
        """
        Export results to CSV file
        
        Args:
            results: List of product profiles
            filename: Optional custom filename (default: extraction_results_<timestamp>.csv)
            
        Returns:
            Path to the saved file
        """
        if not results:
            print("[WARNING] No results to export")
            return ""
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"extraction_results_{timestamp}.csv"
        
        output_path = self.output_dir / filename
        
        # Collect all unique attribute keys
        all_attributes = set()
        for prod in results:
            if "attributes" in prod and isinstance(prod["attributes"], dict):
                all_attributes.update(prod["attributes"].keys())
        
        attribute_list = sorted(list(all_attributes))
        
        # Write CSV
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            headers = ["Product Name", "Description", "Images Processed", "Status"] + attribute_list
            writer = csv.writer(f)
            writer.writerow(headers)
            
            for prod in results:
                row = [
                    prod.get("product_name", ""),
                    prod.get("product_description", ""),
                    str(prod.get("image_count", "")),
                    "Success" if prod.get("error") is None else "Failed"
                ]
                
                # Add attributes
                attrs = prod.get("attributes", {})
                for attr in attribute_list:
                    row.append(attrs.get(attr, ""))
                
                writer.writerow(row)
        
        print(f"[EXPORT] Results saved to CSV: {output_path}")
        return str(output_path)

    def generate_summary_report(
        self,
        results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive summary report
        
        Args:
            results: List of product profiles
            
        Returns:
            Dictionary containing summary statistics
        """
        successful = [r for r in results if r.get("error") is None]
        failed = [r for r in results if r.get("error") is not None]
        
        # Attribute completion statistics
        attribute_stats = {}
        for prod in successful:
            attrs = prod.get("attributes", {})
            for attr_name, attr_value in attrs.items():
                if attr_name not in attribute_stats:
                    attribute_stats[attr_name] = {"filled": 0, "total": 0}
                attribute_stats[attr_name]["total"] += 1
                if attr_value:
                    attribute_stats[attr_name]["filled"] += 1
        
        # Calculate completion rates
        attribute_completion = {}
        for attr_name, stats in attribute_stats.items():
            if stats["total"] > 0:
                attribute_completion[attr_name] = {
                    "completion_rate": f"{(stats['filled'] / stats['total'] * 100):.1f}%",
                    "filled": stats["filled"],
                    "total": stats["total"]
                }
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_products": len(results),
            "successful": len(successful),
            "failed": len(failed),
            "success_rate": f"{(len(successful) / len(results) * 100):.1f}%" if results else "N/A",
            "total_images_processed": sum(r.get("image_count", 0) for r in successful),
            "average_images_per_product": (
                f"{sum(r.get('image_count', 0) for r in successful) / len(successful):.1f}"
                if successful else "N/A"
            ),
            "attribute_completion_rates": attribute_completion,
            "failed_products": [
                {"product_name": r.get("product_name"), "error": r.get("error")}
                for r in failed
            ]
        }
        
        return report

    def save_report(
        self,
        report: Dict[str, Any],
        filename: Optional[str] = None
    ) -> str:
        """
        Save summary report to JSON file
        
        Args:
            report: Report dictionary
            filename: Optional custom filename
            
        Returns:
            Path to the saved file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"summary_report_{timestamp}.json"
        
        output_path = self.output_dir / filename
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"[REPORT] Summary report saved to: {output_path}")
        return str(output_path)

    def print_report(self, report: Dict[str, Any]) -> None:
        """Pretty print the summary report"""
        print(f"\n{'='*80}")
        print("BATCH PROCESSING SUMMARY REPORT")
        print(f"{'='*80}")
        print(f"Timestamp: {report.get('timestamp', 'N/A')}")
        print(f"\n{'─'*80}")
        print("STATISTICS")
        print(f"{'─'*80}")
        print(f"Total Products Processed: {report.get('total_products', 0)}")
        print(f"Successful: {report.get('successful', 0)}")
        print(f"Failed: {report.get('failed', 0)}")
        print(f"Success Rate: {report.get('success_rate', 'N/A')}")
        print(f"\nTotal Images Processed: {report.get('total_images_processed', 0)}")
        print(f"Avg Images per Product: {report.get('average_images_per_product', 'N/A')}")
        
        print(f"\n{'─'*80}")
        print("ATTRIBUTE COMPLETION RATES")
        print(f"{'─'*80}")
        attr_completion = report.get("attribute_completion_rates", {})
        for attr, stats in sorted(attr_completion.items()):
            print(f"  {attr:30s}: {stats['completion_rate']:>6s} ({stats['filled']}/{stats['total']})")
        
        if report.get("failed_products"):
            print(f"\n{'─'*80}")
            print("FAILED PRODUCTS")
            print(f"{'─'*80}")
            for failed in report.get("failed_products", []):
                print(f"  {failed.get('product_name', 'Unknown')}: {failed.get('error', 'Unknown error')}")
        
        print(f"\n{'='*80}\n")


def process_and_export(
    base_folder: str,
    output_dir: str = "output",
    export_json: bool = True,
    export_csv: bool = True,
    save_report: bool = True
) -> Dict[str, str]:
    """
    High-level function to process a directory and export results
    
    Args:
        base_folder: Path to folder containing product subfolders
        output_dir: Directory for output files
        export_json: Whether to export JSON results
        export_csv: Whether to export CSV results
        save_report: Whether to generate and save report
        
    Returns:
        Dictionary with paths to all generated files
    """
    processor = BatchProcessor(output_dir=output_dir)
    
    # Process products
    results = processor.process_directory(base_folder)
    
    output_files = {}
    
    # Export results
    if export_json:
        output_files["json"] = processor.export_results_to_json(results)
    
    if export_csv:
        output_files["csv"] = processor.export_results_to_csv(results)
    
    # Generate and save report
    if save_report:
        report = processor.generate_summary_report(results)
        processor.print_report(report)
        output_files["report"] = processor.save_report(report)
    else:
        report = processor.generate_summary_report(results)
        processor.print_report(report)
    
    return output_files


# ============================================================================
# CLI Entry Point
# ============================================================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python batch_processor.py <base_folder> [output_dir]")
        print("\nExample:")
        print("  python batch_processor.py './raw_images' './output'")
        sys.exit(1)
    
    base_folder = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "output"
    
    # Run processing
    output_files = process_and_export(
        base_folder=base_folder,
        output_dir=output_dir,
        export_json=True,
        export_csv=True,
        save_report=True
    )
    
    print("\n[SUCCESS] All files exported:")
    for file_type, file_path in output_files.items():
        print(f"  {file_type.upper()}: {file_path}")
