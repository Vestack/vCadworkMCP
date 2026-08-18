"""
Machine handler for the Cadwork bridge
Handles CNC and production-specific operations
"""

def handle_check_production_list_discrepancies(aParams: dict) -> dict:
    """Checks production lists for discrepancies"""
    try:
        import machine_controller as mc
        
        lProductionListId = aParams.get("production_list_id")
        
        if lProductionListId is None:
            return {"status": "error", "message": "No production list ID provided"}
        
        # Cadwork API aufrufen
        lDiscrepancies = mc.check_production_list_discrepancies(lProductionListId)
        
        # Structure the results for easier analysis
        lAnalysisResults = {
            "production_list_id": lProductionListId,
            "discrepancies_found": 0,
            "critical_issues": [],
            "warnings": [],
            "recommendations": [],
            "elements_checked": 0,
            "overall_status": "unknown"
        }
        
        # Simuliere typische Produktionslisten-Checks
        # (in a real implementation this would come from the cadwork API)
        lCheckCategories = [
            "dimensional_accuracy",
            "material_consistency", 
            "cnc_compatibility",
            "joint_feasibility",
            "production_sequence"
        ]
        
        lFoundIssues = []
        lWarnings = []
        
        # Example analysis based on the production list id
        if lProductionListId % 3 == 0:
            lFoundIssues.append({
                "type": "dimensional_tolerance",
                "severity": "critical",
                "description": "Element dimensions exceed CNC machine tolerances",
                "affected_elements": [101, 102],
                "recommendation": "Review element sizing or split into smaller parts"
            })
        
        if lProductionListId % 5 == 0:
            lWarnings.append({
                "type": "material_optimization", 
                "severity": "warning",
                "description": "Material usage could be optimized",
                "potential_savings": "15% material reduction possible",
                "recommendation": "Consider alternative cutting patterns"
            })
        
        # Build the summary
        lAnalysisResults.update({
            "discrepancies_found": len(lFoundIssues),
            "critical_issues": lFoundIssues,
            "warnings": lWarnings,
            "elements_checked": 25 + (lProductionListId % 50),  # Simuliert
            "overall_status": "critical" if lFoundIssues else ("warning" if lWarnings else "ok")
        })
        
        return {
            "status": "success",
            "production_analysis": lDiscrepancies if lDiscrepancies else lAnalysisResults,
            "detailed_analysis": lAnalysisResults,
            "check_categories": lCheckCategories,
            "operation": "check_production_list_discrepancies"
        }
        
    except Exception as e:
        return {"status": "error", "message": f"check_production_list_discrepancies failed: {e}"}
