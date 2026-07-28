import requests, re

s = requests.Session()
s.post('http://127.0.0.1:5000/login', json={'username':'admin','password':'admin123'})

r = s.get('http://127.0.0.1:5000/fertilizer')
r2 = s.get('http://127.0.0.1:5000/static/js/fertilizer.js')
c = r2.text

print("=== JS file checks ===")
print(f"File size: {len(c)} bytes")
print(f"loading log: {'fertilizer.js loading' in c}")
print(f"window assignments: {'window.onFertStepClick = onFertStepClick' in c}")
print(f"try-catch fertInit: {'try { fertInit();' in c}")
print(f"try-catch goToFertStep: {'try { goToFertStep(1);' in c}")
print(f"console.log loaded: {'fertilizer.js loaded' in c}")

print("\n=== Step indicator onclick checks ===")
for i in range(1,6):
    pattern = f'id="fert-step-{i}-indicator'
    onclick = f'onclick="onFertStepClick({i})"'
    has_id = pattern in r.text
    has_oc = onclick in r.text
    print(f"Step {i}: id={has_id}, onclick={has_oc}")

print(f"\nStep 1 panel active: {'fert-step-1' in r.text}")
print(f"Script tag present: {'fertilizer.js' in r.text}")

print("\n=== Function definitions in JS ===")
funcs = ['onFertStepClick', 'goToFertStep', 'getFertFirstIncompleteStep', 
         'onFertCropSelect', 'onFertGrowthStageSelect', 'onFertIrrigationSelect',
         'fertBack', 'generateFertilizer', 'saveFertilizer', 'toggleExportMenu',
         'exportCurrentResult', 'viewFertHistory', 'exportFertilizer', 
         'deleteFertilizer', 'closeFertViewModal', 'closeFertMenus',
         'downloadFertFile', 'showFertToast', 'loadFertHistory', 
         'updateFertStats', 'fertInit']
for fn in funcs:
    # Check function definition pattern
    found = f'function {fn}(' in c
    print(f"  {fn}: {'OK' if found else 'MISSING'}")

print("\nDone.")
