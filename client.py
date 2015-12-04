#!/usr/bin/env python
import argparse
import requests
import tabulate
import json
import os
import re

BASE_PATH = os.path.dirname(os.path.realpath(__file__))
BASE_URL  = "https://vps.kylekoza.com/"
cert = (os.path.realpath(os.path.join(BASE_PATH, "client.crt")),
        os.path.realpath(os.path.join(BASE_PATH, "client.key")))

def list_parse(args):
    args = vars(args)
    if args["object"] == "documents":
        r = requests.get(BASE_URL + "get_entitlements/", cert=cert, verify=False)
        result = json.loads(r.text)
        print tabulate.tabulate(result["entitlements"], headers="keys")
    elif args["object"] == "users":
        r = requests.get(BASE_URL + "get_users/", cert=cert, verify=False)
        result = json.loads(r.text)
        print tabulate.tabulate(result["users"], headers="keys")
    else:
        pass

def checkout(args):
    args = vars(args)
    r = requests.get(BASE_URL + "check_out/{0}".format(args["document_id"]), cert=cert, verify=False)
    d = r.headers['content-disposition']
    filename = re.findall("filename=(.+)", d)

    with open(filename, 'wb') as f:
        f.write(r.content)

def checkin(args):
    args = vars(args)
    payload = {"flag": args["flag"]}

    with open(args['document'], 'rb') as upload:
        r = requests.post(BASE_URL + "check_in/", data=payload, cert=cert, verify=False, files={'file': upload})

def delete(args):
    args = vars(args)
    r = requests.get(BASE_URL + "safe_delete/" + args['document_id'], cert=cert, verify=False)

def delegate(args):
    pass

def get_parser():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(title='subcommands')

    arg_checkout = subparsers.add_parser('checkout', help="Check out a document.")
    arg_checkout.add_argument('document_id', help="The id of the document to check out.")
    arg_checkout.set_defaults(func=checkout)

    arg_list_parse = subparsers.add_parser('list', help="List users and document ids.")
    arg_list_parse.add_argument('object', choices=['documents', 'users'], help="documents or users")
    arg_list_parse.set_defaults(func=list_parse)

    arg_checkin = subparsers.add_parser('checkin', help="Check in a document.")
    arg_checkin.add_argument('document', help="Path to the document.")
    arg_checkin.add_argument('--flag', choices=['confidentiality', 'integrity'])
    arg_checkin.set_defaults(func=checkin)

    arg_delete = subparsers.add_parser('delete', help="Delete a document")
    arg_delete.add_argument('document_id', help="The id of the document to delete.")
    arg_delete.set_defaults(func=delete)

    arg_delegate = subparsers.add_parser('delegate', help="Delegate permissions to the document")
    arg_delegate.add_argument('document_id', help="The id of the document to delegate")
    arg_delegate.add_argument('client_id', help="The id of the client to delegate to")
    arg_delegate.add_argument('permission', choices=['read', 'write', 'ownership'])
    arg_delegate.add_argument('--time', type=int, help="Number of days to grant access")
    arg_delegate.add_argument('--propagate', action="store_true", default=False, help="Can the user propagate the granted permission.")
    arg_delegate.set_defaults(func=delegate)

    return parser

def main():
    parser = get_parser()
    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
