#!/bin/bash
# Bild mit Schrift versehen:
# convert TobiWeint.jpg -fill white -stroke black -strokewidth 4 -font Impact -pointsize 100 -draw "text 100,250 'PLEASE'" out.jpg

#oder
# convert -fill white -stroke black -strokewidth 4 -font Impact -pointsize 100 -background none -size 500x caption:"text" text.png
# convert TobiHeult.jpg -draw "image over 600,0 0,0 'text.png'" out.png

convert -gravity center -fill white -stroke black -strokewidth 4 -font Impact -background none -size 500x150 caption:"$1" text.png
convert -gravity center -fill white -stroke black -strokewidth 4 -font Impact -background none -size 500x150 caption:"$2" text2.png
convert MaggiNavigiert.jpg -draw "image over 10,10 0,0 'text.png'" -draw "image over 10,400 0,0 'text2.png'" out.jpg
