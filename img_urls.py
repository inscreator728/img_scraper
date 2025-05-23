import requests
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from PIL import Image, ImageTk
from io import BytesIO
import os

class ImageDownloaderApp:
    def __init__(self, root):
        self.root = root
        self.setup_ui()
        self.image_urls = []  # Store the scraped image URLs

    def setup_ui(self):
        self.root.title("Image Downloader")
        self.root.geometry("800x600")

        # URL Input Frame
        url_frame = ttk.Frame(self.root)
        url_frame.pack(pady=10, fill='x')

        ttk.Label(url_frame, text="Website URL:").pack(side='left', padx=5)
        self.url_entry = ttk.Entry(url_frame, width=50)
        self.url_entry.pack(side='left', padx=5)

        self.scrape_btn = ttk.Button(url_frame, text="Find Images", command=self.start_scraping)
        self.scrape_btn.pack(side='left', padx=5)

        # Image List Frame
        list_frame = ttk.Frame(self.root)
        list_frame.pack(fill='both', expand=True, padx=10, pady=5)

        self.listbox = tk.Listbox(list_frame, selectmode=tk.EXTENDED, height=20)
        self.listbox.pack(side='left', fill='both', expand=True)

        scrollbar = ttk.Scrollbar(list_frame, command=self.listbox.yview)
        scrollbar.pack(side='right', fill='y')
        self.listbox.config(yscrollcommand=scrollbar.set)

        # Control Buttons Frame
        control_frame = ttk.Frame(self.root)
        control_frame.pack(fill='x', pady=10)

        ttk.Button(control_frame, text="Select All", command=self.select_all).pack(side='left', padx=5)
        ttk.Button(control_frame, text="Deselect All", command=self.deselect_all).pack(side='left', padx=5)

        self.dest_entry = ttk.Entry(control_frame, width=40)
        self.dest_entry.pack(side='left', padx=5)
        self.dest_entry.insert(0, os.getcwd())

        ttk.Button(control_frame, text="Browse", command=self.browse_directory).pack(side='left', padx=5)
        ttk.Button(control_frame, text="Download Selected", command=self.download_selected_images).pack(side='right', padx=5)

        # Progress Bar
        self.progress = ttk.Progressbar(self.root, orient="horizontal", length=400, mode="determinate")
        self.progress.pack(pady=10)

        # Status Bar
        self.status_label = ttk.Label(self.root, text="Ready", relief=tk.SUNKEN, anchor='w')
        self.status_label.pack(fill='x')

    def update_status(self, message):
        self.status_label.config(text=message)

    def browse_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.dest_entry.delete(0, tk.END)
            self.dest_entry.insert(0, directory)

    def select_all(self):
        self.listbox.select_set(0, tk.END)

    def deselect_all(self):
        self.listbox.select_clear(0, tk.END)

    def start_scraping(self):
        url = self.url_entry.get()
        if not url.startswith(('http://', 'https://')):
            messagebox.showerror("Invalid URL", "Please enter a valid URL (starting with http:// or https://).")
            return

        self.scrape_btn.config(state=tk.DISABLED)
        self.update_status("Scraping images...")
        self.root.after(100, self.scrape_images, url)

    def scrape_images(self, url):
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            img_tags = soup.find_all('img')

            self.image_urls = []
            for img in img_tags:
                img_url = self.get_image_url(img, url)
                if img_url and self.is_valid_image(img_url):
                    self.image_urls.append(img_url)

            self.listbox.delete(0, tk.END)
            for img_url in self.image_urls:
                self.listbox.insert(tk.END, img_url)

            self.update_status(f"Found {len(self.image_urls)} images.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to scrape images: {e}")
        finally:
            self.scrape_btn.config(state=tk.NORMAL)

    def get_image_url(self, img_tag, base_url):
        for attr in ['src', 'data-src', 'data-original']:
            if img_tag.get(attr):
                return urljoin(base_url, img_tag[attr])
        return None

    def is_valid_image(self, url):
        return url.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp'))

    def download_selected_images(self):
        selected_indices = self.listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("No Selection", "Please select at least one image to download.")
            return

        dest_dir = self.dest_entry.get()
        if not os.path.isdir(dest_dir):
            messagebox.showerror("Invalid Directory", "Please select a valid download directory.")
            return

        self.progress['value'] = 0
        self.progress['maximum'] = len(selected_indices)

        for index in selected_indices:
            url = self.listbox.get(index)
            self.root.after(100, self.download_image, url, dest_dir)

    def download_image(self, url, dest_dir):
        try:
            response = requests.get(url, stream=True, timeout=10)
            response.raise_for_status()

            filename = os.path.basename(urlparse(url).path) or "image.jpg"
            filepath = os.path.join(dest_dir, filename)

            counter = 1
            while os.path.exists(filepath):
                name, ext = os.path.splitext(filename)
                filepath = os.path.join(dest_dir, f"{name}_{counter}{ext}")
                counter += 1

            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)

            # Enhance image quality
            try:
                with Image.open(filepath) as img:
                    img = img.convert("RGB")
                    img = img.resize((img.width * 2, img.height * 2), Image.ANTIALIAS)
                    img.save(filepath, quality=95)
            except Exception as img_err:
                print(f"Image enhancement failed for {filename}: {img_err}")

            self.update_status(f"Downloaded: {filename}")
        except Exception as e:
            self.update_status(f"Failed to download {url}: {e}")
        finally:
            self.progress['value'] += 1

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageDownloaderApp(root)
    root.mainloop()
