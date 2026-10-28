#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"backend"))

from app.core.security import create_access_token

parser=argparse.ArgumentParser(description="Create a local Sentinel development JWT")
parser.add_argument("--subject",default="local.admin@sentinel.test")
parser.add_argument("--role",choices=["viewer","investigator","manager","admin"],default="admin")
args=parser.parse_args()
print(create_access_token(args.subject,args.role))
