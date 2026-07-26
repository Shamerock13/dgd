from pathlib import Path

path = Path('tools/apply_brand_profiles.py')
text = path.read_text(encoding='utf-8')
text = text.replace(
    "'''  BadgeEuro, Clock3, UserRound, Layers3, Info, ImageOff, ExternalLink\\n''',\n'''  BadgeEuro, Clock3, UserRound, Layers3, Info, ImageOff, ExternalLink, MapPin, CalendarDays, ShieldCheck\\n''')",
    "'''  BadgeEuro, Clock3, UserRound, Layers3, Info, ImageIcon, ExternalLink\\n''',\n'''  BadgeEuro, Clock3, UserRound, Layers3, Info, ImageIcon, ExternalLink, MapPin, CalendarDays\\n''')",
)
path.write_text(text, encoding='utf-8')
