import re

with open('templates/fertilizer.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the entire #live-crop-chips-container and the search logic if needed
# We want to keep the search bar. 
# Search bar code is:
# <input type="text" id="live-crop-search" placeholder="Search live crops..." oninput="filterLiveCropChips(this.value)" ...>

# We need to replace the live-crop-chips-container with a select

old_chips_block = '''            <div id="live-crop-chips-container" style="display:flex; flex-wrap:wrap; gap:12px; margin-top:15px;">
                {% for c in live_crops %}
                <button type="button" class="live-crop-chip" data-crop="{{ c.crop_name|lower }}" onclick="selectLiveCropChip('{{ c.crop_name|escape }}', '{{ c.season|escape }}', this)" style="padding:8px 16px; border-radius:24px; border:1px solid var(--fert-border, #e2e8f0); background:var(--fert-card-bg, #fff); cursor:pointer; transition:all 0.2s; display:inline-flex; flex-direction:column; align-items:center; min-width:80px; box-shadow:0 1px 2px rgba(0,0,0,0.05);">
                    <span style="font-weight:600; font-size:1em; color:var(--text-color);">🌱 <span class="chip-crop-name">{{ c.crop_name }}</span></span>
                    {% if c.village %}
                    <span style="font-size:0.75em; color:var(--text-muted); margin-top:2px;">{{ c.village }}</span>
                    {% endif %}
                </button>
                {% endfor %}
            </div>'''

new_select_block = '''            <div style="margin-top:15px;">
                <label for="native-live-crop-select" style="display:block; font-size:0.85rem; font-weight:600; color:var(--text-muted); margin-bottom:8px;">
                    {% if lang == 'ta' %}நேரடி பயிரைத் தேர்ந்தெடுக்கவும்{% else %}Select a live crop{% endif %}
                </label>
                <select id="native-live-crop-select" style="width:100%; padding:12px; border-radius:8px; border:1px solid var(--fert-border, #e2e8f0); background:var(--fert-card-bg, #fff); color:var(--text-color); font-size:1rem; cursor:pointer;" onchange="handleNativeLiveCropSelect(this)">
                    <option value="" data-season="">{% if lang == 'ta' %}-- தேர்ந்தெடுக்கவும் --{% else %}-- Select a live crop --{% endif %}</option>
                    {% for c in live_crops %}
                    <option value="{{ c.crop_name|escape }}" data-season="{{ c.season|escape }}">
                        {{ c.crop_name }}{% if c.village %} — {{ c.village }}{% endif %}
                    </option>
                    {% endfor %}
                </select>
            </div>'''

if old_chips_block in content:
    content = content.replace(old_chips_block, new_select_block)
    with open('templates/fertilizer.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Successfully replaced HTML in fertilizer.html")
else:
    print("ERROR: old_chips_block not found in fertilizer.html")
