#variableDefinitions.py

from olexFunctions import OlexFunctions
OV = OlexFunctions()

def guiVariables():
  return dict(
    gui_logo_colour='#6464a0',
    gui_skin_name='default',
    gui_skin_extension="None",
    gui_skin_logo_name=r'gui/images/src/default.png',
    
    gui_purple='#a245a2',
    gui_red='#ff0000',
    gui_orange='#ff8f00',
    gui_green='#018F1E',
    gui_grey='#555555',
    
    gui_html_base_colour='#00ff00',
    gui_html_bg_colour='#ffffff',
    gui_html_input_bg_colour='#F3F3F3',
    gui_html_input_height=18,
    gui_html_combo_height=18,
    gui_html_spin_height=20,
    gui_html_checkbox_height=30,
    gui_html_button_height=18,
    gui_html_font_colour='#6f6f8b',
    gui_html_font_name='Verdana',
    gui_html_table_bg_colour='#F3F3F3',
    gui_html_table_firstcol_colour='#E9E9E9',
    gui_html_highlight_colour=OV.FindValue('gui_html_highlight_colour','#ff7800'),
    gui_html_link_colour='#6f6f8b',
    gui_html_font_size=2,
    gui_html_code_bg_colour="#ffffdd",
    
    gui_image_font_name='Vera',
    gui_timage_colour='#6464a0',
    gui_timage_font_colour='#ff0000',

    gui_button_colouring='#ff0000',
    gui_button_writing='#00ff00',

    gui_snumtitle_colour='#6464a0',
    gui_snumtitle_font_colour='#ff0000',
    gui_tab_colour='#ff0000',
    gui_tab_font_colour='#ff0000',
    
    gui_infobox_text='2053;2143326838;2143979345',
    gui_infobox_plane='2053;2136422952;2137144606',
    
    gui_htmlpanelwidth='400',
    gui_grad_top_left='#05053c',
    gui_grad_top_right='#05053c',
    gui_grad_bottom_left='#ffffff',
    gui_grad_bottom_right='#ffffff',
    gui_language_encoding=OV.CurrentLanguageEncoding(),
    gui_gui_MainToolbarTabButtonActive='none',
    
    gui_use_fader='false',
    gui_shelx_restraints='--',
    gui_shelx_constraints='--',
    gui_archive_last='--',
  )
