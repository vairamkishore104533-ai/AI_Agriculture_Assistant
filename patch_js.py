import re

with open('static/js/fertilizer.js', 'r', encoding='utf-8') as f:
    content = f.read()

# We want to replace filterLiveCropChips and selectLiveCropChip
# Let's find the start of filterLiveCropChips and the end of selectLiveCropChip

start_str = "function filterLiveCropChips(q) {"
end_str = "        showFertToast(cropName + ' not found in fertilizer database', 'error');\n    }\n}"

if start_str in content and end_str in content:
    start_idx = content.find(start_str)
    end_idx = content.find(end_str) + len(end_str)
    
    new_js = """function filterLiveCropChips(q) {
    var lower = q.toLowerCase().trim();
    var select = document.getElementById('native-live-crop-select');
    if (!select) return;
    
    var options = select.options;
    var hasMatch = false;
    for (var i = 1; i < options.length; i++) {
        var opt = options[i];
        var text = opt.text.toLowerCase();
        if (text.indexOf(lower) >= 0) {
            opt.style.display = '';
            opt.hidden = false;
            hasMatch = true;
        } else {
            opt.style.display = 'none';
            opt.hidden = true;
        }
    }
    
    // Automatically select the first visible option if current selection is hidden
    if (select.selectedIndex > 0 && select.options[select.selectedIndex].hidden) {
        select.selectedIndex = 0;
    }
}

function handleNativeLiveCropSelect(selectElement) {
    if (selectElement.selectedIndex <= 0) return;
    
    var opt = selectElement.options[selectElement.selectedIndex];
    var cropName = opt.value;
    var seasonName = opt.getAttribute('data-season') || "";
    
    if (!window.FERT_DATA || !window.FERT_DATA.crops) {
        showFertToast('Fertilizer data not loaded yet', 'error');
        return;
    }
    
    var crops = window.FERT_DATA.crops;
    var foundIndex = -1;
    var searchName = cropName.trim().toLowerCase();
    
    for (var i = 0; i < crops.length; i++) {
        var c = crops[i];
        if ((c.en && c.en.toLowerCase().trim() === searchName) || 
            (c.ta && c.ta.toLowerCase().trim() === searchName)) {
            foundIndex = i;
            break;
        }
    }
    
    // First sync season if available
    if (seasonName) {
        var seasons = window.FERT_DATA.seasons;
        var foundSeasonIndex = -1;
        var sSearch = seasonName.trim().toLowerCase();
        for (var j = 0; j < seasons.length; j++) {
            var s = seasons[j];
            if ((s.en && s.en.toLowerCase().trim() === sSearch) ||
                (s.ta && s.ta.toLowerCase().trim() === sSearch) ||
                (s.id && s.id.toLowerCase().trim() === sSearch)) {
                foundSeasonIndex = j;
                break;
            }
        }
        
        if (foundSeasonIndex >= 0) {
            var sItem = seasons[foundSeasonIndex];
            var seasonInput = document.getElementById('fert-season-input');
            if (seasonInput) {
                var sDisplayText = sItem.ta && getLang() === "ta" ? sItem.ta : (sItem.en || "");
                seasonInput.value = sDisplayText;
                
                // Advance the fertilizer step logically exactly as manual selection does
                seasonInput.focus();
                seasonInput.dispatchEvent(new Event('input'));
                
                var sDropdown = document.querySelector('.fert-search-dropdown[data-portal="season"]');
                if (sDropdown) {
                    var sOpt = sDropdown.querySelector('.fert-search-option[data-index="' + foundSeasonIndex + '"]');
                    if (sOpt) {
                        sOpt.click();
                    }
                }
            }
        }
    }
    
    // Then sync crop
    if (foundIndex >= 0) {
        var item = crops[foundIndex];
        var cropInput = document.getElementById('fert-crop-input');
        if (cropInput) {
            var displayText = item.ta && getLang() === "ta" ? item.ta : (item.en || "");
            cropInput.value = displayText;
            
            // Advance the fertilizer step logically exactly as manual selection does
            cropInput.focus();
            cropInput.dispatchEvent(new Event('input'));
            
            setTimeout(function() {
                var dropdown = document.querySelector('.fert-search-dropdown[data-portal="crop"]');
                if (dropdown) {
                    var optNode = dropdown.querySelector('.fert-search-option[data-index="' + foundIndex + '"]');
                    if (optNode) {
                        optNode.click(); // Triggers the exact same click handler as manual selection
                        showFertToast(cropName + ' selected for fertilizer recommendation', 'success');
                        return;
                    }
                }
                showFertToast('Could not automatically progress the form', 'error');
            }, 50);
        }
    } else {
        showFertToast(cropName + ' not found in fertilizer database', 'error');
    }
}"""
    
    content = content[:start_idx] + new_js + content[end_idx:]
    with open('static/js/fertilizer.js', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Successfully replaced JS in fertilizer.js")
else:
    print("ERROR: Could not find start or end bounds in fertilizer.js")
