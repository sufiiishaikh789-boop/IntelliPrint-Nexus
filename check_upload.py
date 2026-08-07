"""Diagnostic script to check the upload page's data dependencies."""
from smartdb.crud import get_all_printers

printers = get_all_printers()
print(f"Printers in DB: {len(printers)}")
for p in printers:
    print(f"  id={p.get('id')} name={p.get('name')} status={p.get('status')} ppm={p.get('ppm')} toner={p.get('toner_level')}")

print()

# Test predict_wait_time
from smartai.wait_time import predict_wait_time
result = predict_wait_time(queue_length=2, pages=5, copies=1, printer_speed_ppm=30, priority_flag=False)
print(f"wait_time result: {result}")

# Test recommend_printers
from smartai.recommendation import recommend_printers
rec = recommend_printers(
    job_pages=5,
    job_copies=1,
    color_required=False,
    available_printers=[p for p in printers if p.get('status') == 'Online'],
)
print(f"recommend_printers result: {rec}")
