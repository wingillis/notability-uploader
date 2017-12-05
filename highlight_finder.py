import sys
import os
import numpy as np
import scipy.stats as stats
from numpy.linalg import norm
from skimage.io import imread, imsave
from skimage.color import rgb2gray, rgba2rgb
from skimage.morphology import binary_dilation, disk
from skimage.measure import label, regionprops

def main(fname):
    templates = dict(yellow=np.array([251, 240, 187]),
                     blue=np.array([210, 255, 245]))
    im = imread(fname)
    if im.shape[2] > 3:
        im = rgba2rgb(im)*255
    im_files = {}
    for key, template in templates.items():
        print('Testing {}'.format(key))
        regions = get_highlighted_regions(im, template)
        if regions:
            print('Found {} highlights'.format(len(regions)))
            im_files[key] = save_highlight_extract(im, regions, key, fname)
        else:
            print('No highlights found for this color')

    return im_files

def save_highlight_extract(im, bounds, color, fname):
    path = os.path.dirname(fname)
    basename = os.path.basename(fname)
    fnames = []
    for i, (minr, minc, maxr, maxc) in enumerate(bounds):
        tmp = im[minr:maxr, minc:maxc]
        f = '{}-{}-{}.png'.format(color, i, basename[:-4])
        fnames += [os.path.join(path, f)]
        imsave(os.path.join(path, f), tmp.astype('uint8'))
    return fnames

def get_highlighted_regions(im, color, threshold=13):
    disk_size = 7
    # reshape to 2d matrix
    im_tmp = im.reshape((im.shape[0]*im.shape[1], im.shape[2]))
    template = np.repeat(color, im_tmp.shape[0]).reshape((3, -1)).T
    # subtract the template from the image
    dist = im_tmp - template
    # calculate euclidean distance of resulting color vector
    euclidean = norm(dist, axis=1)
    # find places of minimum value
    m = stats.mode(euclidean[euclidean<threshold]).mode
    if m.size != 0:
        mask = (euclidean==m).reshape(im.shape[:2])
        mask = binary_dilation(mask, disk(disk_size))
        labeled = label(mask)
        props = regionprops(labeled)
        return [region.bbox for region in props if region.minor_axis_length > disk_size*np.pi]
    else:
        return []

if __name__=='__main__':
    main(sys.argv[1])
