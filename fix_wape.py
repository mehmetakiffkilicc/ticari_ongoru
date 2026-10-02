import re

path = r"C:\Users\Akif\Documents\ChatGPT\ticari öngörü merkezi\app\forecasting-center.tsx"
with open(path, encoding='utf-8') as f:
    content = f.read()

# Fix the broken ternary: 'row.wape<40' is a string literal, should be row.wape<40
old = "row.wape<20?'Tahmin güvenilir':'row.wape<40'?'Ortalama sapma makul':'Yüksek sapma — dikkatli kullanın'"
new = "row.wape<20?'Tahmin güvenilir':row.wape<40?'Ortalama sapma makul':'Yüksek sapma — dikkatli kullanın'"

if old in content:
    content = content.replace(old, new)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("FIXED: ternary syntax corrected")
else:
    # Show what's around line 217
    lines = content.split('\n')
    for i, line in enumerate(lines[213:220], start=214):
        print(f"{i}: {repr(line[:120])}")
