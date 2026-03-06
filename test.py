import aspose.pdf as apdf
import os, pathlib

color_name = "C:/Users/tani.yutaro/fixedcut_flask/オールスターカラー.eps"

load_options = apdf.PsLoadOptions()
color_svg = apdf.Document("C:/Users/tani.yutaro/fixedcut_flask/オールスターカラー.eps", load_options)
#mono_svg = apdf.Document(str(mono_path), load_options)
save_options = apdf.SvgSaveOptions()
        
save_options.compress_output_to_zip_archive = False
save_options.treat_target_file_name_as_directory = True
        
color_svg.save(f'./{color_name.replace(".eps",".svg")}', save_options)
#mono_svg.save(f'fixedcut_app/templates/static/img_mono/{form_id}/{mono_name.replace(".eps",".svg")}', save_options)