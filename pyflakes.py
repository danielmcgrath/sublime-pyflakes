import sublime, sublime_plugin
import subprocess
import re
import os
import sys

def pyflakes_command(file_name):
  if sys.platform == 'win32':
    path = os.getenv('PATH').split(';')
    python_path_pattern = re.compile('Python\d{2}$')
    for p in path:
      if python_path_pattern.search(p) is not None:
        return [p+'\Python', p+'\Scripts\pyflakes', file_name]
    return []
  return ['pyflakes', file_name]


def highlight_error(self, view, warning):
  if warning:
    warning = warning.split(':')
    line_number = int(warning[1]) - 1
    point = view.text_point(line_number, 0)
    line = view.line(point)

    PyflakesListener.warning_messages.append({
      'region': line,
      'message': warning[2]
    })

    return line


def display_warning(warning):
  for region in PyflakesListener.warning_messages:
    if region['region'] == warning:
      sublime.status_message(region['message'])
      break


def is_python_file(view):
  return bool(re.search('Python', view.settings().get('syntax'), re.I))


class PyflakesListener(sublime_plugin.EventListener):
  warning_messages = []

  def on_post_save(self, view):
    if is_python_file(view):
      view.erase_regions('PyflakesWarnings')
      self.warning_messages = []

      file_name = view.file_name().replace(' ', '\ ')
      process = subprocess.Popen(pyflakes_command(file_name), stdout = subprocess.PIPE)
      results, error = process.communicate()

      if results:
        regions = []
        for warning in results.split('\n'):
          region = highlight_error(self, view, warning.replace(file_name, ''))
          if region:
            regions.append(region)

        view.add_regions('PyflakesWarnings', regions, 'string pyflakeswarning', 'dot')


  def on_selection_modified(self, view):
    if is_python_file(view):
      warnings = view.get_regions('PyflakesWarnings')
      for warning in warnings:
        if warning.contains(view.sel()[0]):
          display_warning(warning)
          break
