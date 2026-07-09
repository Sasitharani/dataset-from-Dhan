# Find the line with: if i + 1 < len(candles):
# Replace ALL instances with: if i > 0:
# And change: next_c = candles[i + 1]
# To: next_c = candles[i - 1]

import re

file_path = '/workspaces/dataset-from-Dhan/pages/5_Automatic_LIC_Bot.py'

with open(file_path, 'r') as f:
    content = f.read()

# Replace the logic
content = content.replace(
    'if i + 1 < len(candles):',
    'if i > 0:'
)

content = content.replace(
    'next_c = candles[i + 1]',
    'next_c = candles[i - 1]'
)

with open(file_path, 'w') as f:
    f.write(content)

print("✅ Fixed: Now checking previous candle (next in time)!")

