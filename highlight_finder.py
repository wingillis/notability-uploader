import sys
import os
import numpy as np
import scipy.stats as stats
from skimage.io import imread, imsave
from skimage.color import rgb2gray, rgba2rgb
from skimage.morphology import binary_dilation, disk
from skimage.measure import label, regionprops

def main(fname):
    templates = dict(yellow=np.array([250, 239, 190]),
                     blue=np.array([192, 240, 246]))
    im = imread(fname)
    if im.shape[2] > 3:
        im = rgba2rgb(im)*255
    im_files = []
    for key, template in templates.items():
        regions = get_highlighted_regions(im, template)
        im_files += save_highlight_extract(im, regions, key, fname)

    return im_files

def save_highlight_extract(im, bounds, color, fname):
    path = os.path.dirname(fname)
    basename = os.path.basename(fname)
    fnames = []
    for i, (minr, minc, maxr, maxc) in enumerate(bounds):
        tmp = im[minr:maxr, minc:maxc]
        f = '{}-{}-{}.png'.format(color, i, basename[:-4])
        fnames += [os.path.join(path, f)]
        imsave(os.path.join(path, f), tmp)
    return fnames

def get_highlighted_regions(im, color):
    im_tmp = im.copy()
    for i in range(im.shape[0]):
        for j in range(im.shape[1]):
            im_tmp[i, j, :] = im_tmp[i, j, :] - color
    blobs = binary_dilation(rgb2gray(im_tmp) < 0.01, disk(5))
    labeled = label(blobs)
    props = regionprops(labeled)
    return [region.bbox for region in props]

if __name__=='__main__':
    main(sys.argv[1])
