# In-Browser Slide Demo

This folder contains a standalone HTML page for creating and presenting slides with
GrapesJS, Reveal.js and PptxGenJS. A small GSAP animation is also included for
slide transitions.

## Usage

1. Start a simple web server in this directory:
   ```bash
   python3 -m http.server 8000
   ```
   Then open `http://localhost:8000/main.html` in your browser.

2. **LLM HTML Input** – Paste raw HTML for each slide and click **Process Slides**.

3. **Edit Slides** – Switch to the second tab to tweak the layout using GrapesJS.
   After editing, press **Save Edits**.

4. **Present** – Use the third tab to run the slideshow. Each slide fades in with
   a GSAP animation. Use the **Start Presentation** button for fullscreen mode.

5. **Export PPT** – The last tab converts your slides to a PowerPoint file using
   PptxGenJS.

This page does not require any backend; all processing happens in your browser.
