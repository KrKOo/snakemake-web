#! /usr/bin/env python
from app import app, celery

if __name__ == "__main__":
    app.run(host="0.0.0.0")
