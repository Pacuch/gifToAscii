import os
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image
import io
from ascii_magic import AsciiArt


def progress_bar(iterable, prefix='', length=30):
    total = len(iterable)
    prefix = prefix.ljust(len(prefix) + 1)

    def show_progress():
        percent = 100 * (index + 1) // total
        bar = '█' * int(length * (index + 1) // total)
        progress = f'{bar.ljust(length)} {percent}%'
        print(f'\r{prefix} {progress}', end='', flush=True)

    for index, item in enumerate(iterable):
        show_progress()
        yield item
    show_progress()
    print()


def save_gif_frames(gif_file_path, output_folder):
    gif = Image.open(gif_file_path)
    total_digits = len(str(gif.n_frames - 1))

    for frame_number in progress_bar(range(gif.n_frames), prefix='Saving Frames from GIF:'):
        gif.seek(frame_number)
        frame_image = gif.copy()
        frame_name = f"frame_{frame_number:0{total_digits}d}.png"
        output_path = os.path.join(output_folder, frame_name)
        frame_image.save(output_path, format="PNG")


def generate_ascii_art(file):
    my_art = AsciiArt.from_image(file)
    my_art.to_html_file(f'htmls/{file.stem}.html', columns=200, width_ratio=2, full_color=True)


def html_to_gif(html_folder_path, output_gif):
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--window-size=1920x1080')
    driver = webdriver.Chrome(options=chrome_options)

    screenshots = []
    for html_file in progress_bar(html_folder_path, prefix='Generating output GIF:'):
        driver.get(f'file://{os.path.abspath(html_file)}')
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'pre')))

        pre_element = driver.find_element(By.TAG_NAME, 'pre')
        screenshot = driver.get_screenshot_as_png()

        location = pre_element.location
        size = pre_element.size
        left = location['x']
        top = location['y']
        right = left + size['width']
        bottom = top + size['height']

        element_screenshot = Image.open(io.BytesIO(screenshot)).crop((left, top, right, bottom))
        screenshots.append(element_screenshot)

    screenshots[0].save(output_gif, save_all=True, append_images=screenshots[1:], duration=100, loop=0)
    print(f'\nGIF Saved as {output_gif}')
    driver.quit()


def create_dir_if_doesnt_exist(dir):
    if not os.path.exists(dir):
        os.makedirs(dir)


def delete_files_in_folder(dir):
    # Check if the folder exists
    if not os.path.exists(dir):
        return

    # Get a list of all files in the folder
    files = os.listdir(dir)

    # Iterate over each file and delete it
    for file_name in files:
        file_path = os.path.join(dir, file_name)

        try:
            # Check if it's a file (not a subdirectory)
            if os.path.isfile(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"Error deleting {file_path}: {e}")


if __name__ == "__main__":
    output_frames_folder = 'out_frames'
    html_frames_folder = 'htmls'
    inputs_folder = 'inputs'
    outputs_folder = 'outputs'

    gif_path = 'piła.gif'
    output = f'output_{gif_path}'

    create_dir_if_doesnt_exist(output_frames_folder)
    create_dir_if_doesnt_exist(html_frames_folder)
    create_dir_if_doesnt_exist(inputs_folder)
    create_dir_if_doesnt_exist(outputs_folder)

    delete_files_in_folder(output_frames_folder)
    delete_files_in_folder(html_frames_folder)

    save_gif_frames(gif_path, output_frames_folder)

    png_files = [Path(output_frames_folder) / file for file in os.listdir(output_frames_folder) if file.endswith('.png')]
    for png in progress_bar(png_files, prefix='Converting each frame to HTML:'):
        generate_ascii_art(png)

    html_files = [Path(html_frames_folder) / file for file in os.listdir(html_frames_folder) if file.endswith('.html')]
    html_to_gif(html_files, output)
