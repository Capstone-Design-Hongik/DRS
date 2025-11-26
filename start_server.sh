#!/bin/bash
# DRS API 서버 실행 스크립트

source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
