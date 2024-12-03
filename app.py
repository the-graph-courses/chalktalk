import os
from shiny import App, render, ui, reactive
import subprocess
import presentation_utils as pu

app_ui = ui.page_fluid(
    ui.tags.head(
        ui.tags.style("""
            .sidebar { background-color: #f8f9fa; padding: 20px; border-radius: 10px; }
            .main-content { padding: 20px; }
            .btn-primary { margin: 10px 0; }
            .form-control { margin: 10px 0; }
            h3, h4 { color: #2c3e50; margin-bottom: 20px; }
        """)
    ),
    ui.layout_sidebar(
        ui.sidebar(
            ui.h3("Chalktalk Demo", class_="text-center"),
            ui.input_text_area(
                "prompt",
                "What would you like me to teach?",
                rows=5,
                placeholder="Enter your topic or learning objectives here...",
                width="100%"
            ),
            ui.input_numeric(
                "num_slides",
                "Number of Slides",
                value=10,
                min=1,
                max=20,
                width="100%"
            ),
            ui.input_action_button(
                "generate_qmd",
                "Generate Presentation",
                class_="btn-primary btn-lg w-100"
            ),
            ui.br(),
            ui.input_action_button(
                "render_presentation",
                "Render Presentation",
                class_="btn-success btn-lg w-100"
            ),
        ),
        ui.div(
            {"class": "main-content"},
            ui.h4("Generated Presentation Content"),
            ui.input_text_area(
                "qmd_editor",
                "",
                rows=20,
                placeholder="Your presentation content will appear here. Feel free to edit before rendering.",
                width="100%"
            ),
            ui.br(),
            ui.output_ui("presentation_link"),
        )
    )
)

def server(input, output, session):
    @reactive.effect
    @reactive.event(input.generate_qmd)
    def _():
        # Generate the QMD content using the prompt
        presentation = pu.generate_slides(
            topic=input.prompt(),
            title=input.prompt(),
            num_slides=input.num_slides(),
            chalktalk_demo=pu.chalktalk_demo,
        )
        content = pu.format_presentation_for_qmd(presentation)
        ui.update_text_area("qmd_editor", value=content)

    presentation_link_rv = reactive.value(None)

    @reactive.effect
    @reactive.event(input.render_presentation)
    def _():
        # Get the edited QMD content
        edited_content = input.qmd_editor()
        # Save the QMD to a temporary file
        with open("temp_presentation.qmd", "w") as f:
            f.write(edited_content)
        # Render the QMD to HTML using quarto CLI
        subprocess.run(["quarto", "render", "temp_presentation.qmd"], check=True)
        
        # Read the HTML content
        with open("temp_presentation.html", "r", encoding="utf-8") as f:
            html_content = f.read()
            
        # Process HTML with voiceover using the functions from presentation_utils.py
        fragments, modified_html = pu.extract_tts_fragments(html_content)
        audio_dir = "audio_output"
        html_dir = os.getcwd()
        processed_fragments = pu.process_fragments_with_azure(fragments, audio_dir, html_dir)
        modified_html = pu.insert_audio_elements(modified_html, processed_fragments)
        final_html = pu.modify_html_for_autoslide_and_controls(modified_html)
        
        # Save the final HTML
        with open("__final_output.html", "w", encoding="utf-8") as f:
            f.write(final_html)
            
        # Update the presentation link
        presentation_link_rv.set(
            ui.tags.a(
                "Download Presentation",
                href="__final_output.html",
                download="presentation.html"
            )
        )

    @render.ui
    def presentation_link():
        return presentation_link_rv()

app = App(app_ui, server)
