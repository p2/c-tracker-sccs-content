#!/usr/bin/env python3
#
#  Uses HTML data from _source and renders them, using Jinja2, into _target
#
#  Requirements:
#  - jinja2
#  - markdown

import io
import glob
import os.path
import markdown
from jinja2 import Environment, PackageLoader


# run all files in all languages
def run(tpl_dir, tpl_name, source, target, files):
	env = Environment(loader=PackageLoader(__name__, tpl_dir))
	template = env.get_template(tpl_name)
	
	for langpath in glob.iglob(os.path.join(source, '*.lproj')):
		langdir = os.path.split(langpath)[-1]
		run_lang(langdir, files, source, template, target)

# run all files in one language
def run_lang(langdir, files, source, template, target):
	for file in files:
		run_file_in_lang(langdir, source, target, template, file)

# run one file in one language
def run_file_in_lang(langdir, source, target, template, file):
	filename = None
	title = None
	content = []
	
	# read file(s): expecting either a string (one file) or a tuple with a
	# list of files (0) and the target file name (1)
	subfiles = [file]
	if isinstance(file, tuple):
		subfiles = file[0]
		filename = file[1]
	
	for subfile in subfiles:
		myname, mytitle, mycontent = file_content(source, langdir, subfile)
		if filename is None:
			filename = myname
		if title is None:
			title = mytitle
		if mycontent is not None:
			content.append(mycontent)
	
	if len(content) > 0:
		dump_content_to(template, '\n\n'.join(content), title, target, langdir, filename)

# return tuples of file content for the given file
def file_content(source, langpath, filename):
	filepath = os.path.join(source, langpath, filename)
	
	# not found in desired language, fall back to en
	if not os.path.exists(filepath):
		print('~~~>  «{}» does not exist in {}, trying English'.format(filename, lang_name(langpath)))
		altpath = os.path.join(_source, 'en.lproj')
		filepath = os.path.join(altpath, filename)
		if not os.path.exists(filepath):
			print('xxx>  «{}» not found, skipping'.format(filename))
			return None, None, None
	
	content = read_content(filepath)
	title = os.path.splitext(filename)[0]
	if 'index' == title:
		title = "C Tracker"
	
	# markdown?
	if '.md' == os.path.splitext(filename)[-1]:
		filename = os.path.splitext(filename)[0] + '.html'
		title = content.split('\n')[0]
		content = markdown.markdown(content, output_format='html5')
	
	return filename, title, content

# read content of a file into a string
def read_content(source):
	with io.open(source, 'r', encoding="utf-8") as handle:
		return handle.read()

# apply content and title to _template
def dump_content_to(template, content, title, target, langdir, filename):
	lang = os.path.splitext(langdir)[0]
	template.stream(title=title, content=content, lang=lang, target=filename) \
		.dump(os.path.join(target, langdir, filename))

# language name extracted from directory like "path/to/en.lproj"
def lang_name(langpath):
	return os.path.splitext(os.path.split(langpath)[-1])[0]
