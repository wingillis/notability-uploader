import sys
import os
import numpy as np
from skimage.io import imread, imsave
from skimage.color import rgb2gray
from skimage.morphology import binary_dilation, disk
from skimage.measure import label, regionprops

def main(fname):
    yel_color = np.array([249, 239, 186])
    blu_color = np.array([209, 255, 245])
    im = imread(fname)
    blu_bnd = get_highlighted_regions(im, blu_color)
    yel_bnd = get_highlighted_regions(im, yel_color)
    save_highlight_extract(im, yel_bnd, 'yellow', fname)
    save_highlight_extract(im, blu_bnd, 'blue', fname)

def save_highlight_extract(im, bounds, color, fname):
    path = os.path.dirname(fname)
    basename = os.path.basename(fname)
    for i, (minr, minc, maxr, maxc) in enumerate(bounds):
        tmp = im[minr:maxr, minc:maxc]
        imsave(os.path.join(path, '{}-{}-{}.png'.format(color, i, basename[:-4])), tmp)

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
