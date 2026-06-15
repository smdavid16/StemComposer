import sys
import os
import subprocess
from basic_pitch.inference import predict
import pretty_midi

def main():
    if len(sys.argv) < 4:
        print("Usage: python3 convert_instrument.py <input_audio_path> <instrument_program_number> <output_audio_path>")
        sys.exit(1)
        
    input_path = sys.argv[1]
    program_num = int(sys.argv[2])
    output_path = sys.argv[3]
    
    print(f"Transcribing {input_path} using Basic Pitch...")
    # 1. Run basic-pitch to get midi_data
    try:
        model_output, midi_data, note_events = predict(input_path)
    except Exception as e:
        print(f"Error during transcription: {e}")
        sys.exit(1)
        
    # 2. Change program number for all instruments in midi_data
    print(f"Changing target instrument program to {program_num}...")
    for instrument in midi_data.instruments:
        instrument.program = program_num
        
    # Write temporary MIDI file
    temp_midi_path = output_path + ".mid"
    midi_data.write(temp_midi_path)
    print(f"Saved temporary MIDI to {temp_midi_path}")
    
    # 3. Synthesize to WAV using FluidSynth
    sf2_path = "/usr/share/sounds/sf2/FluidR3_GM.sf2"
    if not os.path.exists(sf2_path):
        print(f"Soundfont not found at {sf2_path}, looking for other soundfonts...")
        sf2_dirs = ["/usr/share/sounds/sf2", "/usr/share/soundfonts"]
        for d in sf2_dirs:
            if os.path.exists(d):
                files = [os.path.join(d, f) for f in os.listdir(d) if f.endswith(".sf2")]
                if files:
                    sf2_path = files[0]
                    break
                    
    print(f"Using SoundFont: {sf2_path}")
    
    # Run fluidsynth
    comanda = [
        "fluidsynth",
        "-ni",
        sf2_path,
        temp_midi_path,
        "-F", output_path,
        "-r", "44100"
    ]
    
    print(f"Running fluidsynth command: {' '.join(comanda)}")
    result = subprocess.run(comanda, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    print(result.stdout)
    
    # Clean up temp midi file
    if os.path.exists(temp_midi_path):
        os.remove(temp_midi_path)
        
    if result.returncode == 0 and os.path.exists(output_path):
        print("Success!")
    else:
        print("Error during FluidSynth synthesis.")
        sys.exit(1)

if __name__ == "__main__":
    main()
