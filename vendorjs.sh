#!/bin/bash

# Clear vendor directory
rm -rf static/vendor/

# Emoji Mart
mkdir -p static/vendor/emoji-mart
cp -r node_modules/emoji-mart/dist/browser.js static/vendor/emoji-mart/browser.js

# SortableJS
mkdir -p static/vendor/sortablejs
cp -r node_modules/sortablejs/Sortable.min.js static/vendor/sortablejs/Sortable.min.js

# Flowbite
mkdir -p static/vendor/flowbite
cp -r node_modules/flowbite/dist/flowbite.min.js static/vendor/flowbite/flowbite.min.js
cp -r node_modules/flowbite-datepicker/dist/js/datepicker.min.js static/vendor/flowbite/datepicker.min.js

# HTMX
mkdir -p static/vendor/htmx
cp -r node_modules/htmx.org/dist/htmx.min.js static/vendor/htmx/htmx.min.js

# AlpineJS
mkdir -p static/vendor/alpinejs
cp -r node_modules/alpinejs/dist/cdn.min.js static/vendor/alpinejs/cdn.min.js
