import argparse
from app.core.security import create_access_token

def main():
    parser=argparse.ArgumentParser(description="Create a Sentinel local development JWT")
    parser.add_argument("--subject",default="local.admin@sentinel.test")
    parser.add_argument("--role",choices=["viewer","investigator","manager","admin"],default="admin")
    args=parser.parse_args()
    print(create_access_token(args.subject,args.role))

if __name__=="__main__":
    main()
