
import os

from flask import redirect, render_template, request, session

def alertErrors(isError, alertType):
    if isError == "true":
        error = ["true", alertType]
        return error
    else:
        error = ["false", alertType]
        return error