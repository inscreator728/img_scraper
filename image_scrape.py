import requests
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from PIL import Image
import os
import random
import threading
import time
import datetime

class ImageDownloaderApp:
    def __init__(self, root):
        self.root = root
        self.image_urls = []  # Store the scraped image URLs
        self.default_urls = [
            "https://wallpapercave.com/no-copyright-wallpapers",
            "https://wallpapersafari.com/non-copyrighted-wallpapers/",
            "https://wallpapers.com/non-copyrighted-background"
        ]
        self.progress_lock = threading.Lock()
        self.current_progress = 0
        self.total_size = 0
        self.scraping_in_progress = False
        self.start_time = 0
        self.setup_ui()  # Call setup_ui after initializing variables

    def setup_ui(self):
        self.root.title("Image Downloader")
        self.root.geometry("800x600")

        # URL Input Frame
        url_frame = ttk.Frame(self.root)
        url_frame.pack(pady=10, fill='x')

        ttk.Label(url_frame, text="Website URLs (comma separated):").pack(side='left', padx=5)
        self.url_entry = ttk.Entry(url_frame, width=50)
        self.url_entry.pack(side='left', padx=5)
        self.url_entry.insert(0, ",".join(self.default_urls))

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

        # Progress Frame
        progress_frame = ttk.Frame(self.root)
        progress_frame.pack(pady=10)

        # Scraping Progress
        ttk.Label(progress_frame, text="Scraping Progress:").grid(row=0, column=0, padx=5)
        self.scraping_progress = ttk.Progressbar(progress_frame, orient="horizontal", length=200, mode="indeterminate")
        self.scraping_progress.grid(row=0, column=1, padx=5)

        # Estimated Time Label
        self.estimated_time_label = ttk.Label(progress_frame, text="Estimated time: N/A")
        self.estimated_time_label.grid(row=0, column=2, padx=5)

        # Downloading Progress
        ttk.Label(progress_frame, text="Downloading Progress:").grid(row=1, column=0, padx=5)
        self.downloading_progress = ttk.Progressbar(progress_frame, orient="horizontal", length=200, mode="determinate")
        self.downloading_progress.grid(row=1, column=1, padx=5)

        # Log Frame
        log_frame = ttk.Frame(self.root)
        log_frame.pack(fill='both', expand=True, padx=10, pady=5)

        self.log_text = tk.Text(log_frame, height=10, state='disabled')
        self.log_text.pack(side='left', fill='both', expand=True)

        log_scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        log_scrollbar.pack(side='right', fill='y')
        self.log_text.config(yscrollcommand=log_scrollbar.set)

        # Status Bar
        self.status_label = ttk.Label(self.root, text="Ready", relief=tk.SUNKEN, anchor='w')
        self.status_label.pack(fill='x')

    def log_message(self, message):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        full_message = f"[{timestamp}] {message}"
        self.root.after(0, lambda: self._log_message(full_message))

    def _log_message(self, message):
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, message + '\n')
        self.log_text.config(state='disabled')
        self.log_text.see(tk.END)

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
        urls = self.url_entry.get().split(',')
        urls = [url.strip() for url in urls if url.strip()]
        if not urls:
            messagebox.showerror("Invalid URLs", "Please enter at least one valid URL.")
            return
        self.scrape_btn.config(state=tk.DISABLED)
        self.update_status("Scraping images...")
        self.log_message(f"Starting to scrape images from {len(urls)} URLs")
        self.scraping_in_progress = True
        self.update_progress()  # Start periodic UI updates
        threading.Thread(target=self.scrape_multiple_urls, args=(urls,), daemon=True).start()

    def scrape_multiple_urls(self, urls):
        self.image_urls = []
        for url in urls:
            self.scrape_images(url)
        self.root.after(0, self.update_ui_after_scraping)

    def scrape_images(self, url):
        try:
            headers = {
                'User-Agent': random.choice([
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15',
                    'Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.106 Mobile Safari/537.36'
                ])
            }
            response = requests.get(url, headers=headers, timeout=10, stream=True)
            response.raise_for_status()

            total_size = int(response.headers.get('Content-Length', 0))
            self.start_time = time.time()
            if total_size > 0:
                with self.progress_lock:
                    self.total_size = total_size
                    self.current_progress = 0
                self.root.after(0, lambda: self.scraping_progress.config(mode='determinate', maximum=total_size, value=0))
            else:
                self.root.after(0, lambda: self.scraping_progress.config(mode='indeterminate'))
                self.root.after(0, lambda: self.scraping_progress.start())

            content = b''
            for chunk in response.iter_content(chunk_size=8192):
                content += chunk
                if total_size > 0:
                    with self.progress_lock:
                        self.current_progress = len(content)

            soup = BeautifulSoup(content, 'html.parser')
            img_tags = soup.find_all('img')

            for img in img_tags:
                img_url = self.get_image_url(img, url)
                if img_url and self.is_valid_image(img_url):
                    self.image_urls.append(img_url)

            self.root.after(0, lambda: self.log_message(f"Found {len(self.image_urls)} images from {url}"))
        except requests.exceptions.HTTPError as http_err:
            error_msg = f"HTTP error occurred for {url}: {http_err}"
            self.root.after(0, lambda: messagebox.showerror("HTTP Error", error_msg))
            self.root.after(0, lambda: self.log_message(error_msg))
        except Exception as e:
            error_msg = f"Failed to scrape images from {url}: {e}"
            self.root.after(0, lambda: messagebox.showerror("Error", error_msg))
            self.root.after(0, lambda: self.log_message(error_msg))

    def update_progress(self):
        if self.scraping_in_progress:
            with self.progress_lock:
                current = self.current_progress
                total = self.total_size
            if total > 0:
                self.scraping_progress.config(value=current)
                if current > 0:
                    elapsed_time = time.time() - self.start_time
                    estimated_total_time = (elapsed_time / current) * total
                    remaining_time = estimated_total_time - elapsed_time
                    self.estimated_time_label.config(text=f"Estimated time: {remaining_time:.2f} seconds")
            self.root.after(100, self.update_progress)

    def update_ui_after_scraping(self):
        self.listbox.delete(0, tk.END)
        for img_url in self.image_urls:
            self.listbox.insert(tk.END, img_url)
        self.update_status(f"Found {len(self.image_urls)} images.")
        self.scraping_in_progress = False
        self.scrape_btn.config(state=tk.NORMAL)
        self.scraping_progress.stop()
        self.scraping_progress.config(mode='determinate', value=0)
        self.estimated_time_label.config(text="Estimated time: N/A")
        with self.progress_lock:
            self.current_progress = 0
            self.total_size = 0

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
        self.downloading_progress['value'] = 0
        self.downloading_progress['maximum'] = len(selected_indices)
        for index in selected_indices:
            url = self.listbox.get(index)
            threading.Thread(target=self.download_image, args=(url, dest_dir)).start()

    def download_image(self, url, dest_dir):
        try:
            self.root.after(0, lambda: self.log_message(f"Downloading {url}"))
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
                    img = img.resize((img.width * 2, img.height * 2), Image.LANCZOS)
                    img.save(filepath, quality=95)
            except Exception as img_err:
                print(f"Image enhancement failed for {filename}: {img_err}")

            self.root.after(0, lambda: self.log_message(f"Saved to {filepath}"))
            self.root.after(0, lambda: self.update_status(f"Downloaded: {os.path.basename(filepath)}"))
            self.root.after(0, lambda: self.downloading_progress.step(1))
        except Exception as e:
            error_msg = f"Failed to download {url}: {e}"
            self.root.after(0, lambda: self.log_message(error_msg))
            self.root.after(0, lambda: self.update_status(error_msg))

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageDownloaderApp(root)
    root.mainloop()
