import json
import os
import time
import pickle
import glob
import hashlib
import subprocess
import tempfile
from collections import defaultdict
import highlight_finder as hf

from evernote.api.client import EvernoteClient
from evernote.edam.type import ttypes

def main():
    rcfile = os.path.expanduser('~/.oryxrc')
    script_path = os.path.dirname(__file__)
    time_file = os.path.join(script_path, 'last-checked.pkl')
    with open(time_file, 'r') as f:
        last_checked = pickle.load(f)
    with open(rcfile, 'r') as f:
        config = json.load(f)
    with open(time_file, 'w') as f:
        pickle.dump(time.time(), f)
    pdf_path = '/Users/wgillis/Dropbox (HMS)/Notability'
    pdf_files = glob.glob(os.path.join(pdf_path, '**', '*.pdf')) + glob.glob(os.path.join(pdf_path, '*.pdf'))
    pdf_files = [f for f in pdf_files if os.stat(f).st_mtime > last_checked]
    tags = [os.path.dirname(f.replace(pdf_path, '')) for f in pdf_files]
    client = EvernoteClient(token=config['devToken'], sandbox=False)
    note_store = client.get_note_store()
    notebooks = note_store.listNotebooks()
    notebook = [n for n in notebooks if n.name == 'Notability PDFs'][0]
    # TODO: make tags the sub-notebook the files are in
    for f, tag in zip(pdf_files, tags):
        print('Uploading', f)
        imgs = pdf_to_image(f)
        highlights = create_highlights(imgs)
        note2 = create_note(notebook, f, highlights, tag)
        note_store.createNote(config['devToken'], note2)
        for img in imgs:
            os.remove(img)
        for imgs in highlights.values():
            for img in imgs:
                os.remove(img)

def create_highlights(imgs):
    highlights = defaultdict(list)
    for im in imgs:
        tmp = hf.main(im)
        if tmp:
            for key in tmp:
                highlights[key] += tmp[key]
    return highlights

def create_resource(pdf, typ='application/pdf'):
    m5hash = hashlib.md5()
    resource = ttypes.Resource()
    rattr = ttypes.ResourceAttributes()
    # rattr.attachment = True
    rattr.fileName = os.path.basename(pdf)
    resource.mime = typ
    resource.attributes = rattr
    data = ttypes.Data()
    with open(pdf, 'rb') as f:
        contents = f.read()
    m5hash.update(contents)
    h = m5hash.hexdigest()
    data.bodyHash = h
    data.size = len(contents)
    data.body = contents
    resource.data = data
    return resource, h

def create_note(notebook, pdf, images, tag):
    '''images is a len=2 list where first are blue and then yellow highlights'''
    media = '<en-media type="{typ}" hash="{hash}" /><br/>'
    highlight_choices = defaultdict(str, blue='To read later:<br/>',
                                    yellow='To remember:<br/>')
    note = ttypes.Note()
    note.notebookGuid = notebook.guid
    note.tagNames = [tag]
    note.title = os.path.basename(pdf)
    note.content = '''<?xml version="1.0" encoding="UTF-8"?>
    <!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd">
    <en-note><h2>Highlights:</h2><br/><br/>'''
    resources = []
    for color, imgs in images.items():
        note.content += highlight_choices[color]
        for img in imgs:
            resource, h = create_resource(img, typ='image/png')
            note.content += media.format(typ='image/png', hash=h)
            resources += [resource]
    resource, h = create_resource(pdf)
    resources += [resource]
    note.content += media.format(typ='application/pdf', hash=h)
    note.content += '</en-note>'
    note.resources = resources
    return note

def pdf_to_image(pdf_path, quality=100, typ='png', density=300):
    handle, path = tempfile.mkstemp()
    subprocess.check_call(['/usr/local/bin/convert', '-density', str(density), pdf_path, '-quality', str(quality), path+'.'+typ])
    files = glob.glob(path + '*.' + typ)
    return files

if __name__=='__main__':
    main()
