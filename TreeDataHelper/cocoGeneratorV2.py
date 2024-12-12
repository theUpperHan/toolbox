import os
import numpy as np
import cv2
from tqdm import tqdm
import shutil
from PIL import Image
from datetime import datetime
import json
import sys

class AnsiColors:
    RED = '\033[91m'
    ENDC = '\033[0m'





SEGMENTATION_FOLDER = ''
if len(sys.argv) > 1:
    in_path = sys.argv[1]
    print(f"Path provided: {in_path}")
    if os.path.exists(in_path):
        SEGMENTATION_FOLDER = in_path
    else:
        print(f"{AnsiColors.RED}Invalid path.")
        exit()
else:
    print(f"{AnsiColors.RED}Please provide a path as an argument.")
    exit()

COCO_PATH = os.path.join(SEGMENTATION_FOLDER, "coco.json")
MASK_FOLDER = os.path.join(SEGMENTATION_FOLDER, 'NewMasks')

STREE_FOLDER = os.path.join(SEGMENTATION_FOLDER, 'SingleTrees')
if not os.path.exists(STREE_FOLDER):
    print(f"{AnsiColors.RED}Unable to locate SingleTrees folder")
    exit()


def checkSingleTreeMask(maskfolder, TOTAL_PIXELS=589824):
    print("Checking invalid SINGLE Tree Mask images...")

    all_imgs = os.listdir(maskfolder)
    invalid_imgs = {}
    for i in tqdm(all_imgs, desc="Processing"):
    # for i in all_imgs:
        path = os.path.join(maskfolder, i)
        img = np.asarray(cv2.imread(path))

        black_mask = np.all(img == [0, 0, 0], axis=-1)
        percentage = np.sum(black_mask) / TOTAL_PIXELS
        if (percentage < 0.2) or (percentage > 0.99):
            invalid_imgs[path] = percentage
            os.remove(path)
    print(f"{len(invalid_imgs)} images removed")
    

def checkFolders(segmentation_folder):
    folders = os.listdir(segmentation_folder)
    required_folders = ['Depth', 'Images', 'Masks', 'SingleTrees']
    if not all(folder in folders for folder in required_folders):
        print('Missing folder')
        return False
    else:
        print('Folders are complete')
        return True

def removeImages(folder, invalid_imgs):
    if len(invalid_imgs) == 0:
        print(f"No invalid images in {folder}")
        return

    for i in tqdm(invalid_imgs, desc=f"Deleting invalid images in {folder}"):
        file_path = os.path.join(folder, i)
        if os.path.exists(file_path):
            os.remove(file_path)

def checkNumberAlignment(segmentation_folder):
    # Assume segmentation_folder is an absolute folder
    if not os.path.isabs(segmentation_folder):
        print("Argument 'segmentation_folder' has to be an ABSOLUTE path!")
        return None

    image_folder = os.path.join(segmentation_folder, 'Images')
    depth_folder = os.path.join(segmentation_folder, 'Depth')
    stree_folder = os.path.join(segmentation_folder, 'SingleTrees')

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
    return list(common_set)

# labels is the image/frame names
def createNewMasks(parent_dir, labels):
    def is_not_black(pixel):
        return pixel[:3] != (0, 0, 0)
    
    def combine(img_files, new_mask_dir):
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

    stree_dir = os.path.join(parent_dir, "SingleTrees")
    new_mask_dir = os.path.join(parent_dir, "NewMasks")

    # Clear previous new mask dir ensure clean
    if os.path.exists(new_mask_dir):
        shutil.rmtree(new_mask_dir)
    os.makedirs(new_mask_dir, exist_ok=True)

    # For each label, find all single tree masks belongs to this frame
    for label in tqdm(labels, desc=f"Open Images"):
        id = label.split('_')[0]
        img_files = []
        for filename in os.listdir(stree_dir):
            if filename.split('_')[0] == id:
                img_files.append(os.path.join(stree_dir, filename))

        combine(img_files, new_mask_dir)


def createImgList(main_mask_dir):
    images = []
    id_count = 0
    name_id_dict = {}
    for i in os.listdir(main_mask_dir):
        image = cv2.imread(os.path.join(main_mask_dir, i))
        height, width = image.shape[:2]
        main_mask_img = {
            "id": id_count,
            "width": width,
            "height": height,
            "file_name": i
        }
        images.append(main_mask_img)
        name_id_dict[i] = id_count
        id_count += 1

    return images, name_id_dict

def organizeMainSepMasks(name_id_dict, sep_mask_dir):
    name_sep_dict = {}
    for name in name_id_dict:
        name_sep_dict[name] = []
        for sep_mask in os.listdir(sep_mask_dir):
            if sep_mask.startswith(name.split('.')[0]):
                name_sep_dict[name].append(sep_mask)
    return name_sep_dict

def organizeMainSepMasks(name_id_dict, sep_mask_dir):
    name_sep_dict = {}
    for name in name_id_dict:
        name_sep_dict[name] = []
        for sep_mask in os.listdir(sep_mask_dir):
            if sep_mask.startswith(name.split('.')[0]):
                name_sep_dict[name].append(sep_mask)
    return name_sep_dict

def filterMask(separated_mask, RGB):
    img = np.array(cv2.imread(separated_mask))
    black_threshold = [5,5,5]
    non_black_mask = np.any(img > black_threshold, axis=-1)
    img[non_black_mask] = RGB
    # cv2.imwrite('Filter.png', img)
    return img

def getSegmentation(img_mask, RGB, img_path):
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

def createAnnotations(name_id_dict, name_sep_dict, sep_mask_dir):
    annotations = []

    print("Start creating annotation list...")
    for name in tqdm(name_id_dict, desc=f"Creating Annotations"):
        for image in name_sep_dict[name]:
            image_path = os.path.join(sep_mask_dir, image)
            RGB = [245,155,66]
            new_mask = filterMask(image_path, RGB)
            
            list_poly = getSegmentation(new_mask, RGB, image_path)
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
                

    return annotations

def createInfo(description):
    return {"date_created": datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "description": description}


checkFolders(SEGMENTATION_FOLDER)
checkSingleTreeMask(STREE_FOLDER)
labels = checkNumberAlignment(SEGMENTATION_FOLDER)
createNewMasks(SEGMENTATION_FOLDER, labels)

image_dict, name_id_dict = createImgList(MASK_FOLDER)
info_dict = createInfo("UE Generated Simulated Data")
name_sep_dict = organizeMainSepMasks(name_id_dict, STREE_FOLDER)
annotation_dict = createAnnotations(name_id_dict, name_sep_dict, STREE_FOLDER)

coco = {
    "info": info_dict,
    "licenses": None,
    "images": image_dict,
    "categories": [{"id": 0, "name": "tree"}],
    "annotations": annotation_dict
}

with open(COCO_PATH, 'w+') as f:
    json.dump(coco, f)