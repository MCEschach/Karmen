#!/bin/dash
# Bild mit Schrift versehen:
# convert TobiWeint.jpg -fill white -stroke black -strokewidth 4 -font Impact -pointsize 100 -draw "text 100,250 'PLEASE'" out.jpg

#oder
# convert -fill white -stroke black -strokewidth 4 -font Impact -pointsize 100 -background none -size 500x caption:"text" text.png
# convert TobiHeult.jpg -draw "image over 600,0 0,0 'text.png'" out.png

convert -gravity center -fill white -stroke black -strokewidth 4 -font Impact -background none -size 2000x400 caption:"$1" text.png
convert -gravity center -fill white -stroke black -strokewidth 4 -font Impact -background none -size 2000x400 caption:"$2" text2.png
convert JanSchweinemann.png -draw "image over 80,20 0,0 'text.png'" -draw "image over 80,3300 0,0 'text2.png'" out.jpg
convert out.jpg -resize "432x768" out.jpg
