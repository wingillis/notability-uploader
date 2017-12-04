from evernote.api.client import EvernoteClient
from evernote.edam.type import ttypes
import json
import os
import time
import pickle
import glob
import hashlib
import subprocess
import tempfile
import highlight_finder as hf

def main():
    rcfile = os.path.expanduser('~/.oryxrc')
    with open(os.path.dirname(__file__) + '/last-checked.pkl', 'r') as f:
        last_checked = pickle.load(f)
    with open(rcfile, 'r') as f:
        config = json.load(f)
    with open(os.path.dirname(__file__) + '/last-checked.pkl', 'w') as f:
        pickle.dump(time.time(), f)
    pdf_path = '/Users/wgillis/Dropbox (HMS)/Notability'
    pdf_files = glob.glob(os.path.join(pdf_path, '**', '*.pdf')) + glob.glob(os.path.join(pdf_path, '*.pdf'))
    pdf_files = [f for f in pdf_files if os.stat(f).st_mtime > last_checked]
    client = EvernoteClient(token=config['devToken'], sandbox=False)
    note_store = client.get_note_store()
    notebooks = note_store.listNotebooks()
    notebook = [n for n in notebooks if n.name == 'Notability PDFs'][0]
    # TODO: make tags the sub-notebook the files are in
    for f in pdf_files:
        print('Uploading', f)
        imgs = pdf_to_image(f)
        highlights = create_highlights(imgs)
        note2 = create_note(notebook, f, highlights)
        note_store.createNote(config['devToken'], note2)
        for img in imgs+highlights:
            os.remove(img)

def create_highlights(imgs):
    imfiles = []
    for im in imgs:
        tmp = hf.main(im)
        if tmp:
            imfiles += tmp
    return imfiles

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

def create_note(notebook, pdf, images):
    media = '<en-media type="{typ}" hash="{hash}" /><br/>'
    note = ttypes.Note()
    note.notebookGuid = notebook.guid
    note.title = os.path.basename(pdf)
    note.content = '''<?xml version="1.0" encoding="UTF-8"?>
    <!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd">
    <en-note>'''
    resources = []
    for img in images:
        resource, h = create_resource(img, typ='image/png')
        note.content += media.format(typ='image/png', hash=h)
        resources += [resource]
    resource, h = create_resource(pdf)
    resources += [resource]
    note.content += media.format(typ='application/pdf', hash=h)
    note.content += '</en-note>'
    note.resources = resources
    return note

def pdf_to_image(pdf_path, quality=100, typ='png', density=100):
    handle, path = tempfile.mkstemp()
    subprocess.check_call(['/usr/local/bin/convert', '-density', str(density), pdf_path, '-quality', str(quality), path+'.'+typ])
    # subprocess.check_call(['convert', path + '*.'+typ, '-quality', '100', path+'.pdf'])
    files = glob.glob(path + '*.' + typ)
    return files

if __name__=='__main__':
    main()
