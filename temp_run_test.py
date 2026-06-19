from pathlib import Path
p = Path('app.py')
text = p.read_text(encoding='utf-8')
print('LENGTH', len(text))
print('HAS HEADER', '# Header' in text)
