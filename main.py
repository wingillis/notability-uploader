from evernote.api.client import EvernoteClient
from evernote.edam.type import ttypes
import json
import os
import time
import pickle
import glob
import hashlib
import subprocess

def main():
    rcfile = os.path.expanduser('~/.oryxrc')
    with open('last-checked.pkl', 'r') as f:
        last_checked = pickle.load(f)
    with open(rcfile, 'r') as f:
        config = json.load(f)
    with open('last-checked.pkl', 'w') as f:
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
        # subprocess.check_call(['convert', '-density', '300', f, '-resize', '75%', os.path.join('/tmp', os.path.basename(f)[:-3] + 'png')])
        note = create_note(notebook, f)
        note_store.createNote(config['devToken'], note)

def create_note(notebook, pdf):
    note = ttypes.Note()
    note.notebookGuid = notebook.guid
    note.title = os.path.basename(pdf)
    md5 = hashlib.md5()
    with open(pdf, 'rb') as f:
        f_contents = f.read()
        md5.update(f_contents)
    hashval = md5.hexdigest()
    media = '<en-media type="application/pdf" hash="{hash}" />'.format(hash=hashval)
    note.content = '''<?xml version="1.0" encoding="UTF-8"?>
    <!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd">
    <en-note>{note_media}</en-note>'''.format(note_media=media)
    resource = ttypes.Resource()
    rAttrs = ttypes.ResourceAttributes()
    rAttrs.fileName = os.path.basename(pdf)
    resource.mime = 'application/pdf'
    data = ttypes.Data()
    data.bodyHash = hashval
    data.size = len(f_contents)
    data.body = f_contents
    resource.data = data
    resource.attributes = rAttrs
    note.resources = [resource]
    return note

if __name__=='__main__':
    main()
