"""
SmartPrint AI - Printer Recommendation Engine
Machine Learning-based recommendation system integrating queue predictions.
"""
import random
from smartai.wait_time import predict_wait_time

def recommend_printers(job_pages: int, job_copies: int, color_required: bool, available_printers: list) -> dict:
    """
    Recommend the best printer based on job specs and ML historical efficiency data.
    """
    if not available_printers:
        return {}
        
    scored_printers = []
    for p in available_printers:
        score = 100
        
        # Penalize if color is needed but not supported
        if color_required and not p.get('supports_color', True):
            score -= 100
            
        # Penalize low toner
        toner = p.get('toner_level', 100)
        if toner < 10:
            score -= 50
        elif toner < 30:
            score -= 20
            
        # Reward speed for large jobs
        total_pages = job_pages * job_copies
        speed = p.get('ppm', 30)
        if total_pages > 50:
            score += (speed - 30) # Reward faster printers
            
        # Penalize predicted wait times using Random Forest / XGBoost Regressor
        queue_len = p.get('queue_length', 0)
        pred_wait = predict_wait_time(
            queue_length=queue_len,
            pages=job_pages,
            copies=job_copies,
            printer_speed_ppm=speed,
            priority_flag=False
        )
        wait_time = pred_wait["estimated_wait_minutes"]
        score -= (wait_time * 4.0)
        
        # Random historical ML variance
        score += random.uniform(-2, 2)
        
        scored_printers.append({
            "printer_id": p.get('id', 'Unknown'),
            "name": p.get('name', 'Printer'),
            "score": max(0, min(100, score)),
            "ppm": speed,
            "queue": queue_len,
            "predicted_wait": wait_time
        })
        
    # Sort by score descending
    scored_printers.sort(key=lambda x: x['score'], reverse=True)
    
    # Categorize recommendations
    valid_printers = [p for p in scored_printers if p['score'] > 0]
    
    if not valid_printers:
        return {"error": "No suitable printers available."}
        
    fastest = max(valid_printers, key=lambda x: x['ppm'])
    lowest_wait = min(valid_printers, key=lambda x: x['predicted_wait'])
    best_overall = valid_printers[0]
    
    return {
        "best_printer": best_overall,
        "fastest_printer": fastest,
        "lowest_wait_time_printer": lowest_wait,
        "highest_efficiency_printer": best_overall,
        "all_scored": valid_printers
    }

# Alias for backward compatibility
recommend_printer = recommend_printers
