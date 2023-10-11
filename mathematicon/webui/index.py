from flask import render_template, redirect, url_for

from .app import app


@app.route('/')
def start_page():
    return redirect(url_for('main_page', lang="en"))
