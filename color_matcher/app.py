import os
from flask import Flask, render_template, url_for, redirect
from pandas import read_csv
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from webcolors import hex_to_rgb, rgb_to_hex

color_data_indices = ["specific_name", "medium_name", "broad_name", "hex", "r", "g", "b"]
color_data = read_csv("colordata.csv", names=color_data_indices, header=None)

description_indices = ["color_name", "hex_code", "r", "g", "b"]
description_data = read_csv("color_match_data.csv", names=description_indices, header=None)

app = Flask(__name__)
# app.config.from_object('config.Config')
app.config["SECRET_KEY"] = "dev"


class ColorInputForm(FlaskForm):
    hex_code = StringField("Hex code")
    submit = SubmitField("Submit")


@app.route("/", methods=["GET", "POST"])
def index():
    form = ColorInputForm()
    if form.validate_on_submit():
        hex_code = form.hex_code.data.strip()
        if hex_code[0] != "#":
            hex_code = "#" + hex_code
        # r, g, b = tuple(int(hex_code[i:i+2], 16) for i in (0, 2, 4))
        r, g, b = hex_to_rgb(hex_code)
        return redirect(url_for("results", rgb=f"{r} {g} {b}"))
    return render_template("color_matcher/index.html", form=form)


@app.route("/color/<rgb>")
def results(rgb):
    r, g, b = rgb.split(" ")
    r, g, b = int(r), int(g), int(b)
    # minimum = 10000
    # matching_color = None
    # for i in range(len(color_csv)):
    #     distance = abs(r - int(color_csv.loc[i, 'r'])) + abs(g - int(color_csv.loc[i, 'g'])) + abs(b - int(color_csv.loc[i, 'b']))
    #     if distance < minimum:
    #         minimum = distance
    #         matching_color = (color_csv.loc[i, 'color_name'], color_csv.loc[i, 'hex'])
    matching_color = match_color((r, g, b), color_data, include_hex=True)
    input_color = rgb_to_hex((r, g, b))
    return render_template(
        "color_matcher/results.html",
        input_color=input_color,
        matching_color_name=matching_color[0],
        matching_color_hex=matching_color[1],
    )


def match_color(color, data_source, include_hex=False):
    minimum = 10000
    matching_color = None
    r, g, b = color
    # if type(color) == 'tuple':
    #     r, g, b = color
    # else:
    #     r, g, b = tuple(int(data_source.loc[i, 'hex_code'].strip('#')[n:n+2], 16) for n in (0, 2, 4))
    for i in range(len(data_source)):
        distance = (
            abs(r - int(data_source.loc[i, "r"]))
            + abs(g - int(data_source.loc[i, "g"]))
            + abs(b - int(data_source.loc[i, "b"]))
        )
        if distance < minimum:
            minimum = distance
            if include_hex:
                matching_color = (data_source.loc[i, "specific_name"], data_source.loc[i, "hex"])
            else:
                matching_color = data_source.loc[i, "color_name"]
    return matching_color


@app.route("/map")
def map_descriptions():
    # first unpack hex values in description data
    for i in range(len(description_data)):
        description_data.loc[i, "r"], description_data.loc[i, "g"], description_data.loc[i, "b"] = tuple(
            int(description_data.loc[i, "hex_code"].strip("#")[n : n + 2], 16) for n in (0, 2, 4)
        )
    for i in range(len(color_data)):
        r, g, b = int(color_data.loc[i, "r"]), int(color_data.loc[i, "g"]), int(color_data.loc[i, "b"])
        matching_color = match_color((r, g, b), description_data)
        # print(matching_color.split(' ')[-1])
        color_data.loc[i, "medium_name"] = matching_color
        color_data.loc[i, "broad_name"] = matching_color.split(" ")[-1]
        color_data.to_csv("colordata.csv", header=False, index=False)

    return redirect(url_for("index"))


@app.route("/check")
def check_integrity():
    # first check for hex-code/rgb mismatches
    # jk im not writing that yet

    # next check for color spaces that are too close together
    colors_list = []
    for base_i in range(len(color_data)):
        base_r, base_g, base_b = (
            int(color_data.loc[base_i, "r"]),
            int(color_data.loc[base_i, "g"]),
            int(color_data.loc[base_i, "b"]),
        )
        base_color = color_data.loc[base_i, "specific_name"]
        for comp_i in range(len(color_data)):
            distance = (
                abs(base_r - int(color_data.loc[comp_i, "r"]))
                + abs(base_g - int(color_data.loc[comp_i, "g"]))
                + abs(base_b - int(color_data.loc[comp_i, "b"]))
            )
            if 0 < distance <= 10:
                comp_color = color_data.loc[comp_i, "specific_name"]
                if (comp_color, base_color, distance) not in colors_list:
                    colors_list.append((base_color, color_data.loc[comp_i, "specific_name"], distance))
    return render_template("color_matcher/check.html", colors_list=colors_list)


if __name__ == "__main__":
    app.run(debug=True)
