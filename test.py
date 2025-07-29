#!/usr/bin/env python3
"""
Test script for UnrealSpeech TTS integration
"""

import os
import tempfile
import shutil
from pathlib import Path
import presentation_utils as pu

# Set the API key directly for testing
os.environ["UNREAL_SPEECH_API_KEY"] = (
    "OoF31AXoeFF6DxUMIgF2HsF4RXMiW03eViWanPkXQU3AGQUb9yXIsT"
)


def test_unreal_speech_basic():
    """Test basic UnrealSpeech TTS functionality"""
    print("🧪 Testing UnrealSpeech TTS basic functionality...")

    # Create temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"Using temp directory: {temp_dir}")

        # Test script lines
        test_scripts = [
            "Hello world, this is a test of the UnrealSpeech API.",
            "This is the second test sentence to verify concurrent processing.",
            "And this is the third sentence to complete our test.",
        ]

        try:
            # Call the UnrealSpeech function
            audio_files = pu.fetch_voiceover_unreal(
                script_lines=test_scripts,
                output_dir=temp_dir,
                voice="Sierra",
                max_workers=3,
            )

            print(f"✅ Generated {len(audio_files)} audio files:")
            for i, audio_file in enumerate(audio_files):
                if audio_file and os.path.exists(audio_file):
                    file_size = os.path.getsize(audio_file)
                    print(
                        f"  {i+1}. {os.path.basename(audio_file)} ({file_size} bytes)"
                    )
                else:
                    print(f"  {i+1}. Failed to generate audio file")

            # Verify all files were created
            success_count = sum(1 for f in audio_files if f and os.path.exists(f))
            print(
                f"✅ Success rate: {success_count}/{len(test_scripts)} files generated"
            )

            return success_count == len(test_scripts)

        except Exception as e:
            print(f"❌ Error in basic test: {e}")
            return False


def test_unreal_speech_with_presentation_workflow():
    """Test UnrealSpeech with the full presentation workflow"""
    print("\n🧪 Testing UnrealSpeech with presentation workflow...")

    # Create a simple test HTML with TTS fragments
    test_html = """
    <!DOCTYPE html>
    <html>
    <head><title>Test</title></head>
    <body>
        <section>
            <div class="fragment" data-tts="Welcome to our test presentation.">
                <h1>Welcome</h1>
            </div>
            <div class="fragment" data-tts="This slide demonstrates the UnrealSpeech integration.">
                <p>Testing UnrealSpeech</p>
            </div>
        </section>
        <section>
            <div class="fragment" data-tts="Thank you for watching our presentation.">
                <h2>Thank You</h2>
            </div>
        </section>
    </body>
    </html>
    """

    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"Using temp directory: {temp_dir}")

        try:
            # Extract fragments from test HTML
            fragments, modified_html = pu.extract_media_fragments(test_html)
            print(f"✅ Extracted {len(fragments)} fragments")

            # Process fragments with UnrealSpeech
            processed_fragments = pu.process_fragments_with_unreal(
                fragments, temp_dir, temp_dir, max_workers=3
            )

            print(f"✅ Processed {len(processed_fragments)} fragments with media:")
            for (
                abs_path,
                rel_path,
                fragment,
                unique_id,
                media_type,
            ) in processed_fragments:
                if os.path.exists(abs_path):
                    file_size = os.path.getsize(abs_path)
                    print(
                        f"  - {unique_id}: {os.path.basename(abs_path)} ({file_size} bytes)"
                    )
                else:
                    print(f"  - {unique_id}: File not found!")

            # Insert media elements into HTML
            final_html = pu.insert_media_elements(modified_html, processed_fragments)

            # Save final HTML for inspection
            output_file = os.path.join(temp_dir, "test_presentation.html")
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(final_html)

            print(f"✅ Final HTML saved to: {output_file}")
            print(f"✅ File size: {os.path.getsize(output_file)} bytes")

            # Verify all fragments were processed
            success_count = len(processed_fragments)
            expected_count = len(
                [f for f in fragments if f[3] == "tts"]
            )  # Only TTS fragments

            print(
                f"✅ Workflow success rate: {success_count}/{expected_count} TTS fragments processed"
            )

            return success_count == expected_count

        except Exception as e:
            print(f"❌ Error in workflow test: {e}")
            import traceback

            traceback.print_exc()
            return False


def test_different_voices():
    """Test different UnrealSpeech voices"""
    print("\n🧪 Testing different UnrealSpeech voices...")

    voices_to_test = ["Sierra", "Noah", "Ivy", "Caleb", "Emily"]
    test_text = "This is a test of the selected voice."

    with tempfile.TemporaryDirectory() as temp_dir:
        success_count = 0

        for voice in voices_to_test:
            try:
                print(f"Testing voice: {voice}")
                audio_files = pu.fetch_voiceover_unreal(
                    script_lines=[test_text],
                    output_dir=temp_dir,
                    voice=voice,
                    max_workers=1,
                )

                if audio_files[0] and os.path.exists(audio_files[0]):
                    file_size = os.path.getsize(audio_files[0])
                    print(
                        f"  ✅ {voice}: {os.path.basename(audio_files[0])} ({file_size} bytes)"
                    )
                    success_count += 1
                else:
                    print(f"  ❌ {voice}: Failed to generate audio")

            except Exception as e:
                print(f"  ❌ {voice}: Error - {e}")

        print(
            f"✅ Voice test success rate: {success_count}/{len(voices_to_test)} voices"
        )
        return success_count > 0


def main():
    """Run all tests"""
    print("🚀 Starting UnrealSpeech TTS Integration Tests\n")

    # Check API key
    api_key = os.getenv("UNREAL_SPEECH_API_KEY")
    if not api_key:
        print("❌ UNREAL_SPEECH_API_KEY environment variable not set!")
        return False
    else:
        print(f"✅ API Key set: {api_key[:8]}...{api_key[-8:]}")

    # Run tests
    tests = [
        ("Basic TTS Test", test_unreal_speech_basic),
        ("Presentation Workflow Test", test_unreal_speech_with_presentation_workflow),
        ("Different Voices Test", test_different_voices),
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"Running: {test_name}")
        print("=" * 50)

        try:
            result = test_func()
            results.append((test_name, result))
            if result:
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} CRASHED: {e}")
            results.append((test_name, False))

    # Summary
    print(f"\n{'='*50}")
    print("TEST SUMMARY")
    print("=" * 50)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")

    print(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! UnrealSpeech integration is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the output above for details.")
        return False


if __name__ == "__main__":
    main()
