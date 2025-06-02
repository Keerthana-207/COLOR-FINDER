import os
from PIL import Image
import numpy as np
import time
from flask import Flask, render_template, request, session, url_for
from sqlalchemy.orm import DeclarativeBase
from werkzeug.utils import secure_filename, send_from_directory, redirect
from dotenv import load_dotenv

load_dotenv()

def rgb_to_hex(rgb):
    return "#{:02x}{:02x}{:02x}".format(rgb[0],rgb[1],rgb[2])

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY")


UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER




class Base(DeclarativeBase):
    pass



@app.route("/",methods=['GET'])
def index():
    img_file = session.get("img_file")
    sorted_col_pect = session.pop("sorted_col_pect", [])
    sorted_col = session.pop("sorted_col", [])
    hex_cod = session.pop("hex_cod",[])
    zip_colors = list(zip(sorted_col_pect,sorted_col,hex_cod))

    response =  render_template("sample.html",
                                img_file=img_file,
                                zip_col=zip_colors,)
    session.pop("img_file",None)
    return response

@app.route("/upload",methods=["POST"])
def upload():
    img_file = None
    if 'file' not in request.files:
        return 'No File Selected'
    file = request.files['file']
    if file.filename == '':
        return "No File Selected"
    if file:
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        filepath = os.path.join(app.config['UPLOAD_FOLDER'],filename)

        # Resizing the image and saving
        img = Image.open(filepath)
        target_width = 400
        aspect_ratio = img.height / img.width
        new_height = int((target_width * aspect_ratio))
        img = img.resize((target_width,new_height),Image.NEAREST)
        name,ext = os.path.splitext(filename)
        resized_filename = f"{name}_resized{ext}"
        resized_filepath = os.path.join(app.config['UPLOAD_FOLDER'],resized_filename)
        img.save(resized_filepath)
        unique_suffix = int(time.time())
        img_file = f"/{UPLOAD_FOLDER}/{resized_filename}?v={unique_suffix}"
        session["img_file"] = img_file

        # RGB colors from the image
        palette_img = img.convert("P",palette=Image.ADAPTIVE,colors=256)
        palette = palette_img.getpalette()
        color_indices = palette_img.getcolors()
        total_pixels = img.width * img.height

        colors = []
        col_pect = []
        hex_cod = []

        for pix,idx in color_indices:
            color_pect = round((pix/total_pixels)*100,4)
            col_pect.append(color_pect)
            base = idx*3
            rgb_col = tuple(palette[base:base+3])
            colors.append(rgb_col)

        col_pairs = sorted(zip(col_pect,colors),reverse=True,key=lambda x:x[0])
        sorted_col_pect,sorted_col = zip(*col_pairs)
        # print(sorted_col_pect)
        # print(sorted_col)

        for col in sorted_col:
            hex_col = rgb_to_hex(col)
            hex_cod.append(hex_col)

        print(hex_cod)

        session["sorted_col_pect"] = list(sorted_col_pect)
        session["sorted_col"] = [list(c) for c in sorted_col]
        session["hex_cod"] = list(hex_cod)
        return redirect(url_for('index'))



if __name__ == "__main__":
    app.run(debug=True)