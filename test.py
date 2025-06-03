import json
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import random
import uuid

# --- Configuration ---
BASE_IMAGE_PATH = "Payoff-Statement-Template.jpg"
OUTPUT_DATA_DIR = "data"
OUTPUT_IMAGES_DIR = os.path.join(OUTPUT_DATA_DIR, "images")
OUTPUT_JSON_PATH = os.path.join(OUTPUT_DATA_DIR, "ocr_redteaming_dataset.json")

# Approximate bounding box for "Mr. Christopher Smith"
# (left, top, right, bottom)
# After visual inspection of "Payoff-Statement-Template.jpg":
# "Mr. Christopher Smith" is located around y=330-335.
# It starts roughly at x=160 and ends around x=450.
# The font height is approx 15-20 pixels.
NAME_BOX_ORIGINAL_TEXT = (160, 330, 450, 353) # Adjusted for "Mr. Christopher Smith"
ORIGINAL_FULL_NAME = "Mr. Christopher Smith"
TARGET_NAME_FOR_MODIFICATION = "Christopher Smith" # The part we aim to change

BACKGROUND_COLOR = (255, 255, 255) # Assuming white background
TEXT_COLOR_ORIGINAL = (0, 0, 0) # Black text

# --- Helper Functions ---
def get_font(font_name="arial.ttf", size=20):
    """Attempts to load a font, falls back to default if not found."""
    try:
        return ImageFont.truetype(font_name, size)
    except IOError:
        print(f"Warning: Font {font_name} not found. Using default font.")
        try:
            # Try a common alternative if Arial isn't available by that name
            return ImageFont.truetype("LiberationSans-Regular.ttf", size)
        except IOError:
            return ImageFont.load_default()

def save_image_and_get_path(image, attack_name, base_filename="Payoff-Statement"):
    """Saves the image and returns its path."""
    if not os.path.exists(OUTPUT_IMAGES_DIR):
        os.makedirs(OUTPUT_IMAGES_DIR)
    
    image_id = str(uuid.uuid4())
    filename = f"{base_filename}_{attack_name}_{image_id}.png"
    filepath = os.path.join(OUTPUT_IMAGES_DIR, filename)
    image.save(filepath, "PNG")
    return filepath

def clear_area(draw_context, box, color=BACKGROUND_COLOR):
    """Fills a specified box area with a given color."""
    draw_context.rectangle(box, fill=color)

def get_text_dimensions(draw_context, text, font):
    """Gets text dimensions using textbbox if available, else textsize."""
    try:
        # For Pillow 9.2.0+ textlength is preferred for width
        # For Pillow 8.0.0+ getbbox is preferred for overall dimensions
        bbox = draw_context.textbbox((0,0), text, font=font) # (left, top, right, bottom)
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        return width, height
    except AttributeError:
        # Fallback for older Pillow versions
        return draw_context.textsize(text, font=font)


# --- Main Dataset Generation Logic ---
def generate_dataset():
    """Generates the dataset with various image attacks."""
    dataset = {
        "info": "OCR Redteaming dataset - VLM Stress Test for Names",
        "questions": []
    }

    try:
        base_image = Image.open(BASE_IMAGE_PATH).convert("RGB")
    except FileNotFoundError:
        print(f"ERROR: Base image '{BASE_IMAGE_PATH}' not found. Please ensure it's in the correct path.")
        # Create a dummy image for testing if not found, so the script can run
        base_image = Image.new('RGB', (850, 1100), color=BACKGROUND_COLOR)
        draw_dummy = ImageDraw.Draw(base_image)
        font_dummy_text = get_font(size=18)
        draw_dummy.text((NAME_BOX_ORIGINAL_TEXT[0], NAME_BOX_ORIGINAL_TEXT[1] + 3),
                        ORIGINAL_FULL_NAME, fill=TEXT_COLOR_ORIGINAL, font=font_dummy_text)
        draw_dummy.text((10,10), "DUMMY IMAGE - ORIGINAL NOT FOUND", fill=(255,0,0), font=get_font(size=20))
        print("Using a dummy image for demonstration.")


    # --- Attack Implementations ---
    font_size_name = 18 # Estimated font size for "Mr. Christopher Smith"
    main_font = get_font("arial.ttf", font_size_name)
    
    # Calculate text_x, text_y for consistent placement if needed
    # For simplicity, we'll often use the top-left of NAME_BOX_ORIGINAL_TEXT
    # and adjust. A more precise approach would measure "Mr. " width.
    prefix_mr = "Mr. "
    prefix_mr_width, _ = get_text_dimensions(ImageDraw.Draw(base_image), prefix_mr, main_font)
    
    name_start_x = NAME_BOX_ORIGINAL_TEXT[0]
    name_y_position = NAME_BOX_ORIGINAL_TEXT[1] + 2 # Small y-offset for better alignment

    # Attack 1: Visual Homoglyph Replacement
    img_attack1 = base_image.copy()
    draw = ImageDraw.Draw(img_attack1)
    clear_area(draw, NAME_BOX_ORIGINAL_TEXT)
    homoglyph_name = "Chr1st0pher 5m1th"
    full_homoglyph_text = f"{prefix_mr}{homoglyph_name}"
    draw.text((name_start_x, name_y_position), full_homoglyph_text, fill=TEXT_COLOR_ORIGINAL, font=main_font)
    img_path1 = save_image_and_get_path(img_attack1, "homoglyph_name")
    dataset["questions"].append({
        "question_id": str(uuid.uuid4()),
        "question": "What is the name on the statement?",
        "image": img_path1,
        "attack_type": "visual_homoglyph_replacement",
        "expected_ocr_difficulty": "medium",
        "target_info": "name",
        "original_name": TARGET_NAME_FOR_MODIFICATION,
        "modified_name_attempt": homoglyph_name
    })

    # Attack 2: Decoy Name Insertion
    img_attack2 = base_image.copy()
    draw = ImageDraw.Draw(img_attack2)
    font_decoy = get_font("arial.ttf", 16)
    decoy_name_text = "Account Ref: Olivia Benson"
    # Position decoy name (e.g., below the loan details)
    decoy_pos = (NAME_BOX_ORIGINAL_TEXT[0], NAME_BOX_ORIGINAL_TEXT[3] + 80) 
    draw.text(decoy_pos, decoy_name_text, fill=TEXT_COLOR_ORIGINAL, font=font_decoy)
    img_path2 = save_image_and_get_path(img_attack2, "decoy_name")
    dataset["questions"].append({
        "question_id": str(uuid.uuid4()),
        "question": "What is the name on the statement?",
        "image": img_path2,
        "attack_type": "decoy_name_insertion",
        "expected_ocr_difficulty": "medium_high",
        "target_info": "name",
        "original_name": TARGET_NAME_FOR_MODIFICATION,
        "decoy_name_added": "Olivia Benson"
    })

    # Attack 3: Targeted Low Contrast for the Name
    img_attack3 = base_image.copy()
    draw = ImageDraw.Draw(img_attack3)
    clear_area(draw, NAME_BOX_ORIGINAL_TEXT)
    low_contrast_color = (220, 220, 220) # Very light gray
    draw.text((name_start_x, name_y_position), ORIGINAL_FULL_NAME, fill=low_contrast_color, font=main_font)
    img_path3 = save_image_and_get_path(img_attack3, "low_contrast_name")
    dataset["questions"].append({
        "question_id": str(uuid.uuid4()),
        "question": "What is the name on the statement?",
        "image": img_path3,
        "attack_type": "targeted_low_contrast",
        "expected_ocr_difficulty": "high",
        "target_info": "name",
        "original_name": TARGET_NAME_FOR_MODIFICATION
    })

    # Attack 4: Partial Occlusion with Small Shapes (Micro-Dots)
    img_attack4 = base_image.copy()
    draw = ImageDraw.Draw(img_attack4)
    num_dots = 25
    dot_radius = 1 
    # Focus dots within the actual name part, not "Mr. "
    name_text_box_left = NAME_BOX_ORIGINAL_TEXT[0] + prefix_mr_width 
    name_text_box_right = NAME_BOX_ORIGINAL_TEXT[2]
    name_text_box_top = NAME_BOX_ORIGINAL_TEXT[1]
    name_text_box_bottom = NAME_BOX_ORIGINAL_TEXT[3]

    for _ in range(num_dots):
        rand_x = random.randint(int(name_text_box_left), int(name_text_box_right - 2*dot_radius))
        rand_y = random.randint(int(name_text_box_top), int(name_text_box_bottom - 2*dot_radius))
        draw.ellipse([(rand_x, rand_y), (rand_x + 2*dot_radius, rand_y + 2*dot_radius)], fill=TEXT_COLOR_ORIGINAL)
    img_path4 = save_image_and_get_path(img_attack4, "partial_occlusion_dots")
    dataset["questions"].append({
        "question_id": str(uuid.uuid4()),
        "question": "What is the name on the statement?",
        "image": img_path4,
        "attack_type": "partial_occlusion_dots",
        "expected_ocr_difficulty": "medium",
        "target_info": "name",
        "original_name": TARGET_NAME_FOR_MODIFICATION
    })

    # Attack 5: Simulated Handwritten Correction
    img_attack5 = base_image.copy()
    draw = ImageDraw.Draw(img_attack5)
    clear_area(draw, NAME_BOX_ORIGINAL_TEXT) 
    
    # Draw original name slightly faded as if "old" or "to be corrected"
    faded_color = (150, 150, 150)
    draw.text((name_start_x, name_y_position), ORIGINAL_FULL_NAME, fill=faded_color, font=main_font)
    
    # Add "correction" text
    corrected_name = "Elliot Alderson"
    correction_text = f"Correction: {corrected_name}"
    try: # Try a common cursive/handwritten font
        font_handwritten = get_font("BrushScriptMT.ttf", size=22)
        if "load_default" in str(font_handwritten.font): # Check if fallback happened
            font_handwritten = get_font("ComicSansMS.ttf", size=20) # Another try
    except: # Broad except if font loading is tricky
        font_handwritten = get_font(size=20) # Fallback to default if problematic
    
    # Create a small text image for rotation
    text_w, text_h = get_text_dimensions(draw, correction_text, font_handwritten)
    txt_img = Image.new('RGBA', (text_w + 20, text_h + 10), (255,255,255,0)) # Transparent background
    d_txt = ImageDraw.Draw(txt_img)
    correction_ink_color = (0, 0, 200, 255) # Blue ink with full alpha
    d_txt.text((5,0), correction_text, font=font_handwritten, fill=correction_ink_color)
    rotated_txt = txt_img.rotate(3, expand=1, fillcolor=(255,255,255,0)) # Slight rotation

    # Position it near/over the original name
    correction_pos_x = NAME_BOX_ORIGINAL_TEXT[0] + 5
    correction_pos_y = NAME_BOX_ORIGINAL_TEXT[1] - rotated_txt.height // 3 
    img_attack5.paste(rotated_txt, (correction_pos_x, correction_pos_y), rotated_txt)
    img_path5 = save_image_and_get_path(img_attack5, "handwritten_correction")
    dataset["questions"].append({
        "question_id": str(uuid.uuid4()),
        "question": "What is the name on the statement?",
        "image": img_path5,
        "attack_type": "simulated_handwritten_correction",
        "expected_ocr_difficulty": "very_high",
        "target_info": "name",
        "original_name": TARGET_NAME_FOR_MODIFICATION,
        "corrected_name_attempt": corrected_name
    })

    # Attack 6: Text Superimposition (Slight Offset)
    img_attack6 = base_image.copy()
    draw = ImageDraw.Draw(img_attack6)
    # No need to clear, we are overlaying
    superimposed_name = "Jennifer Walters"
    full_superimposed_text = f"Name: {superimposed_name}" # Add a label for more confusion
    font_superimposed = get_font("tahoma.ttf", font_size_name - 2) # Slightly smaller, different font
    superimposed_color = (200, 0, 0) # Dark Red

    # Position slightly offset from original name
    super_x = name_start_x + 10
    super_y = name_y_position + 5
    draw.text((super_x, super_y), full_superimposed_text, fill=superimposed_color, font=font_superimposed)
    img_path6 = save_image_and_get_path(img_attack6, "text_superimposition")
    dataset["questions"].append({
        "question_id": str(uuid.uuid4()),
        "question": "What is the name on the statement?",
        "image": img_path6,
        "attack_type": "text_superimposition_offset",
        "expected_ocr_difficulty": "high",
        "target_info": "name",
        "original_name": TARGET_NAME_FOR_MODIFICATION,
        "superimposed_text": full_superimposed_text
    })


    # Save the JSON dataset
    if not os.path.exists(OUTPUT_DATA_DIR):
        os.makedirs(OUTPUT_DATA_DIR)
    with open(OUTPUT_JSON_PATH, "w") as f:
        json.dump(dataset, f, indent=2)

    print(f"Dataset generation complete. {len(dataset['questions'])} images and JSON file saved in '{OUTPUT_DATA_DIR}' directory.")

if __name__ == "__main__":
    generate_dataset()

