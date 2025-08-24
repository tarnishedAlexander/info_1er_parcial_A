# Puedes reemplazar este archivo con un ícono real si lo deseas.
# Este es un placeholder temporal para el botón de recarga.
from PIL import Image, ImageDraw

size = (64, 64)
img = Image.new('RGBA', size, (0, 0, 0, 0))
draw = ImageDraw.Draw(img)
# Dibuja un círculo
bbox = [8, 8, 56, 56]
draw.arc(bbox, start=30, end=330, fill=(255, 215, 0, 255), width=8)
# Dibuja una flecha
arrow = [(48, 16), (56, 8), (56, 24)]
draw.polygon(arrow, fill=(255, 215, 0, 255))
img.save('assets/img/reload.png')
