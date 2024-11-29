#!/usr/bin/env python
# coding: utf-8

# # Generate a slide deck with GPT-4o using the llm demo 

# In[ ]:


import os
from openai import OpenAI

# Initialize the OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

chalktalk_demo = open("assets/chalktalk_demo_for_llm.qmd").read()


def generate_slides(topic: str, title: str, num_slides: int, chalktalk_demo: str):
    prompt = f"""
Please create a presentation titled "{title}" on the topic described below: "{topic}". It should consist of {num_slides} slides.

Each slide should have a title and content formatted as per the following chalktalk demo:

{chalktalk_demo}

Important:
- Note how each bullet point is nested inside its own fragment with its own tts-script.
- When discussing code concepts, include actual code blocks. Each code block is its own fragment with its own tts-script.
- In summary, you have short bullet points or code blocks wrapped in fragments with tts-scripts.

Please provide the output directly in the required format, without any additional explanations or JSON formatting.
"""
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    return completion.choices[0].message.content


def format_presentation_for_qmd(presentation):
    """Assuming presentation.content[0].text contains the markdown content."""
    qmd_content = """---
title: "chalktalk Demo"
format: revealjs
execute:
    echo: true
    eval: false
---

"""
    qmd_content += presentation
    return qmd_content


# ## Example usage
# presentation = generate_slides(
#     topic="Data types in Python",
#     title="Introduction to Python Data Types",
#     num_slides=5,
#     chalktalk_demo=chalktalk_demo,
# )

# # Write presentation to qmd file
# with open("test_presentation.qmd", "w") as f:
#     f.write(format_presentation_for_qmd(presentation))


# # Render qmd to a revealjs presentation

# In[ ]:


# | eval: false
from subprocess import call

# call(["quarto", "render", "test_presentation.qmd"])


# # Voiceover

# In[ ]:


# Voiceover with Parallel Processing

import os
import re
import uuid
import requests
from tempfile import gettempdir
import concurrent.futures

# Define your Azure Speech Service details
my_subscription_key = os.getenv("AZURE_SPEECH_KEY")


def fetch_voiceover_azure(
    script_lines,
    output_dir=gettempdir(),
    subscription_key=my_subscription_key,
    voice="en-US-AndrewMultilingualNeural",
    max_workers=20,
):
    """
    Fetches voiceover audio files from Azure Speech Service for each line in script_lines.
    Uses concurrent processing to speed up the fetch operations.

    Parameters:
    - script_lines (list of str): Lines of text to convert to speech.
    - output_dir (str): Directory to save the audio files.
    - subscription_key (str): Azure subscription key.
    - voice (str): Voice name for Azure TTS.
    - max_workers (int): Maximum number of workers for concurrent processing.

    Returns:
    - list of str: Paths to the generated audio files.
    """
    os.makedirs(output_dir, exist_ok=True)
    file_paths = [None] * len(script_lines)
    ssml_template = """<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" 
        xmlns:mstts="http://www.w3.org/2001/mstts" xml:lang="en-US">
        <voice name="{voice}">{text}</voice>
    </speak>"""

    def fetch_and_save(args):
        idx, line = args
        if not line:
            return idx, None
        sanitized = re.sub(r"[^\w\s]", "", line)[:20].replace(" ", "_")
        file_name = f"{sanitized}_{uuid.uuid4()}.mp3"
        file_path = os.path.join(output_dir, file_name)
        ssml = ssml_template.format(voice=voice, text=line)

        headers = {
            "Content-Type": "application/ssml+xml",
            "X-Microsoft-OutputFormat": "audio-16khz-32kbitrate-mono-mp3",
            "Ocp-Apim-Subscription-Key": subscription_key,
            "User-Agent": "YourUserAgent",
        }

        response = requests.post(
            "https://westus2.tts.speech.microsoft.com/cognitiveservices/v1",
            headers=headers,
            data=ssml.encode("utf-8"),
        )
        response.raise_for_status()

        with open(file_path, "wb") as f:
            f.write(response.content)
        return idx, file_path

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(fetch_and_save, (idx, line))
            for idx, line in enumerate(script_lines)
        ]
        for future in concurrent.futures.as_completed(futures):
            idx, file_path = future.result()
            file_paths[idx] = file_path

    return file_paths


# Example usage:
# if __name__ == "__main__":
#     output_directory = os.path.join(os.getcwd(), "audio_parallel")
#     script_lines = [
#         "This is the script for point one. The hope is for a strong and commanding voice.",
#         "Here is the second line to convert to speech.",
#         "And this is the third line, processed in parallel.",
#     ]
#     audio_files = fetch_voiceover_azure(
#         script_lines,
#         output_dir=output_directory,
#     )
#     print("Generated audio files:", audio_files)


# # Scrape HTML for TTS scripts and add audio elements

# In[ ]:


import os
import re
import uuid
from bs4 import BeautifulSoup


def extract_tts_fragments(html_content):
    """
    Extracts fragments with TTS scripts from an HTML document and ensures uniqueness.

    Parameters:
    - html_content (str): The HTML content to parse.

    Returns:
    - list of tuples: Each tuple contains (script_text, fragment_element, unique_id).
    - str: Modified HTML content with unique IDs added to fragments.
    """
    soup = BeautifulSoup(html_content, "html.parser")
    fragments = soup.find_all("div", class_="fragment", attrs={"data-tts-script": True})

    # Add unique identifiers to each fragment
    results = []
    for idx, fragment in enumerate(fragments):
        script_text = fragment.get("data-tts-script")
        unique_id = f"tts_{idx}_{uuid.uuid4().hex[:8]}"
        fragment["data-tts-id"] = unique_id  # Add unique ID to the fragment
        results.append((script_text, fragment, unique_id))

    # Convert the modified soup back to a string
    modified_html_content = str(soup)
    return results, modified_html_content


# Example usage:
# if __name__ == "__main__":
#     html_example = """
#     <section>
#     <div class="fragment" data-tts-script="Hello world">
#         <p>Hello world</p>
#     </div>
#     </section>
#     <section>
#     <p>Random text outside of fragment</p>
#     <div class="fragment" data-tts-script="Second fragment">
#         <p>Second text</p>
#     </div>
#     </section>
#     """
#     fragments, modified_html = extract_tts_fragments(html_example)
#     print("Extracted fragments and modified HTML:")
#     for frag in fragments:
#         print(f"Script: {frag[0]}, Unique ID: {frag[2]}")


# # Process fragments with Azure and get audio files

# In[ ]:


import os
import concurrent.futures


def process_fragments_with_azure(fragments, output_dir, html_dir, max_workers=20):
    """
    Sends TTS scripts to Azure and returns audio paths along with fragment elements and unique IDs.
    Uses concurrent processing to speed up the operation.

    Parameters:
    - fragments (list of tuples): Output from extract_tts_fragments.
    - output_dir (str): Directory to save the audio files.
    - html_dir (str): Directory where the HTML file will be saved.
    - max_workers (int): Maximum number of workers for concurrent processing.

    Returns:
    - list of tuples: Each tuple contains (absolute_audio_path, relative_audio_path, fragment_element, unique_id).
    """

    def process_fragment(frag_tuple):
        script, fragment, unique_id = frag_tuple
        if script:
            try:
                audio_paths = fetch_voiceover_azure([script], output_dir=output_dir)
                if audio_paths and audio_paths[0]:
                    absolute_audio_path = audio_paths[0]
                    # Calculate relative path from HTML file to audio file
                    relative_audio_path = os.path.relpath(absolute_audio_path, html_dir)
                    return (
                        absolute_audio_path,
                        relative_audio_path,
                        fragment,
                        unique_id,
                    )
            except Exception as e:
                print(f"Error processing fragment {unique_id}: {e}")
        return None

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(process_fragment, frag_tuple) for frag_tuple in fragments
        ]
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result:
                results.append(result)

    return results


# Example usage:
# output_dir = "audio_output_parallel"
# html_dir = os.getcwd()  # Use current directory as html_dir
# os.makedirs(output_dir, exist_ok=True)
# processed_fragments = process_fragments_with_azure(fragments, output_dir, html_dir)
# print("Processed fragments with audio paths:")
# for item in processed_fragments:
#     print(f"Audio Path: {item[0]}, Relative Path: {item[1]}, Unique ID: {item[3]}")


# # Insert audio elements into HTML

# In[ ]:


import os
import librosa
from bs4 import BeautifulSoup


def insert_audio_elements(html_content, processed_fragments):
    """
    Inserts audio elements into the HTML using unique identifiers for precise matching.

    Parameters:
    - html_content (str): The HTML content to modify.
    - processed_fragments (list of tuples): Output from process_fragments_with_azure.

    Returns:
    - str: Modified HTML content with audio elements inserted.
    """
    soup = BeautifulSoup(html_content, "html.parser")

    for (
        absolute_audio_path,
        relative_audio_path,
        fragment_elem,
        unique_id,
    ) in processed_fragments:

        # Find the corresponding fragment using the unique ID
        matching_fragment = soup.find("div", attrs={"data-tts-id": unique_id})

        if matching_fragment:
            # Get actual audio duration using librosa
            if os.path.isfile(absolute_audio_path):
                duration_sec = librosa.get_duration(path=absolute_audio_path)
            else:
                print(f"Audio file not found: {absolute_audio_path}")
                continue
            duration_ms = int(duration_sec * 1000)

            # Set the autoslide attribute
            matching_fragment["data-autoslide"] = str(duration_ms)

            # Create audio element
            audio = soup.new_tag("audio", attrs={"data-autoplay": ""})
            source = soup.new_tag(
                "source", attrs={"src": relative_audio_path, "type": "audio/mpeg"}
            )
            audio.append(source)

            # Add audio element to the fragment
            matching_fragment.append(audio)

            print(
                f"Added audio {relative_audio_path} with duration {duration_ms}ms to fragment ID: {unique_id}"
            )

    return str(soup)


# Example usage:
# if __name__ == "__main__":
#     modified_html_with_audio = insert_audio_elements(modified_html, processed_fragments)
#     print("Modified HTML with audio elements:")
#     print(modified_html_with_audio)


# # Modify html for autoslide and controls

# In[ ]:


from bs4 import BeautifulSoup
import re


def modify_html_for_autoslide_and_controls(html_content):
    """
    Modifies the HTML content to:
    - Set data-autoslide="0" on the first slide.
    - Add a 'Start Presentation' button to the first slide.
    - Ensure subsequent slides auto-advance.
    - Add playback speed and volume control JavaScript code.
    """
    soup = BeautifulSoup(html_content, "html.parser")

    # Add empty fragment to beginning of each section (except the first one)
    sections = soup.find_all("section")
    for i, section in enumerate(sections):
        if i > 0:  # Skip the first section
            # Create empty fragment div with short duration
            empty_fragment = soup.new_tag(
                "div", attrs={"class": "fragment", "data-autoslide": "10"}
            )
            # Insert at the beginning of the section
            section.insert(0, empty_fragment)

    # Step 1: Set data-autoslide for all section tags
    sections = soup.find_all("section")
    for i, section in enumerate(sections):
        if i == 0:
            section["data-autoslide"] = "0"  # First slide
        else:
            section["data-autoslide"] = "100"  # All other slides

    # Step 2: Ensure autoSlide is set globally in Reveal.initialize()
    script_tags = soup.find_all("script")
    for script_tag in script_tags:
        if script_tag.string and "Reveal.initialize" in script_tag.string:
            # Modify 'autoSlide' parameter
            if "autoSlide:" in script_tag.string:
                # Update existing autoSlide value to 100
                new_script_content = re.sub(
                    r"autoSlide:\s*\d+", "autoSlide: 100", script_tag.string
                )
            else:
                # Insert autoSlide: 100 into Reveal.initialize parameters
                new_script_content = script_tag.string.replace(
                    "Reveal.initialize({", "Reveal.initialize({\n    autoSlide: 10,\n"
                )
            script_tag.string.replace_with(new_script_content)
            break  # Assuming there's only one such script

    # Step 3: Add a 'Start Presentation' button to the first slide
    start_button_html = """
        <button id="startPresentationButton"
          style="position: absolute; z-index: 1000; bottom: 20px; left: 50%; transform: translateX(-50%);">
          Start Presentation
        </button>
        """
    # Parse the button HTML and append it to the first slide
    first_section = soup.find("section")
    start_button = BeautifulSoup(start_button_html, "html.parser")
    first_section.append(start_button)

    # Step 4: Add JavaScript to handle 'Start Presentation' button click
    start_script = soup.new_tag("script")
    start_script.string = """
    document.addEventListener("DOMContentLoaded", function () {
      const startButton = document.getElementById("startPresentationButton");

      startButton.addEventListener("click", () => {
        // Advance to the next slide
        Reveal.next();
      });
    });
    """
    # Insert the start script at the end of the body
    body_tag = soup.find("body")
    if body_tag:
        body_tag.append(start_script)

    # Step 5: Add the playback speed and volume control JavaScript code
    playback_script = soup.new_tag("script")
    playback_script.string = """
    // Playback speed feature
    document.addEventListener("DOMContentLoaded", function () {
      const speedButton = document.getElementById("speedButton");
      const playbackRates = [1, 1.5, 2, 0.75];
      let currentRateIndex = 0;

 function applyPlaybackRate() {
  const currentRate = playbackRates[currentRateIndex];

  // Update media playback rates
  document.querySelectorAll("audio, video").forEach(media => {
    media.playbackRate = currentRate;
  });

  // Update slide durations
  document.querySelectorAll(".fragment[data-autoslide]").forEach(fragment => {
    const originalDuration = parseInt(fragment.getAttribute("data-original-autoslide") || fragment.getAttribute("data-autoslide"));
    // Store original duration if not already stored
    if (!fragment.getAttribute("data-original-autoslide")) {
      fragment.setAttribute("data-original-autoslide", originalDuration);
    }
    // Adjust duration based on playback rate
    fragment.setAttribute("data-autoslide", Math.round(originalDuration * (1 / currentRate)));
  });
}

      speedButton.addEventListener("click", () => {
        currentRateIndex = (currentRateIndex + 1) % playbackRates.length;
        speedButton.textContent = playbackRates[currentRateIndex] + "x";
        applyPlaybackRate();
      });

      Reveal.addEventListener('slidechanged', applyPlaybackRate);
      applyPlaybackRate();
    });

    // Volume control feature
    document.addEventListener("DOMContentLoaded", function () {
      const volumeSlider = document.getElementById("volumeSlider");

      function updateVolumes() {
        document.querySelectorAll("audio, video").forEach(media => {
          media.volume = volumeSlider.value;
        });
      }

      volumeSlider.addEventListener("input", updateVolumes);
    });
    """
    # Insert the playback script at the end of the body
    if body_tag:
        body_tag.append(playback_script)

    # Step 6: Add the control buttons to the body
    speed_button_html = """
    <button id="speedButton"
      style="position: fixed; z-index: 1000; bottom: 20px; left: 50%; transform: translateX(-50%); margin-left: 100px;">
      1x
    </button>
    """

    volume_slider_html = """
    <input type="range" id="volumeSlider" min="0" max="1" step="0.01" value="1"
      style="position: fixed; z-index: 1000; bottom: 50px; left: 50%; transform: translateX(-50%); width: 200px;">
    """

    # Parse the buttons into BeautifulSoup elements
    speed_button = BeautifulSoup(speed_button_html, "html.parser")
    volume_slider = BeautifulSoup(volume_slider_html, "html.parser")

    # Append the buttons to the body
    if body_tag:
        body_tag.append(speed_button)
        body_tag.append(volume_slider)

    # Return the modified HTML
    return str(soup)


# Example usage:
# if __name__ == "__main__":
#     final_modified_html = modify_html_for_autoslide_and_controls(modified_html_with_audio)
#     print("Final Modified HTML with autoslide and controls:")
#     print(final_modified_html)


# # Complete workflow starting from a prompt for the AI model
# 

# In[ ]:


def create_presentation_from_prompt(
    prompt: str, title: str = None, name: str = "presentation", num_slides: int = 5
):
    """
    Complete workflow to create a voiced presentation from a prompt.

    Parameters:
    - prompt: str - The topic/description for the presentation
    - title: str - Title of the presentation (default: same as prompt)
    - name: str - Base name to use for generated files (default: "presentation")
    - num_slides: int - Number of slides to generate (default: 5)

    Returns:
    - str: Path to the final HTML presentation with voiceover
    """
    import os
    from pathlib import Path

    # Use prompt as title if none provided
    if title is None:
        title = prompt

    # Step 1: Generate the presentation content
    presentation = generate_slides(
        topic=prompt, title=title, num_slides=num_slides, chalktalk_demo=chalktalk_demo
    )

    # Step 2: Create QMD file
    qmd_content = format_presentation_for_qmd(presentation)
    temp_qmd = f"{name}.qmd"
    with open(temp_qmd, "w") as f:
        f.write(qmd_content)

    # Step 3: Render QMD to HTML
    from subprocess import call

    call(["quarto", "render", temp_qmd])

    # Get the generated HTML file path
    html_file = temp_qmd.replace(".qmd", ".html")

    # Step 4: Process the HTML with voiceover
    input_dir = os.path.dirname(os.path.abspath(html_file))
    output_html = os.path.join(input_dir, f"{name}_voiced.html")

    # Create output directory for audio files
    audio_dir = os.path.join(input_dir, f"audio_{name}")
    os.makedirs(audio_dir, exist_ok=True)

    # Read the original HTML file
    with open(html_file, "r", encoding="utf-8") as f:
        html_content = f.read()

    # Extract fragments with TTS scripts and get modified HTML content
    fragments, modified_html_content = extract_tts_fragments(html_content)
    print(f"Found {len(fragments)} fragments with TTS scripts")

    # Process fragments with Azure and get audio files
    processed_fragments = process_fragments_with_azure(fragments, audio_dir, input_dir)
    print(f"Processed {len(processed_fragments)} audio files")

    # Insert audio elements into the modified HTML content
    modified_html = insert_audio_elements(modified_html_content, processed_fragments)

    # Add playback controls and modify Reveal.initialize
    final_html = modify_html_for_autoslide_and_controls(modified_html)

    # Save the modified HTML
    with open(output_html, "w", encoding="utf-8") as f:
        f.write(final_html)
    print(f"Modified HTML saved to {output_html}")

    # Clean up temporary QMD file
    Path(temp_qmd).unlink()
    Path(html_file).unlink()

    return output_html


# Example usage:
# if __name__ == "__main__":
#     prompt = "Types de données en R Programmation (Make sure your output is in French)"
#     title = "Introduction aux Types de Données en R"
#     final_presentation = create_presentation_from_prompt(
#         prompt=prompt, title=title, name="r_datatypes_fr", num_slides=8
#     )
#     print(f"Final presentation available at: {final_presentation}")

