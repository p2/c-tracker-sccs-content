#!/usr/bin/env python3
#
#  Can render Markdown and HTML files using a given template to the filesystem
#
#  Requirements see "build_requirements.txt"

import io
import re
import glob
import os.path
import markdown
import requests
from jinja2 import Environment, PackageLoader

_checked_links = {}

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
			link_errors = check_links(mycontent)
			if link_errors is not None and len(link_errors) > 0:
				for link_error in link_errors:
					print('xxxx>  Invalid link “{}” in «{}/{}/{}»'.format(link_error, source, langdir, subfile))
			content.append(mycontent)
	
	if len(content) > 0:
		dump_content_to(template, '\n\n'.join(content), title, target, langdir, filename)

# checks all links found in an HTML string using `requests`
def check_links(html):
	if html is None:
		return None
	
	errors = []
	expr = r'(href|src)="([^"]+)"'
	for match in re.findall(expr, html):
		if match[1].startswith('http'):
			if match[1] not in _checked_links:
				
				# check link and cache
				ret = requests.get(match[1])
				_checked_links[match[1]] = ret.status_code
			
			if _checked_links[match[1]] >= 400:
				errors.append(match[1])
	
	return errors if len(errors) > 0 else None

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
