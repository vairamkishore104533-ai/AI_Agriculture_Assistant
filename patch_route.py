import sys
with open('routes/fertilizer.py', 'r', encoding='utf-8') as f:
    content = f.read()

target = 'live_crops = [c.to_dict() for c in crops_db if c.status.lower() not in ["harvested", "cancelled", "completed"]]'
replacement = '''live_crops = [c.to_dict() for c in crops_db if c.status.lower() not in ["harvested", "cancelled", "completed"]]
    print(f"DEBUG_FERT: user_id={user_id}, crops_db={len(crops_db)}, live_crops={len(live_crops)}", flush=True)'''

content = content.replace(target, replacement)
with open('routes/fertilizer.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Patched route with print')
