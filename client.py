#!/usr/bin/env python
import argparse

def get_parser():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(title='subcommands')

    checkout = subparsers.add_parser('checkout', help="Check out a document.")
    checkout.add_argument('document_id', help="The id of the document to check out.")
    checkout.set_defaults(func=checkout)

    list_parse = subparsers.add_parser('list', help="List users and document ids.")
    list_parse.add_argument('object', choices=['documents', 'users'], help="documents or users")
    list_parse.set_defaults(func=list_parse)

    checkin = subparsers.add_parser('checkin', help="Check in a document.")
    checkin.add_argument('document', help="Path to the document.")
    checkin.add_argument('--flag', choices=['confidentiality', 'integrity'])
    checkin.set_defaults(func=checkin)

    delete = subparsers.add_parser('delete', help="Delete a document")
    delete.add_argument('document_id', help="The id of the document to delete.")
    delete.set_defaults(func=delete)

    delegate = subparsers.add_parser('delegate', help="Delegate permissions to the document")
    delegate.add_argument('document_id', help="The id of the document to delegate")
    delegate.add_argument('client_id', help="The id of the client to delegate to")
    delegate.add_argument('permission', choices=['read', 'write', 'ownership'])
    delegate.add_argument('--time', type=int, help="Number of days to grant access")
    delegate.add_argument('--propagate', action="store_true", default=False, help="Can the user propagate the granted permission.")
    delegate.set_defaults(func=delegate)

    return parser

def main():
    parser = get_parser()
    parser.parse_args()
    args = vars(args)
    args.func(args)

if __name__ == "__main__":
    main()
