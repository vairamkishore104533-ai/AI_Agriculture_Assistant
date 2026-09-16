with open('routes/fertilizer.py', 'r', encoding='utf-8') as f:
    content = f.read()

target = '    print(f"DEBUG_FERT: user_id={user_id}, crops_db={len(crops_db)}, live_crops={len(live_crops)}", flush=True)\n'
content = content.replace(target, '')

with open('routes/fertilizer.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Removed debug print')
