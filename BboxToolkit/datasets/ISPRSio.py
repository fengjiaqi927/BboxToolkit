import os
import time
import os.path as osp
import xml.etree.ElementTree as ET
import numpy as np

from functools import partial
from .misc import img_exts, get_classes, _ConstMapper, prog_map
from ..imagesize import imsize

import BboxToolkit as bt


def load_isprs(img_dir, ann_dir, classes=None, img_keys=None, obj_keys=None, nproc=10):
    assert osp.isdir(img_dir), f'The {img_dir} is not an existing dir!'
    assert ann_dir is None or osp.isdir(ann_dir), f'The {ann_dir} is not an existing dir!'

    classes = get_classes('ISPRS' if classes is None else classes)
    if (len(classes) == 1) and (classes[0] == 'ship'):
        cls2lbl = _ConstMapper(0)
    else:
        cls2lbl = dict()
        for i, cls in enumerate(classes):
            # if len(cls) < 9:
            #     cls = '1' + '0' * (8 - len(cls)) + cls
            cls2lbl[cls] = i

    img_keys = dict() if img_keys is None else img_keys
    obj_keys = dict() if obj_keys is None else obj_keys

    contents = []
    print('Starting loading ISPRS dataset information.')
    start_time = time.time()
    _load_func = partial(_load_isprs_single,
                         img_dir=img_dir,
                         ann_dir=ann_dir,
                         img_keys=img_keys,
                         obj_keys=obj_keys,
                         cls2lbl=cls2lbl)
    img_list = os.listdir(img_dir)
    contents = prog_map(_load_func, img_list, nproc)
    end_time = time.time()
    print(f'Finishing loading ISPRS, get {len(contents)} images,',
          f'using {end_time-start_time:.3f}s.')
    return contents, classes


def _load_isprs_single(imgfile, img_dir, ann_dir, img_keys, obj_keys, cls2lbl):
    img_id, ext = osp.splitext(imgfile)
    if ext not in img_exts:
        return None

    xmlfile = None if ann_dir is None else osp.join(ann_dir, img_id+'.xml')
    content = _load_isprs_xml(xmlfile, img_keys, obj_keys, cls2lbl)

    if not ('width' in content and 'height' in content):
        imgpath = osp.join(img_dir, imgfile)
        width, height = imsize(imgpath)
        content.update(dict(width=width, height=height))
    content.update(dict(filename=imgfile, id=img_id))
    return content


def _load_isprs_xml(xmlfile, img_keys, obj_keys, cls2lbl):
    
    # 此处的bboxes 为（x,y,h,w,theta）
    # polys 为 （x1,y1,x2,y2,x3,y3,x4,y4）
    bboxes, polys, labels = list(), list(), list()

    content = {k: None for k in img_keys}
    ann = {k: [] for k in obj_keys}
    if xmlfile is None:
        pass
    elif not osp.isfile(xmlfile):
        print(f"Can't find {xmlfile}, treated as empty xmlfile")
    else:
        tree = ET.parse(xmlfile)
        root = tree.getroot()
        # 验证文件名是否正确
        file_name = root.find('source').find('filename').text
        assert osp.splitext(osp.split(xmlfile)[1])[0] == osp.splitext(file_name)[0], f'xmlfile is error'

        # 读取图像尺寸信息
        content['width'] = int(root.find('size').find('width').text)
        content['height'] = int(root.find('size').find('height').text)

        for k, xml_k in img_keys.items():
            node = root.find(xml_k)
            value = None if node is None else node.text
            content[k] = value

        # 读取目标信息
        objects = root.find('objects')
        for obj in objects.findall('object'):
            cls = obj.find('possibleresult').find('name').text
            if cls not in cls2lbl:
                continue

            labels.append(cls2lbl[cls])
            
            points = list()
            for point in obj.find('points'):
                point_x, point_y = point.text.split(',')
                points.append(float(point_x))
                points.append(float(point_y))
            assert points[0] == points[8] , f'load poly_x error'
            assert points[1] == points[9] , f'load poly_y error'
            polys.append(points[:8])
            bboxes.append(bt.poly2obb(np.array(points[:8])))


            for k, xml_k in obj_keys.items():
                node = obj.find(xml_k)
                value = None if node is None else node.text
                ann[k].append(value)
    
    polys = np.array(polys, dtype=np.float32) if polys \
        else np.zeros((0, 4), dtype=np.float32)
    bboxes = np.array(bboxes, dtype=np.float32) if bboxes \
        else np.zeros((0, 4), dtype=np.float32)
    labels = np.array(labels, dtype=np.int64) if labels \
        else np.zeros((0, ), dtype=np.int64)


    ann['polys'] = polys
    ann['labels'] = labels
    ann['bboxes'] = bboxes
    content['ann'] = ann
    return content
