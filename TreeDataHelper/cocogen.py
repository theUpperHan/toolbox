import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import threading
import numpy as np
import cv2
import shutil
from PIL import Image
from datetime import datetime
import json
import sys
from tqdm import tqdm


ERRPATH = -1

class EntryWithPlaceholder(tk.Entry):
    def __init__(self, master=None, placeholder="PLACEHOLDER", color='grey'):
        super().__init__(master)

        self.placeholder = placeholder
        self.placeholder_color = color
        self.default_fg_color = self['fg']

        self.bind("<FocusIn>", self.foc_in)
        self.bind("<FocusOut>", self.foc_out)

        self.put_placeholder()

    def put_placeholder(self):
        self.insert(0, self.placeholder)
        self['fg'] = self.placeholder_color

    def foc_in(self, *args):
        if self['fg'] == self.placeholder_color:
            self.delete('0', 'end')
            self['fg'] = self.default_fg_color

    def foc_out(self, *args):
        if not self.get():
            self.put_placeholder()

class CocoGenTool(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Segmentation Tool")
        self.geometry("600x400")

        # Widgets
        self.create_widgets()

        self.ret = 0

        self.segmentation_folder = None
        self.coco_path = None
        self.mask_folder = None
        self.stree_folder = None
        self.total_pixels = 589824

    def create_widgets(self):

        self.path_label = tk.Label(self, text="Segmentation Folder:")
        self.path_label.pack()

        entry_frame = tk.Frame(self)
        entry_frame.pack(pady=10)

        # self.path_entry = tk.Entry(entry_frame, width=50)
        # self.path_entry.pack(side=tk.LEFT)

        entry_frame = tk.Frame(self)
        entry_frame.pack(pady=10)

        # Path entry
        self.path_entry = EntryWithPlaceholder(entry_frame, "Enter path...")
        self.path_entry.pack(side=tk.LEFT)

        # Browse button
        self.browse_button = tk.Button(entry_frame, text="Browse", command=self.browse_folder)
        self.browse_button.pack(side=tk.LEFT, padx=5)

        # Execute button
        self.execute_button = tk.Button(self, text="Execute", command=self.execute_script)
        self.execute_button.pack(pady=10)

        # Stop button
        # self.stop_button = tk.Button(self, text="Stop", command=self.stop_script, state=tk.DISABLED)
        # self.stop_button.pack(pady=10)

        # Progress bar
        self.progress_bar = ttk.Progressbar(self, orient="horizontal", length=300, mode='determinate')
        self.progress_bar.pack(pady=20)

        # Status messages
        self.status_text = tk.Text(self, height=10, state='disabled')
        self.status_text.pack()

    def updateProgress(self, i, total):
        self.progress_bar['value'] = (i + 1) / total * 100
        app.update_idletasks()

    def setFolders(self):
        self.segmentation_folder = self.path_entry.get()
        if not os.path.exists(self.segmentation_folder):
            messagebox.showerror("Error", "Invalid Segmentation path.")
            self.update_status("Error exit: invalid path")
            self.ret = ERRPATH
            return
        self.coco_path = os.path.join(self.segmentation_folder, "coco.json")
        self.mask_folder = os.path.join(self.segmentation_folder, 'NewMasks')
        self.stree_folder = os.path.join(self.segmentation_folder, 'SingleTrees')
        if not os.path.exists(self.stree_folder):
            messagebox.showerror("Error", "SingleTree folder not found")
            self.update_status("Error exit: invalid path")
            self.ret = ERRPATH
            return

    def checkSingleTreeMask(self):
        self.update_status("\Start filtering SingleTree images.")
        all_imgs = os.listdir(self.stree_folder)
        total = len(all_imgs)
        invalid_imgs = {}
        # for i in tqdm(all_imgs, desc="Processing"):
        for i, name in enumerate(all_imgs):
            path = os.path.join(self.stree_folder, name)
            img = np.asarray(cv2.imread(path))

            black_mask = np.all(img == [0, 0, 0], axis=-1)
            percentage = np.sum(black_mask) / self.total_pixels
            if (percentage < 0.2) or (percentage > 0.99):
                invalid_imgs[path] = percentage
                os.remove(path)
            # self.progress_bar['value'] = (i + 1) / total_images * 100
            # app.update_idletasks()
            self.updateProgress(i, total)
        self.update_status("\tFinished filter SingleTree images.")

    def checkNumberAlignment(self):
        def removeImages(folder, invalid_imgs):
            if len(invalid_imgs) == 0:
                self.update_status(f"No invalid images in {folder}")
                return

            total = len(invalid_imgs)
            for i, name in enumerate(invalid_imgs):
                file_path = os.path.join(folder, name)
                if os.path.exists(file_path):
                    os.remove(file_path)
                self.updateProgress(i, total)

        if not os.path.isabs(self.segmentation_folder):
            self.update_status("Argument 'segmentation_folder' has to be an ABSOLUTE path!")
            return


        self.update_status("\Start checking image numbers in folders.")
        image_folder = os.path.join(self.segmentation_folder, 'Images')
        depth_folder = os.path.join(self.segmentation_folder, 'Depth')
        stree_folder = os.path.join(self.segmentation_folder, 'SingleTrees')

        # All element in the format of 1435_Forest_Environment_Set_Map_
        image_files = [i.split('.')[0] for i in os.listdir(image_folder)]
        depth_files = [i.split('.')[0] for i in os.listdir(depth_folder)]
        stree_files = ['_'.join(i.split('_')[:-3]) + '_' for i in os.listdir(stree_folder)]

        # Save the aligned images
        image_set = set(image_files)
        depth_set = set(depth_files)
        stree_set = set(stree_files)
        common_set = image_set & depth_set & stree_set

        # Files that needed to be deleted
        unaligned_image = [i for i in os.listdir(image_folder) if i.split('.')[0] not in common_set]
        unaligned_depth = [i for i in os.listdir(depth_folder) if i.split('.')[0] not in common_set]
        unaligned_stree = [i for i in os.listdir(stree_folder) if '_'.join(i.split('_')[:-3]) + '_' not in common_set]

        # Clean unaligned images
        removeImages(image_folder, unaligned_image)
        removeImages(depth_folder, unaligned_depth)
        removeImages(stree_folder, unaligned_stree)
        self.labels = list(common_set)
        self.update_status("\Finished checking image numbers in folders.")

    def createNewMasks(self):
        def is_not_black(pixel):
            return pixel[:3] != (0, 0, 0)
        
        def combine(img_files, new_mask_dir, label):
            images = [Image.open(path).convert("RGBA") for path in img_files]
            combined_image = Image.new("RGBA", images[0].size, (0, 0, 0, 255))
            combined_pixels = combined_image.load()
            for image in images:
                pixels = image.load()
                for x in range(image.width):
                    for y in range(image.height):
                        if is_not_black(pixels[x, y]):
                            combined_pixels[x, y] = pixels[x, y]
            new_mask = os.path.join(new_mask_dir, label+'.png')
            combined_image.save(new_mask)
            del combined_image
            del images
        
        # Clear previous new mask dir ensure clean
        if os.path.exists(self.mask_folder):
            shutil.rmtree(self.mask_folder)
        os.makedirs(self.mask_folder, exist_ok=True)

        # For each label, find all single tree masks belongs to this frame
        
        total = len(self.labels)
        # for label in tqdm(labels, desc=f"Open Images"):
        for i, name in enumerate(self.labels):
            id = name.split('_')[0]
            img_files = []
            for filename in os.listdir(self.stree_folder):
                if filename.split('_')[0] == id:
                    img_files.append(os.path.join(self.stree_folder, filename))
            
            combine(img_files, self.mask_folder, name)
            self.updateProgress(i, total)

    def createImgList(self):
        images = []
        id_count = 0
        name_id_dict = {}
        
        masks = os.listdir(self.mask_folder)
        total = len(masks)
        for i, name in enumerate(masks):
            image = cv2.imread(os.path.join(self.mask_folder, name))
            height, width = image.shape[:2]
            main_mask_img = {
                "id": id_count,
                "width": width,
                "height": height,
                "file_name": name
            }
            images.append(main_mask_img)
            name_id_dict[name] = id_count
            id_count += 1

            self.updateProgress(i, total)
        return images, name_id_dict

    def createInfo(self, description):
        return {"date_created": datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "description": description}
    
    def organizeMainSepMasks(self, name_id_dict, sep_mask_dir):
        name_sep_dict = {}
        total = len(name_id_dict)
        for i, name in enumerate(name_id_dict):
            name_sep_dict[name] = []
            for sep_mask in os.listdir(sep_mask_dir):
                if sep_mask.startswith(name.split('.')[0]):
                    name_sep_dict[name].append(sep_mask)
            self.updateProgress(i, total)
        return name_sep_dict
    
    

    def createAnnotations(self, name_id_dict, name_sep_dict, sep_mask_dir):

        def filterMask(separated_mask, RGB):
            img = np.array(cv2.imread(separated_mask))
            black_threshold = [5,5,5]
            non_black_mask = np.any(img > black_threshold, axis=-1)
            img[non_black_mask] = RGB
            # cv2.imwrite('Filter.png', img)
            return img
        
        def getSegmentation(img_mask, RGB):
            rgb = np.array(RGB, dtype="uint8")
            object_mask = cv2.inRange(img_mask, rgb, rgb)
            contours = cv2.findContours(object_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_TC89_KCOS)
            contours = contours[0] if len(contours) == 2 else contours[1]

            bbox_list = []
            contour_area = 0
            list_contour = []
            list_poly = []
            for contour in contours:
                bbox_list.append(cv2.boundingRect(contour))
                contour_area += cv2.contourArea(contour)
                contour_pt_list = []
                for i in contour:
                    for j in i:
                        # contour_pt_list.append((int(j[0]), int(j[1])))
                        contour_pt_list.append(int(j[0]))
                        contour_pt_list.append(int(j[1]))

                if contour_pt_list:
                    list_contour.append(contour_pt_list)
            
            if not list_contour:
                # print(f"{img_path} have no trees!")
                return []

            if len(bbox_list) != 1:
                # print(f"{img_path} may contain excessive branch!")
                return []

            if bbox_list and len(bbox_list) == 1:
                bbox_full = (bbox_list[0][0], bbox_list[0][1], bbox_list[0][2], bbox_list[0][3])
                list_poly.append(bbox_full)
                list_poly.append(list_contour)
                list_poly.append(contour_area)

            return list_poly
        
        annotations = []
        print("Start creating annotation list...")
        # for name in tqdm(name_id_dict, desc=f"Creating Annotations"):
        total = len(name_id_dict)
        for i, name in enumerate(name_id_dict):
            for image in name_sep_dict[name]:
                image_path = os.path.join(sep_mask_dir, image)
                RGB = [245,155,66]
                new_mask = filterMask(image_path, RGB)
                
                list_poly = getSegmentation(new_mask, RGB)
                if list_poly == []:
                    continue

                tree_id = image.split('.')[0].split('_')[-1][4:]

                anno = {
                    "id": tree_id,
                    "image_id": name_id_dict[name],
                    "category_id": 0,
                    "bbox": list_poly[0],
                    "segmentation": list_poly[1],
                    "area": list_poly[2],
                    "iscrowd": 0
                }

                annotations.append(anno)
            self.updateProgress(i, total)
                    

        return annotations

    ###############################################################

    def browse_folder(self):
        folder_selected = filedialog.askdirectory()
        self.path_entry.delete(0, tk.END)
        self.path_entry.insert(0, folder_selected)

    def execute_script(self):
        self.script_thread = threading.Thread(target=self.run_script, daemon=True)
        self.script_thread.start()
        

    def run_script(self):
        self.execute_button.config(state=tk.DISABLED)
        self.update_status("Starting coco generation...")
        # Example of how to update the status text
        # You would include real updates throughout your script's execution

        self.setFolders()
        self.checkSingleTreeMask()
        self.checkNumberAlignment()
        self.createNewMasks()
        image_dict, name_id_dict = self.createImgList()
        info_dict = self.createInfo("UE Generated Simulated Data")
        name_sep_dict = self.organizeMainSepMasks(name_id_dict, self.stree_folder)
        annotation_dict = self.createAnnotations(name_id_dict, name_sep_dict, self.stree_folder)
        coco = {
            "info": info_dict,
            "licenses": None,
            "images": image_dict,
            "categories": [{"id": 0, "name": "tree"}],
            "annotations": annotation_dict
        }

        with open(self.coco_path, 'w+') as f:
            json.dump(coco, f)
        
        self.update_status("Finished.")
        self.execute_button.config(state=tk.ACTIVE)
        
    
    def update_status(self, message):
        self.status_text.config(state='normal')
        self.status_text.insert(tk.END, message + "\n")
        self.status_text.see(tk.END)
        self.status_text.config(state='disabled')



if __name__ == "__main__":
    app = CocoGenTool()
    app.mainloop()
