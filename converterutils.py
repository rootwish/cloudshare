# -*- coding: utf-8 -*-
import os
import email
import os.path
import mimetypes
import subprocess
import xml.etree.ElementTree

import magic
import pypandoc
import emaildata.text


def file_pdf_to_html(path, filename):
    p = subprocess.Popen(['pdftohtml', '-noframes', path + filename],
                         stdout=subprocess.PIPE)
    p.communicate()


def file_doc_to_html(path, filename):
    p = subprocess.Popen(['soffice', '--headless', '--convert-to',
                          'html', path + filename, '--outdir', path],
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    returncode = p.communicate()
    return returncode


def file_html_to_md(path, filename):
    result = pypandoc.convert(path + filename, 'md', format='html')
    return result


def str_md_to_html(md_code):
    result = pypandoc.convert(md_code, 'html', format='md')
    return result


def save_stream(path, filename, stream):
    with open(path + filename, 'wb') as localfile:
        localfile.write(stream)


def file_mht_to_html(path, filename):
    message = email.message_from_file(open(path + filename))
    html = emaildata.text.Text.html(message)
    return html


def get_md_version(filename):
    basename, _ = os.path.splitext(filename)
    return basename + '.md'


def storage(filename, fileobj, repo):
    """
        >>> import shutil
        >>> import gitinterface
        >>> import converterutils
        >>> repo_name = 'test_repo'
        >>> interface = gitinterface.GitInterface(repo_name)
        >>> cv1_name = 'cv_1.doc'
        >>> cv2_name = 'cv_2.doc'
        >>> cv1_file = open('test/' + cv1_name, 'r')
        >>> cv2_file = open('test/' + cv2_name, 'r')
        >>> md1_str = converterutils.storage(cv1_name, cv1_file, interface)
        >>> md2_str = converterutils.storage(cv2_name, cv2_file, interface)
        >>> with open('test_repo/cv_1.md') as file:
        ...     md1_file = file.read()
        >>> with open('test_repo/cv_2.md') as file:
        ...     md2_file = file.read()
        >>> md1_str == md1_file
        True
        >>> md2_str == md2_file
        True
        >>> shutil.rmtree(repo_name)
    """
    mimetype = magic.Magic()
    stream = fileobj.read()
    path = repo.repo.path + '/'

    basename, _ = os.path.splitext(filename)
    localname = filename

    htmlname = basename + '.html'
    mdname = basename + '.md'
    mimetype = mimetype.from_buffer(stream)
    save_stream(path, localname, stream)
    if mimetype.startswith('PDF'):
        file_pdf_to_html(path, localname)
    elif mimetype.startswith('news or mail'):
        html_src = file_mht_to_html(path, localname)
        save_stream(path, htmlname, html_src)
    else:
       returncode = file_doc_to_html(path, localname)
    md = file_html_to_md(path, htmlname).encode('utf-8')
    save_stream(path, mdname, md)
    repo.add_file(path, mdname, md)
    return md


def file_doc_to_docbook(path, filename, output):
    p = subprocess.Popen(['libreoffice', '--headless', '--convert-to',
                          'xml:DocBook File', os.path.join(path, filename),
                          '--outdir', output],
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    returncode = p.communicate()
    return returncode


def file_docbook_to_markdown(path, filename, output):
    input_file = os.path.join(path, filename)
    output_file = os.path.join(output, filename + '.md')
    try:
        pypandoc.convert(input_file, 'markdown', format='docbook', outputfile=output_file)
    except RuntimeError as e:
        pass


def remove_note(path, filename):
    e = xml.etree.ElementTree.parse(os.path.join(path, filename))
    note_parent = e.findall('.//note/..')
    for parent in note_parent:
        while(parent.find('note') is not None):
            parent.remove(parent.find('note'))
    e.write(os.path.join(path, filename), encoding='utf-8')


def process_mht(path, filename):
    with open(os.path.join(path, filename), 'r') as f:
        stream = f.read()
    if 'multipart/related' in stream:
        return False
    else:
        return True


def convert_folder(path):
    """
        >>> import os
        >>> import converterutils
        >>> import xml.etree.ElementTree
        >>> converterutils.convert_folder('./test')
        >>> e = xml.etree.ElementTree.parse('docbook_output/cv_1.xml').getroot()
        >>> e.findall('para')[0].text
        'http://jianli.yjbys.com/'
        >>> with open('md_output/cv_1.xml.md') as file:
        ...     data = file.read()
        >>> 'http://jianli.yjbys.com/' in data
        True
        >>> os.remove('docbook_output/cv_1.xml')
        >>> os.remove('docbook_output/cv_2.xml')
        >>> os.remove('md_output/cv_1.xml.md')
        >>> os.remove('md_output/cv_2.xml.md')
    """
    docbook_path = 'docbook_output'
    markdown_path = 'md_output'
    if not os.path.exists(docbook_path):
        os.mkdir(docbook_path)
    if not os.path.exists(markdown_path):
        os.mkdir(markdown_path)
    for root, dirs, files in os.walk(path):
        for name in files:
            mimetype = mimetypes.guess_type(os.path.join(root, name))[0]
            if mimetype in ['application/msword',
                            "application/vnd.openxmlformats-officedocument"
                            ".wordprocessingml.document"]:
                if not process_mht(root, name):
                    continue
                returncode = file_doc_to_docbook(root, name, docbook_path)
                if "Error" in returncode[0]:
                    continue
                basename, _ = os.path.splitext(name)
                docbookname = basename + '.xml'
                if not os.path.exists(os.path.join(docbook_path, docbookname)):
                    continue
                remove_note(docbook_path, docbookname)
                file_docbook_to_markdown(docbook_path,
                                         docbookname,
                                         markdown_path)
            else:
                pass
