
# # Generate a slide deck with GPT-4o using the llm demo  

# %%


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
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )
    return completion.choices[0].message.content


def format_presentation_for_qmd(presentation):
    """Assuming presentation.content[0].text contains the markdown content."""
    qmd_content = """---
title: "chalktalk Demo"
format: 
    revealjs:
        theme: moon
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

# %%


# | eval: false
from subprocess import call

# call(["quarto", "render", "test_presentation.qmd"])

# %%
import datetime
import uuid
import re

def create_presentation_directory(title: str) -> tuple[str, str]:
    """
    Creates a unique directory for a presentation and its media assets.
    
    Args:
        title: The presentation title
        
    Returns:
        tuple: (base_dir, media_dir) paths
    """
    # Sanitize title: remove special chars, replace spaces with underscore
    safe_title = re.sub(r'[^\w\s-]', '', title).strip().lower()
    safe_title = re.sub(r'[-\s]+', '_', safe_title)
    
    # Generate timestamp and UUID
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    unique_id = uuid.uuid4().hex[:8]
    
    # Create directory name
    dir_name = f"{safe_title}_{timestamp}_{unique_id}"
    base_dir = os.path.join("presentations", dir_name)
    media_dir = os.path.join(base_dir, "media")
    
    # Create directory structure
    os.makedirs(os.path.join(media_dir, "audio"), exist_ok=True)
    os.makedirs(os.path.join(media_dir, "video"), exist_ok=True)
    
    return base_dir, media_dir


# # Voiceover

# %%


# Voiceover with Parallel Processing

import os
import re
import uuid
import requests
from tempfile import gettempdir
import concurrent.futures



def fetch_voiceover_azure(
    script_lines,
    output_dir,  # This will now be the media/audio directory
    subscription_key=os.getenv("AZURE_SPEECH_KEY"),
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
        file_path = os.path.join(output_dir, "audio", file_name)  # Updated path
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


# %%
import os
import time
import uuid
import requests
from datetime import datetime

def fetch_avatar_azure(
    script_lines,
    output_dir,  # This will now be the media/video directory
    subscription_key=os.getenv("AZURE_SPEECH_KEY"),
    speech_region="westus2"
):
    """
    Fetches avatar videos from Azure Speech Service for each line in script_lines.
    
    Args:
        script_lines (list): List of text strings to convert to avatar videos
        output_dir (str): Directory to save the video files
        subscription_key (str): Azure subscription key
        speech_region (str): Azure region (e.g., "westus2")
    
    Returns:
        list: Paths to the generated video files
    """
    # Pre-allocate list for paths
    avatar_paths = [None] * len(script_lines)
    
    # Ensure output directory exists
    video_dir = os.path.join(output_dir, "video")
    os.makedirs(video_dir, exist_ok=True)
    
    # Define Azure URL base
    url_base = f"https://{speech_region}.api.cognitive.microsoft.com"
    
    for i, script_line in enumerate(script_lines):
        # Skip empty or None lines
        if not script_line:
            avatar_paths[i] = None
            continue
            
        # Generate a unique job ID
        job_id = f"job-{datetime.now().strftime('%Y%m%d%H%M%S')}-{i}"
        
        # Prepare the payload
        payload = {
            "inputKind": "PlainText",
            "inputs": [
                {"content": script_line}
            ],
            "synthesisConfig": {
                "voice": "en-US-AndrewMultilingualNeural"
            },
            "avatarConfig": {
                "talkingAvatarCharacter": "harry",
                "talkingAvatarStyle": "business",
                "videoFormat": "Mp4",
                "videoCodec": "h264",
                "bitrateKbps": 900,
                "backgroundColor": "#191919FF"
            }
        }

        # Send the request
        headers = {
            "Ocp-Apim-Subscription-Key": subscription_key,
            "Content-Type": "application/json"
        }
        
        response = requests.put(
            f"{url_base}/avatar/batchsyntheses/{job_id}?api-version=2024-08-01",
            headers=headers,
            json=payload
        )
        
        if response.status_code >= 400:
            raise Exception(f"Job submission failed for script line {i}: {response.text}")
        
        print(f"Job submitted successfully for script line {i}. Processing...")
        
        # Poll for job status
        while True:
            time.sleep(1)
            result = requests.get(
                f"{url_base}/avatar/batchsyntheses/{job_id}?api-version=2024-08-01",
                headers={"Ocp-Apim-Subscription-Key": subscription_key}
            )
            
            content = result.json()
            if content["status"] == "Succeeded":
                video_url = content["outputs"]["result"]
                print(f"Ready for script line {i}. Synthesized video: {video_url}")
                break
            elif content["status"] == "Failed":
                raise Exception(f"Synthesis failed for script line {i}: {content}")
            else:
                print(f"Processing script line {i}. Status: {content['status']}")
        
        # Download video
        avatar_path = os.path.join(video_dir, f"{job_id}.mp4")
        video_response = requests.get(video_url)
        with open(avatar_path, "wb") as f:
            f.write(video_response.content)
        
        avatar_paths[i] = avatar_path
    
    return avatar_paths


# %%
# Example usage:
# if __name__ == "__main__":
#     script_lines = [
#         "Welcome to this presentation about artificial intelligence.",
#     ]
    
#     output_directory = os.path.join(os.getcwd(), "avatar_videos")
    
#     video_files = fetch_avatar_azure(
#         script_lines,
#         output_dir=output_directory
#     )
    
#     print("Generated video files:", video_files)


# %%


import os
import re
import uuid
from bs4 import BeautifulSoup


def extract_media_fragments(html_content):
    """
    Extracts fragments with TTS and TTV scripts from an HTML document and ensures uniqueness.

    Parameters:
    - html_content (str): The HTML content to parse.

    Returns:
    - list of tuples: Each tuple contains (script_text, fragment_element, unique_id, media_type).
    - str: Modified HTML content with unique IDs added to fragments.
    """
    soup = BeautifulSoup(html_content, "html.parser")
    fragments = []

    # Find fragments with data-tts
    tts_fragments = soup.find_all("div", class_="fragment", attrs={"data-tts": True})
    for idx, fragment in enumerate(tts_fragments):
        script_text = fragment.get("data-tts")
        unique_id = f"tts_{idx}_{uuid.uuid4().hex[:8]}"
        fragment["data-tts-id"] = unique_id  # Add unique ID to the fragment
        fragments.append((script_text, fragment, unique_id, "tts"))

    # Find fragments with data-ttv
    ttv_fragments = soup.find_all("div", class_="fragment", attrs={"data-ttv": True})
    for idx, fragment in enumerate(ttv_fragments):
        script_text = fragment.get("data-ttv")
        unique_id = f"ttv_{idx}_{uuid.uuid4().hex[:8]}"
        fragment["data-ttv-id"] = unique_id  # Add unique ID to the fragment
        fragments.append((script_text, fragment, unique_id, "ttv"))

    # Convert the modified soup back to a string with proper encoding
    modified_html_content = soup.prettify(formatter="html")
    return fragments, modified_html_content

# Example usage:
# if __name__ == "__main__":
#     html_example = """
#     <section>
#     <div class="fragment" data-tts="Hello world">
#         <p>Hello world</p>
#     </div>
#     <div class="fragment" data-ttv="Video script here">
#         <video src="example.mp4"></video>
#     </div>
#     </section>
#     <section>
#     <p>Random text outside of fragment</p>
#     <div class="fragment" data-tts="Second fragment">
#         <p>Second text</p>
#     </div>
#     </section>
#     """
#     fragments, modified_html = extract_media_fragments(html_example)
#     print("Extracted fragments and modified HTML:")
#     for script, fragment, unique_id, media_type in fragments:
#         print(f"Script: {script}, Type: {media_type}, Unique ID: {unique_id}")


# %%
def process_fragments_with_azure(fragments, output_dir, html_dir, max_workers=20):
    """
    Processes TTS and TTV scripts with Azure and returns media paths along with fragment elements and unique IDs.

    Returns:
    - list of tuples: Each tuple contains (absolute_media_path, relative_media_path, fragment_element, unique_id, media_type).
    """

    def process_fragment(frag_tuple):
        script, fragment, unique_id, media_type = frag_tuple
        if script:
            try:
                if media_type == "tts":
                    media_paths = fetch_voiceover_azure([script], output_dir=output_dir)
                elif media_type == "ttv":
                    media_paths = fetch_avatar_azure([script], output_dir=output_dir)
                else:
                    return None

                if media_paths and media_paths[0]:
                    absolute_media_path = media_paths[0]
                    # Calculate relative path from HTML file to media file
                    relative_media_path = os.path.relpath(absolute_media_path, html_dir)
                    return (
                        absolute_media_path,
                        relative_media_path,
                        fragment,
                        unique_id,
                        media_type,
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

# %%

import moviepy
import os
import librosa
from bs4 import BeautifulSoup

def insert_media_elements(html_content, processed_fragments):
    """
    Inserts audio or video elements into the HTML using unique identifiers for precise matching.

    Returns:
    - str: Modified HTML content with media elements inserted.
    """
    soup = BeautifulSoup(html_content, "html.parser")

    for (
        absolute_media_path,
        relative_media_path,
        fragment_elem,
        unique_id,
        media_type,
    ) in processed_fragments:

        # Find the corresponding fragment using the unique ID
        matching_fragment = soup.find("div", attrs={f"data-{media_type}-id": unique_id})

        if matching_fragment:
            # Get actual media duration
            if os.path.isfile(absolute_media_path):
                if media_type == "tts":
                    duration_sec = librosa.get_duration(path=absolute_media_path)
                elif media_type == "ttv":
                    from moviepy import VideoFileClip
                    try:
                        clip = VideoFileClip(absolute_media_path)
                        duration_sec = clip.duration
                        clip.close()
                    except Exception as e:
                        print(f"Error getting video duration: {e}")
                        continue
            else:
                print(f"Media file not found: {absolute_media_path}")
                continue
            duration_ms = int(duration_sec * 1000)

            # Set the autoslide attribute
            matching_fragment["data-autoslide"] = f"{int(duration_ms)}"

            if media_type == "tts":
                # Create audio element
                media_tag = soup.new_tag("audio", attrs={"data-autoplay": ""})
                source = soup.new_tag(
                    "source", attrs={"src": relative_media_path, "type": "audio/mpeg"}
                )
                media_tag.append(source)
            elif media_type == "ttv":
                # Create video element
                media_tag = soup.new_tag(
                    "video", attrs={"data-autoplay": "", "playsinline": ""})
                source = soup.new_tag(
                    "source", attrs={"src": relative_media_path, "type": "video/mp4"}
                )
                media_tag.append(source)
            else:
                continue

            # Add media element to the fragment
            matching_fragment.append(media_tag)

            print(
                f"Added {media_type} {relative_media_path} with duration {duration_ms}ms to fragment ID: {unique_id}"
            )

    return soup.prettify(formatter="html")

# Example usage:
# if __name__ == "__main__":
#     modified_html_with_media = insert_media_elements(modified_html, processed_fragments)
#     print("Modified HTML with media elements:")
#     print(modified_html_with_media)


# # Modify html for autoslide and controls

# %%


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
    return soup.prettify(formatter="html")


# Example usage:
# if __name__ == "__main__":
#     final_modified_html = modify_html_for_autoslide_and_controls(modified_html_with_audio)
#     print("Final Modified HTML with autoslide and controls:")
#     print(final_modified_html)


# # Complete workflow starting from a prompt for the AI model
# 

# %%

def create_presentation_from_prompt(
    prompt: str, 
    title: str = None, 
    name: str = "presentation", 
    num_slides: int = 5
):
    """
    Complete workflow to create a voiced presentation from a prompt.
    Now uses dedicated directories for each presentation.
    """
    # Use prompt as title if none provided
    if title is None:
        title = prompt[:50]  # Use first 50 chars of prompt as title
        
    # Create unique directory for this presentation
    base_dir, media_dir = create_presentation_directory(title)
    
    # Generate and save QMD
    presentation = generate_slides(
        topic=prompt, 
        title=title, 
        num_slides=num_slides, 
        chalktalk_demo=chalktalk_demo
    )
    
    qmd_content = format_presentation_for_qmd(presentation)
    qmd_file = os.path.join(base_dir, f"{name}.qmd")
    with open(qmd_file, "w") as f:
        f.write(qmd_content)
        
    # Render QMD to HTML
    call(["quarto", "render", qmd_file])
    
    # Process HTML with media
    html_file = qmd_file.replace(".qmd", ".html")
    with open(html_file, "r", encoding="utf-8") as f:
        html_content = f.read()
        
    fragments, modified_html = extract_media_fragments(html_content)
    processed_fragments = process_fragments_with_azure(
        fragments, 
        media_dir, 
        base_dir  # Use base_dir as html_dir for relative paths
    )
    
    modified_html = insert_media_elements(modified_html, processed_fragments)
    final_html = modify_html_for_autoslide_and_controls(modified_html)
    
    # Save final HTML
    output_html = os.path.join(base_dir, f"{name}_final.html")
    with open(output_html, "w", encoding="utf-8") as f:
        f.write(final_html)
        
    return output_html



# %%
# Example usage:
# if __name__ == "__main__":
#     prompt = "Personal Identity Problems (ethics)"
#     title = "Personal Identity Problems (ethics)"
#     final_presentation = create_presentation_from_prompt(
#         prompt=prompt, title=title, name="main_test", num_slides=4
#     )
#     print(f"Final presentation available at: {final_presentation}")
# %%
