import os
import cv2
import torch
import argparse
from yolox.exp import get_exp
from yolox.data.data_augment import preproc
from yolox.utils.demo_utils import multi_scale_test
from yolox.utils.visualize import vis
from yolox.utils.postprocess import vis_rescore, coco_results
from yolox.data.datasets import COCODataset

def inference(exp, model, img_path, conf_thres, nms_thres, target_size, device):
    model.eval()
    img = cv2.imread(img_path)
    img_info = {"id": 0, "file_name": os.path.basename(img_path), "width": img.shape[1], "height": img.shape[0]}
    img, ratio = preproc(img, target_size, (0.5, 0.5, 0.5))
    img = torch.from_numpy(img).unsqueeze(0).to(device)
    outputs = model(img)

    with torch.no_grad():
        outputs = model(img)
        outputs = post_process(
            outputs, target_size, img_info, conf_thres, nms_thres)[0]
        outputs = outputs[outputs[:, 4] > 0]
        return outputs

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("image", type=str, help="path to the test image")
    parser.add_argument("-f", "--model", type=str, default="yolox_s.py", help="model file path")
    parser.add_argument("-c", "--checkpoint", type=str, default=None, help="checkpoint file path")
    parser.add_argument("--conf", type=float, default=0.3, help="confidence threshold")
    parser.add_argument("--nms", type=float, default=0.45, help="NMS threshold")
    parser.add_argument("--tsize", type=int, default=640, help="test size")
    parser.add_argument("--device", default="cuda", help="device id (i.e. 0 or 0,1 or cpu)")
    args = parser.parse_args()

    exp = get_exp(args.model, args.checkpoint)
    model = exp.get_model()
    model.to(args.device)
    model.eval()

    with torch.no_grad():
        output = inference(exp, model, args.image, args.conf, args.nms, args.tsize, args.device)

        # Assuming you are using COCO classes, you can load the COCO classes and map class IDs to class names
        coco_classes = COCODataset.CLASS_NAMES

        # Print annotation details
        for detection in output:
            class_id = int(detection[5])
            class_name = coco_classes[class_id]
            conf = detection[4]
            bbox = detection[:4]
            print(f"Class: {class_name}, Confidence: {conf:.2f}, Bbox: {bbox.tolist()}")
