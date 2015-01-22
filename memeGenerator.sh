#!/bin/dash
# Bild mit Schrift versehen:
# convert TobiWeint.jpg -fill white -stroke black -strokewidth 4 -font Impact -pointsize 100 -draw "text 100,250 'PLEASE'" out.jpg

#oder
# convert -fill white -stroke black -strokewidth 4 -font Impact -pointsize 100 -background none -size 500x caption:"text" text.png
# convert TobiHeult.jpg -draw "image over 600,0 0,0 'text.png'" out.png

convert -gravity center -fill white -stroke black -strokewidth 4 -font Impact -background none -size 500x573 caption:"$1" text.png
convert TobiHeult.jpg -draw "image over 640,0 0,0 'text.png'" -scale 767x382 out.jpg
