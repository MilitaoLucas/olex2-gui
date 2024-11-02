from functools import wraps

def run_with_bitmap(bitmap_text, use_timage=True,
                    update_html_before=False, update_model_before=False,
                    update_html_after=True, update_model_after=False):
  from olexFunctions import OV
  import olx
  if OV.HasGUI() and use_timage:
    from PilTools import timage
    timage.info_bitmaps(timage, bitmap_text, '#ff4444')

  def decorator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
      OV.CreateBitmap(bitmap_text)
      if update_html_before: olx.html.Update()
      if update_model_before: olx.xf.EndUpdate()
      olx.Refresh()
      try:
        return func(*args, **kwargs)
      except Exception as e:
        raise e
      finally:
        OV.DeleteBitmap(bitmap_text)
        if update_html_after: olx.html.Update()
        if update_model_after: olx.xf.EndUpdate()
        olx.Refresh()
    return wrapper

  def headless_decorator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
      return func(*args, **kwargs)
    return wrapper
  if OV.HasGUI():
    return decorator
  else:
    return headless_decorator

def long_call(bitmap_text, use_timage=False,
                    update_html_before=False, update_model_before=False,
                    update_html_after=False, update_model_after=False):
  return run_with_bitmap(bitmap_text, use_timage=use_timage,
    update_html_before=update_html_before,
    update_model_before=update_model_before,
    update_html_after=update_html_after,
    update_model_after=update_model_after)

def gui_only(returns=None):
  import olx
  def decorator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
      if olx.HasGUI() == 'true':
        return func(*args, **kwargs)
      else:
        return returns
    return wrapper
  return decorator

def return_str(convert_None=True, lower=False, skip_types=None):
  def decorator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
      rv = func(*args, **kwargs)
      if rv is None and convert_None:
        return ""
      if skip_types and type(rv) in skip_types:
        return rv
      return str(rv) if not lower else str(rv).lower()
    return wrapper
  return decorator
