import re

with open('templates/fertilizer.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace opening tag
content = content.replace(
    '<div class="live-crop-chip"',
    '<button type="button" class="live-crop-chip"'
)

# We need to replace the specific closing </div> for live-crop-chip.
# The structure is:
# <button type="button" class="live-crop-chip" ...>
#    <span ...>...</span>
#    {% if c.village %}
#    <span ...>...</span>
#    {% endif %}
# </div>
# We can just replace:
#                     {% endif %}
#                 </div>
# with:
#                     {% endif %}
#                 </button>

content = content.replace(
    '                    {% endif %}\n                </div>\n                {% endfor %}',
    '                    {% endif %}\n                </button>\n                {% endfor %}'
)

with open('templates/fertilizer.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("Replaced div with button")
