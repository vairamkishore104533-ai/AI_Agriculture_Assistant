from app import app
from flask import session

with app.test_client() as c:
    with c.session_transaction() as sess:
        sess['user_id'] = '6a47db6c8a750ffbce798a8c'
        sess['lang'] = 'en'
    
    response = c.get('/fertilizer')
    html = response.get_data(as_text=True)
    
    if "live-crop-chips-container" in html:
        print("SUCCESS: live-crop-chips-container is present!")
    else:
        print("FAILED: live-crop-chips-container is missing!")
        
    if "No live crops available" in html:
        print("INFO: 'No live crops available' was rendered.")
        
    if "Paddy" in html: print("Paddy found in HTML")
    if "Cotton" in html: print("Cotton found in HTML")
    if "Turmeric" in html: print("Turmeric found in HTML")
