import django, os, sys
os.environ['DJANGO_SETTINGS_MODULE'] = 'MailSeguridad.settings'
django.setup()

# Test the function directly
from seguridad.table_manager import render_hyperlinks

tests = [
    # (input, expected_substring)
    ('=HYPERLINK("https://outlook.com/msg1", "Ver mensaje")', '<a href="https://outlook.com/msg1" target="_blank" rel="noopener">Ver mensaje</a>'),
    ("=HYPERLINK('https://example.com', 'Click here')", "<a href='https://example.com' target='_blank' rel='noopener'>Click here</a>"),
    ('Texto normal sin hyperlink', 'Texto normal sin hyperlink'),
    ('=HYPERLINK("https://a.com", "A") y =HYPERLINK("https://b.com", "B")', '<a href="https://a.com" target="_blank" rel="noopener">A</a>'),
    ('', ''),
    (None, ''),
]

all_ok = True
for val, expected in tests:
    result = render_hyperlinks(val)
    ok = expected in result
    if not ok:
        print(f'FAIL: {val!r}')
        print(f'  Expected: {expected!r}')
        print(f'  Got:      {result!r}')
        all_ok = False
    else:
        print(f'OK: {val!r}')

# Test in template rendering
from django.template import Template, Context
from seguridad.templatetags.seguridad_extras import render_links

tpl = Template('{% load seguridad_extras %}{{ val|render_links }}')
ctx = Context({'val': '=HYPERLINK("https://test.com", "Click")'})
result = tpl.render(ctx)
expected = '<a href="https://test.com" target="_blank" rel="noopener">Click</a>'
ok = expected in result
print(f'\nTemplate filter OK: {ok}')
if not ok:
    print(f'  Got: {result!r}')

print(f'\nAll tests passed: {all_ok}')
sys.exit(0 if all_ok else 1)
